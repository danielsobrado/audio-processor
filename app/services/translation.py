"""
Translation service for converting text to other languages.
This implementation uses Hugging Face's transformers library.
"""

import logging

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translating text using a pre-trained model."""

    def __init__(self):
        self.pipeline = None
        self.settings = get_settings()
        if self.settings.translation.enabled:
            self.model_name = self.settings.translation.model_name
            # Only check for CUDA if torch is available
            if (
                TORCH_AVAILABLE
                and torch is not None
                and self.settings.translation.device == "cuda"
                and torch.cuda.is_available()
            ):
                self.device = 0
            else:
                self.device = -1
            logger.info(
                f"TranslationService initialized with model '{self.model_name}' on device '{
                    self.settings.translation.device
                }'"
            )
        else:
            logger.info("TranslationService is disabled by configuration.")

    async def initialize_model(self) -> None:
        """
        Loads the translation model into memory.
        This should be called once on worker startup to avoid loading the model
        for every request.
        """
        if not self.settings.translation.enabled or self.pipeline is not None:
            return

        if not TORCH_AVAILABLE:
            logger.error(
                "torch is not available. Translation functionality requires torch and transformers."
            )
            return

        try:
            from transformers.pipelines import pipeline

            logger.info(f"Loading translation model: {self.model_name}...")
            self.pipeline = pipeline("translation", model=self.model_name, device=self.device)
            logger.info("Translation model loaded successfully.")
        except ImportError:
            logger.error(
                "`transformers` and `torch` are required for translation. Please install them."
            )
            self.pipeline = None
        except Exception as e:
            logger.error(
                f"Failed to load translation model '{self.model_name}': {e}",
                exc_info=True,
            )
            self.pipeline = None

    async def translate_text(
        self, text: str, target_language: str, source_language: str | None = None
    ) -> str:
        """
        Translate text to a target language.

        Args:
            text: The text to translate.
            target_language: The target language code (e.g., 'es').
            source_language: The source language code (e.g., 'en'). This is often
                             inferred by the model.

        Returns:
            The translated text, or the original text if translation fails.
        """
        if not self.pipeline:
            logger.warning("Translation pipeline not available. Returning original text.")
            return text

        try:
            # The pipeline call expects a list of texts or a single string
            # Many Helsinki-NLP models handle the language pair automatically
            results = self.pipeline(text, max_length=self.settings.translation.max_length)

            if isinstance(results, list) and len(results) > 0:
                result = results[0]
                if isinstance(result, dict) and "translation_text" in result:
                    translated_text = str(result["translation_text"])
                    logger.debug(
                        f"Translated text to '{target_language}': {translated_text[:100]}..."
                    )
                    return translated_text
            elif isinstance(results, dict) and "translation_text" in results:
                translated_text = str(results.get("translation_text", ""))
                logger.debug(f"Translated text to '{target_language}': {translated_text[:100]}...")
                return translated_text

            logger.error("Translation failed: Unexpected result format from pipeline.")
            return text

        except Exception as e:
            logger.error(f"Translation to '{target_language}' failed: {e}", exc_info=True)
            return text  # Return original text on failure to avoid breaking the entire job
