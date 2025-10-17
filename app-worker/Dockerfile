FROM python:3.11-slim

WORKDIR /app

# Instalar FFmpeg para procesamiento de video
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements y instalar dependencias
COPY app-worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del worker
COPY app-worker/ .

# Copiar shared y app desde el directorio raíz
COPY shared /app/shared
COPY app /app/app

# Comando por defecto para ejecutar worker
CMD ["celery", "-A", "worker.celery_app", "worker", "--loglevel=info", "--queues=uploaded-videos"]
