from celery import Celery
from kombu import Queue
import os


def create_celery_app(app_name: str, include_modules: list) -> Celery:
    """
    Crea una instancia de Celery compatible con RabbitMQ (local) o AWS SQS (nube).
    """
    use_sqs = bool(
        os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")
    )

    if use_sqs:
        # AWS - SQS
        region = os.getenv("AWS_REGION", "")
        queue_name = os.getenv("AWS_SQS_QUEUE_NAME", "")
        queue_url = os.getenv("AWS_SQS_QUEUE_URL")
        aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID", "")
        aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY", "")
        aws_session_token = os.getenv("AWS_SESSION_TOKEN", "")
        visibility_timeout = int(os.getenv("SQS_VISIBILITY_TIMEOUT", 3600))
        wait_time_seconds = int(os.getenv("SQS_WAIT_TIME_SECONDS", 20))
        max_messages = int(os.getenv("SQS_MAX_MESSAGES", 1))
        polling_interval = int(os.getenv("SQS_POLLING_INTERVAL", 1))

        # celery_app = Celery(app_name, broker=f"sqs://@sqs.{region}.amazonaws.com")
        celery_app = Celery(app_name,
                            broker="sqs://",
                            include=["worker.tasks.video_processing"])

        celery_app.conf.task_queues = (Queue(queue_name),)

        broker_transport_options = {
            "region": region,
            # "is_secure": True,
            'aws_access_key_id': aws_access_key_id,
            'aws_secret_access_key': aws_secret_access_key,
            'aws_session_token': aws_session_token,
            "visibility_timeout": visibility_timeout,
            "wait_time_seconds": wait_time_seconds,
            "max_messages": max_messages,
            "polling_interval": polling_interval,
            "predefined_queues": {
                queue_name: {
                    "url": queue_url
                }
            }
        }
        celery_app.conf.broker_transport_options = broker_transport_options

        print(f"[Celery] 🔶 Usando AWS SQS ({region})")

        TASK_QUEUE_NAME = queue_name

    else:
        # Local - RabbitMQ
        broker_url = os.getenv(
            "CELERY_BROKER_URL", "amqp://admin:admin@rabbitmq:5672//"
        )
        celery_app = Celery(app_name, broker=broker_url)
        celery_app.conf.task_default_queue = "uploaded-videos"

        print(f"[Celery] 🧩 Usando RabbitMQ local → {broker_url}")

        TASK_QUEUE_NAME = "uploaded-videos"

    celery_app.conf.update(
        task_default_queue=TASK_QUEUE_NAME,
        task_queues=(Queue(TASK_QUEUE_NAME),),

        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,

        # Seguridad recomendada
        worker_hijack_root_logger=False,
        task_track_started=True,
        task_acks_late=True,

        # Reduce sobrecarga en SQS
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=500,

        task_routes={
            "tasks.video_processing.process_video_task": {
                "queue": TASK_QUEUE_NAME
            }
        },

        include=include_modules,
    )

    return celery_app
