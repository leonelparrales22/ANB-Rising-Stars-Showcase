from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

# Crear engine para el worker
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Obtener sesión de base de datos para el worker"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
