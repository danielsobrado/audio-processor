# File: app/core/processing_strategies.py

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from app.core.deepgram_formatter import DeepgramFormatter
from app.schemas.database import JobStatus
from app.workers.celery_app import (
    audio_processor_instance,
    translation_service_instance,
)

logger = logging.getLogger(__name__)


class ProcessingContext:
    """
    A context object to hold and pass data between processing strategies.
    """

    def __init__(self, request_data: Dict[str, Any], audio_path: Any):
        self.request_data = request_data
        self.request_id: str = request_data["request_id"]
        self.audio_path: Any = audio_path
        self.processing_result: Optional[Dict[str, Any]] = None
        self.deepgram_result: Optional[Dict[str, Any]] = None
        self.error: Optional[Exception] = None

    def is_failed(self) -> bool:
        """Check if the context has an error."""
        return self.error is not None


class ProcessingStrategy(ABC):
    """
    Abstract base class for a step in the audio processing pipeline.
    """

    @abstractmethod
    async def process(self, context: ProcessingContext) -> ProcessingContext:
        """
        Process the audio data according to the specific strategy.

        Args:
            context: The shared context containing all processing data.

        Returns:
            The updated context.
        """
        pass


class TranscriptionStrategy(ProcessingStrategy):
    """Strategy for transcribing audio using WhisperX."""

    async def process(self, context: ProcessingContext) -> ProcessingContext:
        logger.info(f"Executing TranscriptionStrategy for job {context.request_id}")
        if audio_processor_instance is None:
            raise RuntimeError("AudioProcessor not initialized.")

        try:
            context.processing_result = await audio_processor_instance.process_audio(
                audio_path=context.audio_path,
                language=context.request_data.get("language", "auto"),
                diarize=context.request_data.get("diarize", True),
            )
        except Exception as e:
            logger.error(f"Transcription failed for job {context.request_id}: {e}")
            context.error = e
        return context


class FormattingStrategy(ProcessingStrategy):
    """Strategy for formatting the transcription result into Deepgram format."""

    async def process(self, context: ProcessingContext) -> ProcessingContext:
        if context.is_failed() or not context.processing_result:
            return context

        logger.info(f"Executing FormattingStrategy for job {context.request_id}")
        try:
            formatter = DeepgramFormatter()
            context.deepgram_result = formatter.format_transcription_result(
                whisperx_result=context.processing_result,
                request_id=context.request_id,
                model_name=context.request_data.get("model", "large-v2"),
                audio_duration=context.processing_result.get("duration"),
                punctuate=context.request_data.get("punctuate", True),
                diarize=context.request_data.get("diarize", True),
                smart_format=context.request_data.get("smart_format", True),
                utterances=context.request_data.get("utterances", True),
            )
        except Exception as e:
            logger.error(f"Formatting failed for job {context.request_id}: {e}")
            context.error = e
        return context


class SummarizationStrategy(ProcessingStrategy):
    """Strategy for summarizing the transcript."""

    async def process(self, context: ProcessingContext) -> ProcessingContext:
        if context.is_failed() or not context.deepgram_result:
            return context

        logger.info(f"Executing SummarizationStrategy for job {context.request_id}")
        try:
            from app.services.summarization import SummarizationService

            summarization_service = SummarizationService()
            transcript = context.deepgram_result["results"]["channels"][0][
                "alternatives"
            ][0]["transcript"]
            summary = await summarization_service.summarize_text(transcript)

            formatter = DeepgramFormatter()
            formatter.add_summary_data(context.deepgram_result, summary)
        except Exception as e:
            logger.error(f"Summarization failed for job {context.request_id}: {e}")
            context.error = e
        return context


class TranslationStrategy(ProcessingStrategy):
    """Strategy for translating the transcript."""

    async def process(self, context: ProcessingContext) -> ProcessingContext:
        if context.is_failed() or not context.deepgram_result:
            return context

        logger.info(f"Executing TranslationStrategy for job {context.request_id}")
        try:
            if not translation_service_instance:
                logger.warning("Translation service not available. Skipping.")
                return context

            transcript = context.deepgram_result["results"]["channels"][0][
                "alternatives"
            ][0]["transcript"]
            target_lang = context.request_data.get("target_language")
            source_lang = context.request_data.get("language", "en")

            if target_lang:
                translated_text = await translation_service_instance.translate_text(
                    text=transcript,
                    target_language=target_lang,
                    source_language=source_lang,
                )
                translations = {target_lang: translated_text}
                formatter = DeepgramFormatter()
                formatter.add_translation_data(context.deepgram_result, translations)
            else:
                logger.warning("Translation requested but no target language specified.")
        except Exception as e:
            logger.error(f"Translation failed for job {context.request_id}: {e}")
            context.error = e
        return context


class GraphProcessingStrategy(ProcessingStrategy):
    """Strategy for populating the knowledge graph."""

    async def process(self, context: ProcessingContext) -> ProcessingContext:
        if context.is_failed() or not context.processing_result:
            return context

        logger.info(f"Executing GraphProcessingStrategy for job {context.request_id}")
        try:
            from app.core.graph_processor import graph_processor

            graph_data = {
                "job_id": context.request_id,
                "audio_file_id": context.request_data.get(
                    "audio_file_id", context.request_id
                ),
                "language": context.request_data.get("language", "auto"),
                "segments": context.processing_result.get("segments", []),
            }
            graph_result = await graph_processor.process_transcription_result(
                graph_data
            )

            if context.deepgram_result:
                if "metadata" not in context.deepgram_result:
                    context.deepgram_result["metadata"] = {}
                context.deepgram_result["metadata"]["graph_processing"] = graph_result
        except Exception as e:
            # Don't fail the whole job, just log the warning
            logger.warning(f"Graph processing failed for job {context.request_id}: {e}")
            if context.deepgram_result:
                if "metadata" not in context.deepgram_result:
                    context.deepgram_result["metadata"] = {}
                context.deepgram_result["metadata"]["graph_processing"] = {
                    "success": False,
                    "error": str(e),
                }
        return context
