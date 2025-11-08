import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Base de datos
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/anb_database")

    # Celery
    celery_broker_url: str = os.getenv("CELERY_BROKER_URL", "amqp://admin:admin@rabbitmq:5672//")

    # Almacenamiento
    uploads_dir: str = os.getenv("UPLOADS_DIR", "uploads")
    assets_dir: str = os.getenv("ASSETS_DIR", "assets")

    # Seguridad
    secret_key: str = os.getenv("SECRET_KEY", "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 120

    # Ambiente de ejecución
    # `testing`: para pruebas de carga.
    # `production`: para funcionamiento normal.
    environment: str = os.getenv("ENVIRONMENT", "production")

    # AWS (para futuro)
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_session_token: str = os.getenv("AWS_SESSION_TOKEN", "")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    s3_bucket: str = os.getenv("S3_BUCKET", "anb-videos")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
