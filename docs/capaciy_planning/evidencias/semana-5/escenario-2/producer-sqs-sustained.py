import os
import time
import boto3
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# ============================
# Configuración SQS / Celery
# ============================

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

SQS_QUEUE = os.getenv("SQS_QUEUE_NAME")
SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")

celery_app = Celery("sender", broker="sqs://")

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
# Cliente SQS para monitoreo
# ============================

sqs = boto3.client(
    "sqs",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
)

def get_queue_backlog():
    """Obtiene número aproximado de mensajes pendientes en SQS."""
    attrs = sqs.get_queue_attributes(
        QueueUrl=SQS_QUEUE_URL,
        AttributeNames=["ApproximateNumberOfMessages"]
    )
    return int(attrs["Attributes"]["ApproximateNumberOfMessages"])


# ============================
# PRUEBA SOSTENIDA CON CONTROL
# ============================

if __name__ == "__main__":
    VIDEO_ID = "bfc776b1-eee1-49de-b59c-350f43a02c1e"

    # Cantidad de tareas a enviar por iteración
    TASKS_PER_CYCLE = 5

    # Máximo backlog permitido
    MAX_QUEUE_SIZE = 10

    # Espera cuando la cola está saturada
    WAIT_IF_FULL = 10

    # Intervalo de envío cuando la cola está estable
    SEND_INTERVAL = 3

    # Tiempo total de la prueba
    DURATION_SECONDS = 120

    TOTAL_SENT = 0
    start_time = time.time()

    print("\n🚀 Iniciando PRUEBA SOSTENIDA con control de saturación...\n")

    while True:

        elapsed = time.time() - start_time
        if elapsed >= DURATION_SECONDS:
            break

        backlog = get_queue_backlog()
        print(f"📊 Backlog actual SQS: {backlog} mensajes")

        if backlog >= MAX_QUEUE_SIZE:
            print(f"⚠️ Cola saturada ({backlog}/{MAX_QUEUE_SIZE}). Esperando {WAIT_IF_FULL}s...")
            time.sleep(WAIT_IF_FULL)
            continue

        print(f"➡️ Enviando {TASKS_PER_CYCLE} tareas...")

        for _ in range(TASKS_PER_CYCLE):
            celery_app.send_task(
                "worker.tasks.video_processing.process_video_task",
                args=[VIDEO_ID],
                queue=SQS_QUEUE
            )
            TOTAL_SENT += 1

        print(f"✔ Enviadas hasta ahora: {TOTAL_SENT}")
        print(f"⏳ Esperando {SEND_INTERVAL}s antes del próximo ciclo...\n")
        time.sleep(SEND_INTERVAL)

    print("\n====================================")
    print(f"   ✔ TOTAL de tareas enviadas: {TOTAL_SENT}")
    print("====================================\n")
