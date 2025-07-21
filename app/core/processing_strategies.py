# File: app/core/processing_strategies.py

import logging
from abc import ABC, abstractmethod
from typing import Any

from app.core.deepgram_formatter import DeepgramFormatter

logger = logging.getLogger(__name__)


def get_audio_processor_instance():
    """Lazy import to avoid circular dependencies."""
    from app.workers.celery_app import audio_processor_instance

    return audio_processor_instance


def get_translation_service_instance():
    """Lazy import to avoid circular dependencies."""
    from app.workers.celery_app import translation_service_instance

    return translation_service_instance


class ProcessingContext:
    """
    A context object to hold and pass data between processing strategies.
    """

    def __init__(self, request_data: dict[str, Any], audio_path: Any):
        self.request_data = request_data
        self.request_id: str = request_data["request_id"]
        self.audio_path: Any = audio_path
        self.processing_result: dict[str, Any] | None = None
        self.deepgram_result: dict[str, Any] | None = None
        self.error: Exception | None = None

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
        audio_processor = get_audio_processor_instance()
        if audio_processor is None:
            raise RuntimeError("AudioProcessor not initialized.")

        try:
            # Ensure models are initialized if needed
            if audio_processor.whisper_model is None:
                logger.info("Initializing AudioProcessor models...")
                await audio_processor.initialize_models()

            context.processing_result = await audio_processor.process_audio(
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
            transcript = context.deepgram_result["results"]["channels"][0]["alternatives"][0][
                "transcript"
            ]
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
            translation_service = get_translation_service_instance()
            if not translation_service:
                logger.warning("Translation service not available. Skipping.")
                return context

            # Ensure models are initialized if needed
            if not hasattr(translation_service, "model") or translation_service.model_name is None:
                logger.info("Initializing TranslationService models...")
                await translation_service.initialize_model()

            transcript = context.deepgram_result["results"]["channels"][0]["alternatives"][0][
                "transcript"
            ]
            target_lang = context.request_data.get("target_language")
            source_lang = context.request_data.get("language", "en")

            if target_lang:
                translated_text = await translation_service.translate_text(
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
                "audio_file_id": context.request_data.get("audio_file_id", context.request_id),
                "language": context.request_data.get("language", "auto"),
                "segments": context.processing_result.get("segments", []),
            }
            graph_result = await graph_processor.process_transcription_result(graph_data)

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


class SentimentAnalysisStrategy(ProcessingStrategy):
    """
    Strategy for analyzing sentiment of transcription segments using LLM.
    """

    async def process(self, context: ProcessingContext) -> ProcessingContext:
        """Process sentiment analysis on transcription result."""
        if context.is_failed():
            return context

        try:
            from app.core.graph_processor import graph_processor

            logger.info(f"🎭 Running sentiment analysis for request {context.request_id}")

            if not context.processing_result or not context.processing_result.get("segments"):
                context.error = Exception(
                    "No transcription segments available for sentiment analysis"
                )
                return context

            # Check if sentiment analysis is enabled
            settings = graph_processor.settings
            if not settings.graph.sentiment_analysis_enabled:
                logger.info("Sentiment analysis is disabled, skipping")
                return context

            # Run sentiment analysis on each segment
            segments = context.processing_result["segments"]
            analyzed_segments = []

            for segment in segments:
                text = segment.get("text", "").strip()
                if text:
                    try:
                        if graph_processor.llm_sentiment_analyzer:
                            sentiment_data = (
                                await graph_processor.llm_sentiment_analyzer.analyze_sentiment(text)
                            )
                            segment["sentiment"] = sentiment_data
                            logger.debug(
                                f"Sentiment for '{text[:30]}...': {sentiment_data.get('sentiment', 'unknown')}"
                            )
                    except Exception as e:
                        logger.warning(f"Sentiment analysis failed for segment: {e}")
                        segment["sentiment"] = {
                            "sentiment": "neutral",
                            "confidence": 0.5,
                            "emotions": [],
                            "intensity": 0.5,
                        }

                analyzed_segments.append(segment)

            # Update processing result with sentiment data
            context.processing_result["segments"] = analyzed_segments
            logger.info(f"✅ Sentiment analysis completed for {len(analyzed_segments)} segments")

        except Exception as e:
            logger.error(f"❌ Sentiment analysis strategy failed: {e}")
            context.error = e

        return context


class KeywordSpottingStrategy(ProcessingStrategy):
    """
    Strategy for spotting specific keywords and entities in transcription using LLM.
    """

    async def process(self, context: ProcessingContext) -> ProcessingContext:
        """Process keyword spotting on transcription result."""
        if context.is_failed():
            return context

        try:
            from app.core.graph_processor import graph_processor

            logger.info(f"🔍 Running keyword spotting for request {context.request_id}")

            if not context.processing_result or not context.processing_result.get("segments"):
                context.error = Exception(
                    "No transcription segments available for keyword spotting"
                )
                return context

            # Run entity extraction on each segment
            segments = context.processing_result["segments"]
            enhanced_segments = []

            for segment in segments:
                text = segment.get("text", "").strip()
                if text:
                    try:
                        # Extract entities
                        entities = await graph_processor._extract_entities(text)
                        segment["entities"] = [
                            {
                                "text": entity_text,
                                "type": entity_type,
                                "confidence": confidence,
                            }
                            for entity_text, entity_type, confidence in entities
                        ]

                        # Extract topics
                        topics = await graph_processor._extract_topics(text)
                        segment["topics"] = [
                            {"name": topic_name, "confidence": confidence}
                            for topic_name, confidence in topics
                        ]

                        logger.debug(
                            f"Found {len(entities)} entities and {len(topics)} topics in segment"
                        )

                    except Exception as e:
                        logger.warning(f"Keyword spotting failed for segment: {e}")
                        segment["entities"] = []
                        segment["topics"] = []

                enhanced_segments.append(segment)

            # Update processing result with keyword data
            context.processing_result["segments"] = enhanced_segments
            logger.info(f"✅ Keyword spotting completed for {len(enhanced_segments)} segments")

        except Exception as e:
            logger.error(f"❌ Keyword spotting strategy failed: {e}")
            context.error = e

        return context
