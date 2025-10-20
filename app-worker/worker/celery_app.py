from celery import Celery
import os
from worker.logging_config import configure_logging
configure_logging()

# Configuración de Celery
celery_app = Celery(
    'video_processor',
    broker=os.getenv('CELERY_BROKER_URL', 'amqp://admin:admin@rabbitmq:5672//'),
    include=['worker.tasks.video_processing']
)

# Configuración básica
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_routes={
        'worker.tasks.video_processing.process_video_task': {'queue': 'uploaded-videos'},
    },
    task_default_queue='uploaded-videos',
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_hijack_root_logger=False
)

if __name__ == '__main__':
    celery_app.start()
