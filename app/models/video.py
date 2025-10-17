from sqlalchemy import Column, ForeignKey
from sqlalchemy import String, Integer, DateTime, Float
from sqlalchemy.orm import relationship
import datetime
import uuid
from enum import Enum

from ..core.database import Base


class VideoStatus(Enum):
    UPLOADED = 'uploaded'
    PROCESSING = 'processing'
    PROCESSED = 'processed'
    FAILED = 'failed'


class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=str(uuid.uuid4()))
    title = Column(String, nullable=False)
    status = Column(String, nullable=False, default=VideoStatus.UPLOADED.value)
    id_user = Column(String, ForeignKey('users.id'), index=True, nullable=False)
    
    # URLs de archivos
    file_original_url = Column(String, nullable=False)
    file_processed_url = Column(String)
    
    # Metadatos del archivo original (según especificación)
    file_size_bytes = Column(Integer)  # Máximo 100MB = 104,857,600 bytes
    original_duration_seconds = Column(Float)
    original_resolution = Column(String)
    
    # Metadatos del video procesado
    processed_duration_seconds = Column(Float)  # Duración final (máx 30s + 10s de cortinillas)
    processed_resolution = Column(String, default="1280x720")
    
    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False)
    processing_started_at = Column(DateTime)
    processed_at = Column(DateTime)
    
    # Sistema de votación
    votes = Column(Integer, default=0, nullable=False)
    
    # Información de procesamiento
    celery_task_id = Column(String)

    # Relaciones
    user = relationship("User", back_populates="videos")
    votes_relation = relationship("Vote", back_populates="video", cascade="all, delete-orphan")
