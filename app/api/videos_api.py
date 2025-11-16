from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid
import datetime
import os
import shutil
import logging

from ..core.security import verify_token

from shared.broker import create_celery_app
from shared.storage import storage_manager
from shared.config.settings import settings
from shared.db.config import get_db
from shared.db.models.user import User
from shared.db.models.video import Video, VideoStatus
from shared.db.models.vote import Vote

logger = logging.getLogger(__name__)

router_videos = APIRouter()

bearer = HTTPBearer()


@router_videos.post("/upload", response_class=JSONResponse)
def upload_video(
    title: str = Form(..., min_length=1, max_length=255),
    video_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    auth: HTTPAuthorizationCredentials = Depends(bearer),
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
        raise HTTPException(
            status_code=400, detail={"message": "No se proporcionó archivo de video"}
        )

    if not video_file.filename.lower().endswith(".mp4"):
        raise HTTPException(
            status_code=400, detail={"message": "El archivo debe ser MP4"}
        )

    # Verificar tamaño del archivo (100MB máximo)
    file_size = 0
    content = video_file.file.read()
    file_size = len(content)
    video_file.file.seek(0)  # Resetear posición del archivo

    if file_size > 100 * 1024 * 1024:  # 100MB en bytes
        raise HTTPException(
            status_code=400, detail={"message": "El archivo excede el límite de 100MB"}
        )

    # Generar nombre único para el archivo
    video_id = str(uuid.uuid4())
    filename = f"{video_id}.mp4"

    # Guardar archivo
    try:
        file_url = storage_manager.upload_video(video_file.file, video_id, filename)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail={"message": f"Error al guardar archivo: {str(e)}"}
        )

    # Crear registro en base de datos
    video_new = Video(
        id=video_id,
        title=title,
        status=VideoStatus.UPLOADED.value,
        id_user=user.id,
        uploaded_at=datetime.datetime.now(datetime.timezone.utc),
        file_original_url=file_url,
        file_size_bytes=file_size,
    )

    try:
        db.add(video_new)
        db.commit()
        db.refresh(video_new)
    except Exception as e:
        db.rollback()
        # Limpiar archivo si falla la BD
        try:
            storage_manager.delete_video(file_url)
        except:
            pass
        raise HTTPException(
            status_code=500,
            detail={"message": f"Error al guardar en base de datos: {str(e)}"},
        )

    # Para pruebas de carga, no se envía tarea a Celery
    if settings.environment == "testing":
        return JSONResponse(
            status_code=202,
            content={
                "message": "Video subido correctamente. Procesamiento en curso.",
                "task_id": "test-task-id",
            },
        )

    # Enviar mensaje a cola 'uploaded-videos' con Celery
    try:
        # Configuración de Celery
        celery_app = create_celery_app(
            "video_processor", ["worker.tasks.video_processing"]
        )

        # Enviar tarea a la cola
        task = celery_app.send_task(
            "worker.tasks.video_processing.process_video_task",
            args=[video_new.id],
            queue=settings.queue_name,
        )

        # Actualizar video con task_id
        video_new.celery_task_id = task.id
        video_new.status = VideoStatus.PROCESSING.value
        video_new.processing_started_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()

        task_id = task.id

    except Exception as e:
        logger.error(f"Error enviando tarea a Celery: {str(e)}")
        task_id = "error-celery"

    return JSONResponse(
        status_code=201,
        content={
            "message": "Video subido correctamente. Procesamiento en curso.",
            "task_id": task_id,
        },
    )


@router_videos.get("/", response_class=JSONResponse)
def get_videos(
    db: Session = Depends(get_db), auth: HTTPAuthorizationCredentials = Depends(bearer)
):
    """
    Obtener todos los videos del usuario autenticado
    """

    # Autenticación
    user_email = verify_token(auth.credentials)
    user = db.query(User).filter(User.email == user_email).first()

    processed_videos = (
        db.query(Video)
        .filter(Video.id_user == user.id, Video.status == VideoStatus.PROCESSED.value)
        .all()
    )

    not_processed_videos = (
        db.query(Video)
        .filter(Video.id_user == user.id, Video.status != VideoStatus.PROCESSED.value)
        .all()
    )

    videos = []
    for video in processed_videos:
        videos.append(
            {
                "video_id": video.id,
                "title": video.title,
                "status": video.status,
                "uploaded_at": video.uploaded_at,
                "processed_at": video.processed_at,
                "processed_url": video.file_processed_url,
            }
        )

    for video in not_processed_videos:
        videos.append(
            {
                "video_id": video.id,
                "title": video.title,
                "status": video.status,
                "uploaded_at": video.uploaded_at,
            }
        )

    return JSONResponse(
        status_code=200, content=jsonable_encoder(videos, exclude_none=True)
    )


@router_videos.get("/{id_video}", response_class=JSONResponse)
def get_video(
    id_video: str,
    db: Session = Depends(get_db),
    auth: HTTPAuthorizationCredentials = Depends(bearer),
):
    """
    Obtener un video específico del usuario autenticado
    """

    # Autenticación
    user_email = verify_token(auth.credentials)
    user = db.query(User).filter(User.email == user_email).first()

    video = (
        db.query(Video).filter(Video.id == id_video, Video.id_user == user.id).first()
    )

    if video is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "El video con id especificado no existe o no pertence al usuario"
            },
        )

    return JSONResponse(
        status_code=200,
        content=jsonable_encoder(
            {
                "video_id": video.id,
                "title": video.title,
                "status": video.status,
                "uploaded_at": video.uploaded_at,
                "processed_at": (
                    video.processed_at
                    if video.status == VideoStatus.PROCESSED.value
                    else None
                ),
                "original_url": (
                    video.file_original_url
                    if video.status == VideoStatus.UPLOADED.value
                    else None
                ),
                "processed_url": (
                    video.file_processed_url
                    if video.status == VideoStatus.PROCESSED.value
                    else None
                ),
                "votes": (
                    video.votes if video.status == VideoStatus.PROCESSED.value else None
                ),
            },
            exclude_none=True,
        ),
    )


@router_videos.delete("/{id_video}", response_class=JSONResponse)
def delete_video(
    id_video: str,
    db: Session = Depends(get_db),
    auth: HTTPAuthorizationCredentials = Depends(bearer),
):

    # Autenticación
    user_email = verify_token(auth.credentials)
    user = db.query(User).filter(User.email == user_email).first()

    video = (
        db.query(Video).filter(Video.id == id_video, Video.id_user == user.id).first()
    )

    if video is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": "El video con id especificado no existe o no pertence al usuario autenticado"
            },
        )

    if video.status == VideoStatus.PROCESSED.value:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "El video no puede ser eliminado porque no cumple las condiciones"
            },
        )

    original_url = video.file_original_url
    processed_url = video.file_processed_url

    # Eliminar archivos usando storage manager
    try:
        if original_url:
            storage_manager.delete_video(original_url)
        if processed_url:
            storage_manager.delete_video(processed_url)
    except Exception as e:
        logger.warning(f"Error eliminando archivos: {str(e)}")
        # Continuar con la eliminación de BD aunque falle la eliminación de archivos

    try:
        db.delete(video)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"message": "Error al eliminar el video"},
        )

    return JSONResponse(
        status_code=200,
        content={
            "message": "El vìdeo fue eliminado exitosamente",
            "video_id": video.id,
        },
    )
