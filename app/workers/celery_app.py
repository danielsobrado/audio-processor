import asyncio
import logging
from typing import Optional

from celery import Celery

from app.config.settings import get_settings
from app.core.audio_processor import AudioProcessor
from app.services.translation import TranslationService

logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()


def create_celery_app() -> Celery:
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
        # Note: Celery signals are sync, so we need to run the async init
        asyncio.run(audio_processor_instance.initialize_models())
        logger.info("AudioProcessor models initialized successfully")

    # Initialize Translation Service
    settings = get_settings()
    if translation_service_instance is None and settings.translation.enabled:
        logger.info("Initializing TranslationService model for worker...")
        translation_service_instance = TranslationService()
        asyncio.run(translation_service_instance.initialize_model())
        logger.info("TranslationService model initialized successfully")
