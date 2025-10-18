from celery import Celery
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi import Query
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

router_public = APIRouter()
bearer = HTTPBearer()

@router_public.get("/videos")
def get_all_public_videos(db: Session = Depends(get_db)):
    """
    Obtener todos los videos que ya fueron procesados y estan listos para votacion
    """
    videos = db.query(Video).filter(Video.status == VideoStatus.PROCESSED.value).all()
    
    return [
        {
            "id": video.id,
            "title": video.title,
            "file_processed_url": video.file_processed_url,
            "uploaded_at": video.uploaded_at,
            "processed_at": video.processed_at,
            "votes": video.votes
        }
        for video in videos
    ]

@router_public.post('/videos/{video_id}/vote', response_class=JSONResponse)
def vote_for_video(
    video_id: str,
    db: Session = Depends(get_db),
    auth: HTTPAuthorizationCredentials = Depends(bearer)
):
    """
    Emitir un voto por un video público (solo 1 voto por usuario por video).
    """
    # Obtener usuario desde JWT
    user_email = verify_token(auth.credentials)
    user = db.query(User).filter(User.email == user_email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Usuario no autorizado")

    # Verificar existencia del video y que esté procesado
    video = db.query(Video).filter(Video.id == video_id, Video.status == VideoStatus.PROCESSED.value).first()

    if not video:
        raise HTTPException(status_code=404, detail="Video no encontrado o aún no está disponible públicamente")

    # Verificar si ya votó por ese video
    existing_vote = db.query(Vote).filter(Vote.id_user == user.id, Vote.id_video == video_id).first()

    if existing_vote:
        raise HTTPException(status_code=400, detail="Ya has votado por este video")

    # Crear voto
    new_vote = Vote(id_user=user.id, id_video=video_id)

    try:
        db.add(new_vote)
        # Incrementar contador de votos
        video.votes += 1
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error al registrar el voto")

    return JSONResponse(status_code=200,
                        content={'message': "Voto registrado exitosamente."})

@router_public.get("/rankings")
def get_rankings(
    city: str = Query(None, description="Filtrar por ciudad"),
    db: Session = Depends(get_db)
):
    """
    Devuelve el ranking de usuarios basado en la suma de votos de sus videos procesados,
    agrupados por usuario. Soporta filtro opcional por ciudad.
    """
    try:
        query = (
            db.query(
                Video.id_user,
                func.sum(Video.votes).label("total_votes"),
                User.first_name,
                User.last_name,
                User.city,
            )
            .join(User, User.id == Video.id_user)
            .filter(Video.status == VideoStatus.PROCESSED.value)
        )

        if city:
            query = query.filter(func.lower(User.city) == city.lower())

        result = (
            query
            .group_by(Video.id_user, User.first_name, User.last_name, User.city)
            .order_by(desc("total_votes"))
            .all()
        )

        rankings = []
        for idx, row in enumerate(result):
            rankings.append({
                "position": idx + 1,
                "username": f"{row.first_name} {row.last_name}",
                "city": row.city,
                "votes": row.total_votes or 0
            })

        return rankings

    except Exception as e:
        print("Error en get_rankings:", e)
        raise HTTPException(status_code=400, detail="Error al obtener el ranking")
