import subprocess
import os
import structlog
from datetime import datetime
from worker.celery_app import celery_app

from shared.db.config import get_db
from shared.config.settings import settings
from shared.storage import storage_manager

from shared.db.models.video import Video, VideoStatus
from shared.db.models.user import User
from shared.db.models.vote import Vote

# Importar métricas
from shared.metrics.metrics import (
    start_metrics_server,
    videos_processed,
    videos_failed,
    video_processing_time,
)
import threading

logger = structlog.get_logger()

# Iniciar servidor de métricas Prometheus en segundo plano
threading.Thread(
    target=start_metrics_server, kwargs={"port": 9001}, daemon=True
).start()


@celery_app.task(
    bind=True,
    name="worker.tasks.video_processing.process_video_task",
    max_retries=5,
    default_retry_delay=60,
)
def process_video_task(self, video_id: str):
    """
    Tarea principal de procesamiento de video que ejecuta:
    1. Recortar a máximo 30 segundos
    2. Ajustar a 720p 16:9
    3. Agregar cortinillas ANB (5s inicio + 5s final)
    """
    start_time = datetime.utcnow()
    logger.info("Starting video processing", video_id=video_id, task_id=self.request.id)

    try:
        db = next(get_db())
        video = db.query(Video).filter(Video.id == video_id).first()

        if not video:
            raise Exception(
                f"Video con ID {video_id} no encontrado en la base de datos"
            )

        video.status = VideoStatus.PROCESSING.value
        video.processing_started_at = datetime.utcnow()
        db.commit()

        # Rutas de archivos usando configuración
        input_path = f"{settings.uploads_dir}/temp_input_{video_id}.mp4"
        temp_path = f"{settings.uploads_dir}/temp_{video_id}.mp4"
        output_path = f"{settings.uploads_dir}/temp_processed_{video_id}.mp4"

        # Descargar video original desde storage
        try:
            storage_manager.download_video(video.file_original_url, input_path)
        except Exception as e:
            raise FileNotFoundError(f"Error descargando video original: {str(e)}")

        # Verificar que existe el archivo descargado
        if not os.path.exists(input_path):
            raise FileNotFoundError(
                f"Video original no encontrado después de descarga: {input_path}"
            )

        logger.info("Step 1: Trimming video to 30 seconds", video_id=video_id)
        if not trim_video_to_30s(input_path, temp_path):
            raise Exception("Error en recorte de video")

        logger.info("Step 2: Resizing to 720p 16:9", video_id=video_id)
        temp_resized_path = f"{settings.uploads_dir}/temp_resized_{video_id}.mp4"
        if not resize_to_720p_16_9(temp_path, temp_resized_path):
            raise Exception("Error en redimensionado de video")

        if os.path.exists(temp_path):
            os.remove(temp_path)
        os.rename(temp_resized_path, temp_path)

        logger.info("Step 3: Adding ANB intro/outro", video_id=video_id)
        if not add_anb_intro_outro(temp_path, output_path):
            raise Exception("Error al agregar cortinillas ANB")

        if os.path.exists(temp_path):
            os.remove(temp_path)

        logger.info(
            "Video processing completed successfully",
            video_id=video_id,
            output_path=output_path,
        )

        # Subir video procesado a storage
        try:
            processed_url = storage_manager.upload_processed_video(
                output_path, video_id
            )
            logger.info(
                "Video uploaded to storage",
                video_id=video_id,
                processed_url=processed_url,
            )
        except Exception as e:
            logger.error(
                "Error uploading processed video", video_id=video_id, error=str(e)
            )
            raise Exception(f"Error subiendo video procesado: {str(e)}")

        # Limpiar archivos temporales
        temp_files_to_clean = [
            input_path,
            temp_path,
            output_path,
            f"{settings.uploads_dir}/temp_resized_{video_id}.mp4",
        ]

        for temp_file in temp_files_to_clean:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.info("Cleaned temporary file", file_path=temp_file)
                except Exception as e:
                    logger.warning(
                        "Could not clean temporary file",
                        file_path=temp_file,
                        error=str(e),
                    )

        video.status = VideoStatus.PROCESSED.value
        video.file_processed_url = processed_url
        video.processed_at = datetime.utcnow()
        db.commit()

        # Métricas: video procesado exitosamente
        videos_processed.inc()
        video_processing_time.observe((datetime.utcnow() - start_time).total_seconds())

        return {
            "status": "completed",
            "video_id": video_id,
            "output_path": processed_url,
            "processed_at": datetime.utcnow().isoformat(),
        }

    except Exception as exc:
        logger.error(
            "Video processing failed",
            video_id=video_id,
            error=str(exc),
            task_id=self.request.id,
        )

        # Limpiar archivos temporales en caso de error
        temp_files_to_clean = [
            f"{settings.uploads_dir}/temp_input_{video_id}.mp4",
            f"{settings.uploads_dir}/temp_{video_id}.mp4",
            f"{settings.uploads_dir}/temp_processed_{video_id}.mp4",
            f"{settings.uploads_dir}/temp_resized_{video_id}.mp4",
        ]

        for temp_file in temp_files_to_clean:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.info(
                        "Cleaned temporary file after error", file_path=temp_file
                    )
                except Exception as e:
                    logger.warning(
                        "Could not clean temporary file after error",
                        file_path=temp_file,
                        error=str(e),
                    )

        # Actualizar base de datos con error
        try:
            if "db" in locals():
                video = db.query(Video).filter(Video.id == video_id).first()
                if video:
                    video.status = VideoStatus.FAILED.value
                    db.commit()
        except Exception as db_error:
            logger.error(
                "Error updating database with failure status", error=str(db_error)
            )

        # Métricas: video fallido
        videos_failed.inc()
        video_processing_time.observe((datetime.utcnow() - start_time).total_seconds())

        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error(
                "Max retries exceeded for video processing",
                video_id=video_id,
                task_id=self.request.id,
            )
            raise exc


# ---------- Funciones auxiliares (trim, resize, intro/outro) ----------


def trim_video_to_30s(input_path: str, output_path: str) -> bool:
    try:
        cmd = ["ffmpeg", "-i", input_path, "-t", "30", "-c", "copy", "-y", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
    except Exception as e:
        logger.error("Error trimming video", error=str(e), input_path=input_path)
        return False


def resize_to_720p_16_9(input_path: str, output_path: str) -> bool:
    try:
        cmd = [
            "ffmpeg",
            "-i",
            input_path,
            "-vf",
            "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black",
            "-c:a",
            "copy",
            "-y",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("FFmpeg error", stderr=result.stderr, stdout=result.stdout)
        return result.returncode == 0
    except Exception as e:
        logger.error("Error resizing video", error=str(e), input_path=input_path)
        return False


def add_anb_intro_outro(input_path: str, output_path: str) -> bool:
    try:
        os.makedirs(settings.assets_dir, exist_ok=True)
        intro_path = f"{settings.assets_dir}/anb_intro_5s.mp4"
        outro_path = f"{settings.assets_dir}/anb_outro_5s.mp4"
        if not os.path.exists(intro_path) or not os.path.exists(outro_path):
            create_simple_intro_outro(intro_path, outro_path)

        # Crear archivo de concatenación
        concat_file = f"/tmp/concat_{os.path.basename(input_path)}.txt"
        with open(concat_file, "w") as f:
            f.write(f"file '{intro_path}'\n")
            f.write(f"file '{input_path}'\n")
            f.write(f"file '{outro_path}'\n")

        # Concatenar usando archivo de texto
        cmd = [
            "ffmpeg",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_file,
            "-c",
            "copy",
            "-y",
            output_path,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        # Limpiar archivo temporal
        try:
            os.remove(concat_file)
        except:
            pass

        if result.returncode != 0:
            logger.error(
                "FFmpeg concat error", stderr=result.stderr, stdout=result.stdout
            )
            return False
        return True
    except Exception as e:
        logger.error("Error adding intro/outro", error=str(e), input_path=input_path)
        return False


def create_simple_intro_outro(intro_path: str, outro_path: str):
    try:
        os.makedirs(settings.assets_dir, exist_ok=True)
        cmd_intro = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "color=c=blue:size=1280x720:duration=5:rate=30",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000:duration=5",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-t",
            "5",
            "-y",
            intro_path,
        ]
        cmd_outro = [
            "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:size=1280x720:duration=5:rate=30",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=channel_layout=stereo:sample_rate=48000:duration=5",
            "-c:v",
            "libx264",
            "-c:a",
            "aac",
            "-t",
            "5",
            "-y",
            outro_path,
        ]
        subprocess.run(cmd_intro, capture_output=True, text=True)
        subprocess.run(cmd_outro, capture_output=True, text=True)
        logger.info(
            "Created simple intro/outro files",
            intro_path=intro_path,
            outro_path=outro_path,
        )
    except Exception as e:
        logger.error("Error creating intro/outro files", error=str(e))
