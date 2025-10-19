from sqlalchemy import Column, ForeignKey
from sqlalchemy import String, DateTime
from sqlalchemy.orm import relationship

from shared.db.config import Base
import datetime


class Vote(Base):
    __tablename__ = "votes"

    id_video = Column(
        String,
        ForeignKey("videos.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    id_user = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    voted_at = Column(
        DateTime, default=datetime.datetime.now(datetime.UTC), nullable=False
    )

    # Relaciones
    video = relationship("Video", back_populates="votes_relation")
    user = relationship("User", back_populates="votes")
