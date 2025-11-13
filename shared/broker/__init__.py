from celery import Celery
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
        region = os.getenv("AWS_REGION", "us-east-1")
        queue_name = os.getenv("AWS_SQS_QUEUE_NAME", "uploaded-videos")
        queue_url = os.getenv("AWS_SQS_QUEUE_URL")

        celery_app = Celery(app_name, broker="sqs://")
        broker_transport_options = {"region": region, "visibility_timeout": 3600}

        if queue_url:
            broker_transport_options["predefined_queues"] = {
                queue_name: {"url": queue_url}
            }

        celery_app.conf.update(
            broker_transport_options=broker_transport_options,
            task_default_queue=queue_name,
        )

        print(f"[Celery] 🔶 Usando AWS SQS ({region})")

    else:
        # Local - RabbitMQ
        broker_url = os.getenv(
            "CELERY_BROKER_URL", "amqp://admin:admin@rabbitmq:5672//"
        )
        celery_app = Celery(app_name, broker=broker_url)
        celery_app.conf.task_default_queue = "uploaded-videos"

        print(f"[Celery] 🧩 Usando RabbitMQ local → {broker_url}")

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        worker_max_tasks_per_child=1000,
        worker_hijack_root_logger=False,
        include=include_modules,
    )

    return celery_app
