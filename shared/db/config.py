from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from shared.config.settings import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Obtener sesión de base de datos.
    Si se usa en FastAPI → funciona como dependencia (yield).
    Si se usa fuera de FastAPI (por ejemplo en Celery) → devuelve la sesión directamente.
    """
    db = SessionLocal()
    # Si se llama como generador (FastAPI) → yield
    try:
        yield db
    except RuntimeError:
        # Si no hay ciclo async activo → uso fuera de FastAPI
        return db
    finally:
        db.close()
