from shared.broker import create_celery_app
from worker.logging_config import configure_logging

# Configurar logs
configure_logging()

# Crear instancia global de Celery usando la configuración compartida
celery_app = create_celery_app(
    app_name="video_processor",
    include_modules=["worker.tasks.video_processing"],
)

if __name__ == "__main__":
    celery_app.start()
