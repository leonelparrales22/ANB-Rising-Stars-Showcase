import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Base de datos
    database_url: str = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@postgres:5432/anb_database')
    
    # Celery
    celery_broker_url: str = os.getenv('CELERY_BROKER_URL', 'amqp://admin:admin@rabbitmq:5672//')
    
    # Almacenamiento
    uploads_dir: str = os.getenv('UPLOADS_DIR', 'uploads')
    assets_dir: str = os.getenv('ASSETS_DIR', 'assets')
    
    # AWS (para futuro)
    aws_access_key_id: str = os.getenv('AWS_ACCESS_KEY_ID', '')
    aws_secret_access_key: str = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    aws_region: str = os.getenv('AWS_REGION', 'us-east-1')
    s3_bucket: str = os.getenv('S3_BUCKET', 'anb-videos')
    
    class Config:
        env_file = ".env"

settings = Settings()
