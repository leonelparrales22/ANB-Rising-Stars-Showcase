import subprocess
import os
import structlog
from datetime import datetime
from worker.celery_app import celery_app

logger = structlog.get_logger()

@celery_app.task(bind=True, name='worker.tasks.video_processing.process_video_task')
def process_video_task(self, video_id: str):
    """
    Tarea principal de procesamiento de video que ejecuta:
    1. Recortar a máximo 30 segundos
    2. Ajustar a 720p 16:9
    3. Agregar cortinillas ANB (5s inicio + 5s final)
    """
    
    logger.info("Starting video processing", video_id=video_id, task_id=self.request.id)
    
    try:
        # TODO: Conectar con base de datos para obtener información del video
        # Por ahora simulamos con rutas hardcodeadas
        
        # Rutas de archivos
        input_path = f"uploads/{video_id}.mp4"
        temp_path = f"uploads/temp_{video_id}.mp4"
        output_path = f"uploads/processed_{video_id}.mp4"
        
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
        resize_result = resize_to_720p_16_9(temp_path, temp_path)
        if not resize_result:
            raise Exception("Error en redimensionado de video")
        
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
        
        # TODO: Actualizar base de datos con resultado
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
        
        # TODO: Actualizar base de datos con error
        raise self.retry(exc=exc, countdown=60, max_retries=3)


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
            '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2',
            '-c:a', 'copy',  # Copiar audio sin re-encoding
            '-y',
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0
        
    except Exception as e:
        logger.error("Error resizing video", error=str(e), input_path=input_path)
        return False


def add_anb_intro_outro(input_path: str, output_path: str) -> bool:
    """Agregar cortinillas de apertura y cierre de ANB (5 segundos cada una)"""
    try:
        # TODO: Crear archivos de cortinillas ANB
        # Por ahora simulamos concatenación
        
        intro_path = "assets/anb_intro_5s.mp4"
        outro_path = "assets/anb_outro_5s.mp4"
        
        # Si no existen las cortinillas, crear un video simple
        if not os.path.exists(intro_path):
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
        # Crear directorio assets si no existe
        os.makedirs("assets", exist_ok=True)
        
        # Crear cortinilla de 5 segundos con color sólido
        cmd_intro = [
            'ffmpeg', '-f', 'lavfi', '-i', 'color=c=blue:size=1280x720:duration=5',
            '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000',
            '-y', intro_path
        ]
        
        cmd_outro = [
            'ffmpeg', '-f', 'lavfi', '-i', 'color=c=red:size=1280x720:duration=5',
            '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000',
            '-y', outro_path
        ]
        
        subprocess.run(cmd_intro, capture_output=True)
        subprocess.run(cmd_outro, capture_output=True)
        
        logger.info("Created simple intro/outro files", intro_path=intro_path, outro_path=outro_path)
        
    except Exception as e:
        logger.error("Error creating intro/outro files", error=str(e))
