from celery import Celery

def create_celery_app() -> Celery:
    celery_app = Celery("audio-processor-celery", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")
    celery_app.autodiscover_tasks(['app.workers'])
    return celery_app

celery_app = create_celery_app()
