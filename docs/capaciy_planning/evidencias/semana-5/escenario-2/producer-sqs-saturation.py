import os
import time
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# ============================
# Config Celery SQS
# ============================

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

SQS_QUEUE = os.getenv("SQS_QUEUE_NAME")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

celery_app = Celery(
    "sender",
    broker="sqs://"
)

# Configuración SQS
celery_app.conf.broker_transport_options = {
    "region": AWS_REGION,
    "visibility_timeout": 3600,
    "wait_time_seconds": 1,
    "predefined_queues": {
        SQS_QUEUE: {"url": SQS_QUEUE_URL}
    },
    "aws_access_key_id": AWS_ACCESS_KEY,
    "aws_secret_access_key": AWS_SECRET_KEY,
}

if AWS_SESSION_TOKEN:
    celery_app.conf.broker_transport_options["aws_session_token"] = AWS_SESSION_TOKEN

celery_app.conf.task_default_queue = SQS_QUEUE
celery_app.conf.task_queues = ()

# ============================
# RAMP-UP de tareas
# ============================

if __name__ == "__main__":
    VIDEO_ID = "bfc776b1-eee1-49de-b59c-350f43a02c1e"
    TOTAL_ENVIADAS = 0
    WAIT_TIME = 10 
    RAMP_STEPS = [2, 4, 6, 8, 10]

    for batch in RAMP_STEPS:
        print(f"\n🚀 Enviando lote de {batch} tareas...")

        for i in range(batch):
            celery_app.send_task(
                "worker.tasks.video_processing.process_video_task",
                args=[VIDEO_ID],
                queue=SQS_QUEUE
            )

            TOTAL_ENVIADAS += 1
            print(f"✔ Tarea #{TOTAL_ENVIADAS} enviada (video_id={VIDEO_ID})")

        # Pausa pequeña entre rampas para evitar explosión instantánea
        print(f"⏳ Lote de {batch} completado. Preparando siguiente rampa, esperando {WAIT_TIME}s antes de la siguiente ronda...\n")
        time.sleep(WAIT_TIME)

    print("\n====================================")
    print(f"   ✔ TOTAL de tareas enviadas: {TOTAL_ENVIADAS}")
    print("====================================\n")
