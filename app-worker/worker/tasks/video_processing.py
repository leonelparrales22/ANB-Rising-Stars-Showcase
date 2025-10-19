import subprocess
import os
import structlog
from datetime import datetime
from worker.celery_app import celery_app
from shared.database import get_db
from shared.config import settings
import sys
sys.path.append('/app')
from app.models.video import Video, VideoStatus
from app.models.user import User
from app.models.vote import Vote

logger = structlog.get_logger()

@celery_app.task(bind=True, name='worker.tasks.video_processing.process_video_task', max_retries=5, default_retry_delay=60)
def process_video_task(self, video_id: str):
    """
    Tarea principal de procesamiento de video que ejecuta:
    1. Recortar a máximo 30 segundos
    2. Ajustar a 720p 16:9
    3. Agregar cortinillas ANB (5s inicio + 5s final)
    """
    
    logger.info("Starting video processing", video_id=video_id, task_id=self.request.id)
    
    try:
        # Conectar con base de datos para obtener información del video
        db = next(get_db())
        video = db.query(Video).filter(Video.id == video_id).first()
        
        if not video:
            raise Exception(f"Video con ID {video_id} no encontrado en la base de datos")
        
        # Actualizar estado a PROCESSING
        video.status = VideoStatus.PROCESSING.value
        video.processing_started_at = datetime.utcnow()
        db.commit()
        
        # Rutas de archivos usando configuración
        input_path = video.file_original_url
        temp_path = f"{settings.uploads_dir}/temp_{video_id}.mp4"
        output_path = f"{settings.uploads_dir}/processed_{video_id}.mp4"
        
        # Verificar que existe el archivo original
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Video original no encontrado: {input_path}")
        
        # Paso 1: Recortar a máximo 30 segundos
        logger.info("Step 1: Trimming video to 30 seconds", video_id=video_id)
        trim_result = trim_video_to_30s(input_path, temp_path)
        if not trim_result:
            raise Exception("Error en recorte de video")
        
        # Paso 2: Ajustar a 720p 16:9
        logger.info("Step 2: Resizing to 720p 16:9", video_id=video_id)
        temp_resized_path = f"{settings.uploads_dir}/temp_resized_{video_id}.mp4"
        resize_result = resize_to_720p_16_9(temp_path, temp_resized_path)
        if not resize_result:
            raise Exception("Error en redimensionado de video")
        
        # Limpiar archivo temporal anterior
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Renombrar archivo redimensionado
        os.rename(temp_resized_path, temp_path)
        
        # Paso 3: Agregar cortinillas ANB
        logger.info("Step 3: Adding ANB intro/outro", video_id=video_id)
        add_intro_outro_result = add_anb_intro_outro(temp_path, output_path)
        if not add_intro_outro_result:
            raise Exception("Error al agregar cortinillas ANB")
        
        # Limpiar archivo temporal
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        logger.info("Video processing completed successfully", 
                   video_id=video_id, 
                   output_path=output_path)
        
        # Limpiar archivos temporales
        temp_files_to_clean = [
            f"{settings.uploads_dir}/temp_{video_id}.mp4",
            f"{settings.uploads_dir}/temp_resized_{video_id}.mp4"
        ]
        
        for temp_file in temp_files_to_clean:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.info("Cleaned temporary file", file_path=temp_file)
                except Exception as e:
                    logger.warning("Could not clean temporary file", file_path=temp_file, error=str(e))
        
        # Actualizar base de datos con resultado exitoso
        video.status = VideoStatus.PROCESSED.value
        video.file_processed_url = output_path
        video.processed_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "completed",
            "video_id": video_id,
            "output_path": output_path,
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as exc:
        logger.error("Video processing failed", 
                    video_id=video_id, 
                    error=str(exc), 
                    task_id=self.request.id)
        
        # Limpiar archivos temporales en caso de error
        temp_files_to_clean = [
            f"{settings.uploads_dir}/temp_{video_id}.mp4",
            f"{settings.uploads_dir}/temp_resized_{video_id}.mp4"
        ]
        
        for temp_file in temp_files_to_clean:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    logger.info("Cleaned temporary file after error", file_path=temp_file)
                except Exception as e:
                    logger.warning("Could not clean temporary file after error", file_path=temp_file, error=str(e))
        
        # Actualizar base de datos con error
        try:
            if 'db' in locals():
                video = db.query(Video).filter(Video.id == video_id).first()
                if video:
                    video.status = VideoStatus.FAILED.value
                    db.commit()
        except Exception as db_error:
            logger.error("Error updating database with failure status", error=str(db_error))
        
        # Reintentar la tarea automáticamente con delay y límite de reintentos
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            logger.error("Max retries exceeded for video processing", video_id=video_id, task_id=self.request.id)
            raise exc


def trim_video_to_30s(input_path: str, output_path: str) -> bool:
    """Recortar video a máximo 30 segundos"""
    try:
        cmd = [
            'ffmpeg', '-i', input_path,
            '-t', '30',  # Máximo 30 segundos
            '-c', 'copy',  # Copiar sin re-encoding para velocidad
            '-y',  # Sobrescribir archivo de salida
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
        
    except Exception as e:
        logger.error("Error trimming video", error=str(e), input_path=input_path)
        return False


def resize_to_720p_16_9(input_path: str, output_path: str) -> bool:
    """Ajustar video a resolución 720p con relación de aspecto 16:9"""
    try:
        cmd = [
            'ffmpeg', '-i', input_path,
            '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=black',
            '-c:a', 'copy',  # Copiar audio sin re-encoding
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("FFmpeg error", stderr=result.stderr, stdout=result.stdout)
        return result.returncode == 0
        
    except Exception as e:
        logger.error("Error resizing video", error=str(e), input_path=input_path)
        return False


def add_anb_intro_outro(input_path: str, output_path: str) -> bool:
    """Agregar cortinillas de apertura y cierre de ANB (5 segundos cada una)"""
    try:
        # Crear directorio assets si no existe
        os.makedirs(settings.assets_dir, exist_ok=True)
        
        intro_path = f"{settings.assets_dir}/anb_intro_5s.mp4"
        outro_path = f"{settings.assets_dir}/anb_outro_5s.mp4"
        
        # Si no existen las cortinillas, crear videos simples
        if not os.path.exists(intro_path) or not os.path.exists(outro_path):
            create_simple_intro_outro(intro_path, outro_path)
        
        # Concatenar: intro + video principal + outro
        cmd = [
            'ffmpeg',
            '-i', intro_path,
            '-i', input_path,
            '-i', outro_path,
            '-filter_complex', '[0:v:0][0:a:0][1:v:0][1:a:0][2:v:0][2:a:0]concat=n=3:v=1:a=1[outv][outa]',
            '-map', '[outv]', '-map', '[outa]',
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
        
    except Exception as e:
        logger.error("Error adding intro/outro", error=str(e), input_path=input_path)
        return False


def create_simple_intro_outro(intro_path: str, outro_path: str):
    """Crear cortinillas simples de 5 segundos (temporal)"""
    try:
        os.makedirs(settings.assets_dir, exist_ok=True)
        
        cmd_intro = [
            'ffmpeg', '-f', 'lavfi', '-i', 'color=c=blue:size=1280x720:duration=5:rate=30',
            '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000:duration=5',
            '-c:v', 'libx264', '-c:a', 'aac', '-t', '5',
            '-y', intro_path
        ]
        
        cmd_outro = [
            'ffmpeg', '-f', 'lavfi', '-i', 'color=c=red:size=1280x720:duration=5:rate=30',
            '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000:duration=5',
            '-c:v', 'libx264', '-c:a', 'aac', '-t', '5',
            '-y', outro_path
        ]
        
        result_intro = subprocess.run(cmd_intro, capture_output=True, text=True)
        result_outro = subprocess.run(cmd_outro, capture_output=True, text=True)
        
        if result_intro.returncode != 0:
            logger.error("Error creating intro", stderr=result_intro.stderr)
        if result_outro.returncode != 0:
            logger.error("Error creating outro", stderr=result_outro.stderr)
        
        logger.info("Created simple intro/outro files", intro_path=intro_path, outro_path=outro_path)
        
    except Exception as e:
        logger.error("Error creating intro/outro files", error=str(e))
