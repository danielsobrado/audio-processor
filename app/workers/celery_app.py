import asyncio
import logging
from typing import Optional

from celery import Celery
# --- BEGIN: Import Queue for DLQ ---
from kombu import Queue
# --- END: Import Queue for DLQ ---

from app.config.settings import get_settings
from app.core.audio_processor import AudioProcessor
from app.services.translation import TranslationService

logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()


def create_celery_app() -> Celery:
    """
    Create and configure the Celery application with reliability features.
    
    Features:
    - Automatic retries with exponential backoff
    - Dead letter queue for failed tasks
    - Late acknowledgment to prevent task loss
    
    Queue Management:
    - Default queue: 'default' (for normal tasks)
    - Dead letter queue: 'dead_letter' (for failed tasks)
    
    To monitor queues:
        uv run celery -A app.workers.celery_app inspect active_queues
    
    To process dead letter queue:
        uv run celery -A app.workers.celery_app worker --queues=dead_letter
    """
    celery_app = Celery(
        "audio-processor-celery",
        broker=settings.celery.broker_url,
        backend=settings.celery.result_backend,
    )

    # Configure Celery with settings
    celery_app.conf.update(
        task_serializer=settings.celery.task_serializer,
        result_serializer=settings.celery.result_serializer,
        accept_content=settings.celery.accept_content,
        timezone=settings.celery.timezone,
        enable_utc=settings.celery.enable_utc,
        worker_concurrency=settings.celery.worker_concurrency,
        # Acknowledge task only after it has been successfully executed.
        # This prevents losing tasks if a worker crashes mid-execution.
        task_acks_late=True,
        # Define our queues: one for normal tasks, one for failed tasks.
        # To monitor dead letter queue: uv run celery -A app.workers.celery_app inspect active_queues
        # To process dead letter queue: uv run celery -A app.workers.celery_app worker --queues=dead_letter
        task_queues=(
            Queue('default', routing_key='task.#'),
            Queue('dead_letter', routing_key='dead_letter.#'),
        ),
        task_default_queue='default',
        task_default_exchange='tasks',
        task_default_routing_key='task.default',
    )

    celery_app.autodiscover_tasks(["app.workers"])
    return celery_app


celery_app = create_celery_app()

# Global instance for the worker - initialized once per worker process
audio_processor_instance: Optional[AudioProcessor] = None
translation_service_instance: Optional[TranslationService] = None


@celery_app.on_after_configure.connect  # type: ignore[misc]
def setup_models(sender, **kwargs):
    """Load models when the worker starts."""
    global audio_processor_instance, translation_service_instance

    # Initialize Audio Processor
    if audio_processor_instance is None:
        logger.info("Initializing AudioProcessor models for worker...")
        audio_processor_instance = AudioProcessor()
        # Run the sync initialization without models to avoid async issues
        # Models will be lazy-loaded when needed in the task
        logger.info("AudioProcessor instance created (models will be lazy-loaded)")

    # Initialize Translation Service
    settings = get_settings()
    if translation_service_instance is None and settings.translation.enabled:
        logger.info("Initializing TranslationService model for worker...")
        translation_service_instance = TranslationService()
        # Models will be lazy-loaded when needed
        logger.info("TranslationService instance created (models will be lazy-loaded)")
