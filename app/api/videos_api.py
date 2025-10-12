from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
import uuid
import datetime

from ..core.security import verify_token
from ..core.config import settings
from ..core.database import get_db
from ..schemas.videos_schemas import CreateVideoRequest
from ..models.user import User
from ..models.video import Video, VideoStatus
from ..models.vote import Vote

router_videos = APIRouter()

bearer = HTTPBearer()


@router_videos.post("/", response_class=JSONResponse)
def post_video(request: CreateVideoRequest,
               db: Session = Depends(get_db),
               auth: HTTPAuthorizationCredentials = Depends(bearer)):

    user_email = verify_token(auth.credentials)

    user = db.query(User).filter(User.email == user_email).first()

    video_new = Video(title=request.title,
                      status=VideoStatus.UPLOADED.value,
                      id_user=user.id,
                      uploaded_at=datetime.datetime.now(datetime.UTC),
                      file_uploaded_url="file://ruta/video.mp4")
    try:
        db.add(video_new)
        db.commit()
    finally:
        db.rollback()

    # TODO: Enviar mensaje a `Cola Videos Por Procesar`.

    return JSONResponse(status_code=201,
                        content={'message': "Video subido correctamente. Procesamiento en curso.",
                                 'task_id': "task-id-123",
                                 'id_video': video_new.id})


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
