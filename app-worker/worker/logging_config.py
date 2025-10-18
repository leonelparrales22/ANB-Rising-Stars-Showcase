import logging
import os
from logging.handlers import RotatingFileHandler
import structlog

# === Paths de logs ===
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
JSON_LOG_FILE = os.path.join(LOG_DIR, 'celery_json.log')   # Solo logs estructurados
DEBUG_LOG_FILE = os.path.join(LOG_DIR, 'celery_debug.log') # (Opcional) todos los logs

# Asegurarse de que la carpeta existe
os.makedirs(LOG_DIR, exist_ok=True)

def configure_logging():
    # === Limpieza de handlers previos ===
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)

    # === Handler solo para logs estructurados de tareas ===
    json_handler = RotatingFileHandler(
        filename=JSON_LOG_FILE,
        maxBytes=10_000_000,
        backupCount=5
    )
    json_handler.setLevel(logging.INFO)
    json_handler.setFormatter(logging.Formatter('%(message)s'))

    # Solo incluir logs de tus tareas (ej. video_processing)
    class TaskOnlyFilter(logging.Filter):
        def filter(self, record):
            return record.name.startswith("worker.tasks.")

    json_handler.addFilter(TaskOnlyFilter())
    root_logger.addHandler(json_handler)

    # === (Opcional) Consola o archivo para logs generales ===
    if os.getenv("LOG_TO_CONSOLE", "true").lower() == "true":
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(console_handler)
    else:
        debug_file_handler = RotatingFileHandler(
            filename=DEBUG_LOG_FILE,
            maxBytes=10_000_000,
            backupCount=3
        )
        debug_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(debug_file_handler)

    # === Configuración de structlog ===
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True
    )
