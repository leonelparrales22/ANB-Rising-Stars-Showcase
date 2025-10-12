from sqlalchemy import Column, ForeignKey
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime
import uuid
from enum import Enum

from ..core.database import Base


from enum import Enum


class VideoStatus(Enum):
    UPLOADED = 'uploaded'
    PROCESSED = 'processed'


class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, default=str(uuid.uuid4()))
    title = Column(String, nullable=False)
    status = Column(String, nullable=False)
    id_user = Column(String, ForeignKey('users.id'), index=True, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False)
    file_uploaded_url = Column(String, nullable=False)
    processed_at = Column(DateTime)
    file_uploaded_url = Column(String)
    votes = Column(Integer, default=0, nullable=False)
