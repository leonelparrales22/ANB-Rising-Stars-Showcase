from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid
import datetime
import os
import shutil
import logging

logger = logging.getLogger(__name__)

from ..core.security import verify_token
from ..core.config import settings
from ..core.database import get_db
from ..models.user import User
from ..models.video import Video, VideoStatus
from ..models.vote import Vote

router_videos = APIRouter()

bearer = HTTPBearer()


@router_videos.post("/", response_class=JSONResponse)
def upload_video(
    title: str = Form(..., min_length=1, max_length=255),
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    auth: HTTPAuthorizationCredentials = Depends(bearer)
):
    """
    Subir un video con validaciones:
    - video_file: Archivo MP4, máximo 100MB
    - title: Título descriptivo del video
    """
    
    # Autenticación
    user_email = verify_token(auth.credentials)
    user = db.query(User).filter(User.email == user_email).first()
    
    # Validaciones del archivo
    if not video_file.filename:
        raise HTTPException(status_code=400, detail="No se proporcionó archivo de video")
    
    if not video_file.filename.lower().endswith('.mp4'):
        raise HTTPException(status_code=400, detail="El archivo debe ser MP4")
    
    # Verificar tamaño del archivo (100MB máximo)
    file_size = 0
    content = video_file.file.read()
    file_size = len(content)
    video_file.file.seek(0)  # Resetear posición del archivo
    
    if file_size > 100 * 1024 * 1024:  # 100MB en bytes
        raise HTTPException(status_code=400, detail="El archivo excede el límite de 100MB")
    
    # Crear directorio de uploads si no existe
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generar nombre único para el archivo
    video_id = str(uuid.uuid4())
    filename = f"{video_id}.mp4"
    file_path = os.path.join(upload_dir, filename)
    
    # Guardar archivo
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(video_file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar archivo: {str(e)}")
    
    # Crear registro en base de datos
    video_new = Video(
        id=video_id,
        title=title,
        status=VideoStatus.UPLOADED.value,
        id_user=user.id,
        uploaded_at=datetime.datetime.now(datetime.UTC),
        file_original_url=file_path,
        file_size_bytes=file_size
    )
    
    try:
        db.add(video_new)
        db.commit()
        db.refresh(video_new)
    except Exception as e:
        db.rollback()
        # Limpiar archivo si falla la BD
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error al guardar en base de datos: {str(e)}")

    # Enviar mensaje a cola 'uploaded-videos' con Celery
    try:
        # Configuración de Celery
        celery_app = Celery(
            'video_processor',
            broker='amqp://admin:admin@rabbitmq:5672//'
        )
        
        # Enviar tarea a la cola
        task = celery_app.send_task(
            'worker.tasks.video_processing.process_video_task',
            args=[video_new.id],
            queue='uploaded-videos'
        )
        
        # Actualizar video con task_id
        video_new.celery_task_id = task.id
        video_new.status = VideoStatus.PROCESSING.value
        video_new.processing_started_at = datetime.datetime.now(datetime.UTC)
        db.commit()
        
        task_id = task.id
        
    except Exception as e:
        logger.error(f"Error enviando tarea a Celery: {str(e)}")
        task_id = "error-celery"
    
    return JSONResponse(
        status_code=201,
        content={
            "message": "Video subido correctamente. Procesamiento en curso.",
            "task_id": task_id
        }
    )


@router_videos.delete('/{id_video}', response_class=JSONResponse)
def get_entity(id_video: str,
               db: Session = Depends(get_db),
               auth: HTTPAuthorizationCredentials = Depends(bearer)):

    user_email = verify_token(auth.credentials)

    user = db.query(User).filter(User.email == user_email).first()

    if id_video is None or id_video == "":
        raise HTTPException(status_code=400,
                            detail={'message': "El video con id especificado no existe o no pertence al usuario autenticado."})

    try:
        id_video_uuid = uuid.UUID(id_video)
    except ValueError:
        raise HTTPException(status_code=400,
                            detail={'message': "El video con id especificado no existe o no pertence al usuario autenticado."})

    video = db.query(Video).filter(Video.id == id_video, Video.id_user == user.id).first()

    if video is None:
        raise HTTPException(status_code=404,
                            detail={'message': "El video con id especificado no existe o no pertence al usuario autenticado."})

    if video.status == VideoStatus.PROCESSED.value:
        raise HTTPException(status_code=400,
                            detail={'message': "El video no puede ser eliminado porque no cumple las condiciones."})

    try:
        db.delete(video)

        db.commit()
    finally:
        db.rollback()

    return JSONResponse(status_code=200,
                        content={'message': f"El video con id {id_video} fue eliminado del sistema."})
