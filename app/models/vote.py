from sqlalchemy import Column, ForeignKey
from sqlalchemy import String, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime
import uuid

from ..core.database import Base


class Vote(Base):
    __tablename__ = "votes"

    id_video = Column(String, ForeignKey('videos.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    id_user = Column(String, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    voted_at = Column(DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False)
