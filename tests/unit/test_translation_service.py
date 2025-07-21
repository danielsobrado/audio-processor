"""
Unit tests for the translation service.
"""

from unittest.mock import Mock, patch

import pytest

from app.services.translation import TranslationService


class TestTranslationService:
    """Test cases for TranslationService."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = Mock()
        settings.translation.enabled = True
        settings.translation.model_name = "Helsinki-NLP/opus-mt-en-es"
        settings.translation.device = "cpu"
        return settings

    @pytest.fixture
    def mock_disabled_settings(self):
        """Mock settings with translation disabled."""
        settings = Mock()
        settings.translation.enabled = False
        return settings

    @patch("app.services.translation.get_settings")
    def test_init_enabled(self, mock_get_settings, mock_settings):
        """Test TranslationService initialization when enabled."""
        mock_get_settings.return_value = mock_settings

        service = TranslationService()

        assert service.pipeline is None
        assert service.model_name == "Helsinki-NLP/opus-mt-en-es"
        assert service.device == -1  # CPU device

    @patch("app.services.translation.get_settings")
    def test_init_disabled(self, mock_get_settings, mock_disabled_settings):
        """Test TranslationService initialization when disabled."""
        mock_get_settings.return_value = mock_disabled_settings

        service = TranslationService()

        assert service.pipeline is None

    @patch("app.services.translation.get_settings")
    @patch("app.services.translation.torch")
    @pytest.mark.asyncio
    async def test_initialize_model_success(
        self, mock_torch, mock_get_settings, mock_settings
    ):
        """Test successful model initialization."""
        mock_get_settings.return_value = mock_settings
        mock_torch.cuda.is_available.return_value = False

        # Mock the transformers pipeline import more directly
        mock_pipeline_instance = Mock()

        with patch(
            "transformers.pipelines.pipeline", return_value=mock_pipeline_instance
        ) as mock_pipeline:
            service = TranslationService()
            await service.initialize_model()

            assert service.pipeline == mock_pipeline_instance
            mock_pipeline.assert_called_once_with(
                "translation", model="Helsinki-NLP/opus-mt-en-es", device=-1
            )

    @patch("app.services.translation.get_settings")
    @pytest.mark.asyncio
    async def test_initialize_model_disabled(
        self, mock_get_settings, mock_disabled_settings
    ):
        """Test model initialization when translation is disabled."""
        mock_get_settings.return_value = mock_disabled_settings

        service = TranslationService()
        await service.initialize_model()

        assert service.pipeline is None

    @patch("app.services.translation.get_settings")
    @pytest.mark.asyncio
    async def test_initialize_model_import_error(
        self, mock_get_settings, mock_settings
    ):
        """Test model initialization with import error."""
        mock_get_settings.return_value = mock_settings

        with patch(
            "transformers.pipelines.pipeline",
            side_effect=ImportError("transformers not found"),
        ):
            service = TranslationService()
            await service.initialize_model()

            assert service.pipeline is None

    @patch("app.services.translation.get_settings")
    @pytest.mark.asyncio
    async def test_translate_text_no_pipeline(self, mock_get_settings, mock_settings):
        """Test translation when pipeline is not available."""
        mock_get_settings.return_value = mock_settings

        service = TranslationService()
        # Don't initialize the pipeline

        result = await service.translate_text("Hello", "es")

        assert result == "Hello"  # Should return original text

    @patch("app.services.translation.get_settings")
    @pytest.mark.asyncio
    async def test_translate_text_success_list_format(
        self, mock_get_settings, mock_settings
    ):
        """Test successful translation with list format response."""
        mock_get_settings.return_value = mock_settings

        # Mock pipeline response
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"translation_text": "Hola"}]

        service = TranslationService()
        service.pipeline = mock_pipeline

        result = await service.translate_text("Hello", "es")

        assert result == "Hola"
        mock_pipeline.assert_called_once_with("Hello", max_length=512)

    @patch("app.services.translation.get_settings")
    @pytest.mark.asyncio
    async def test_translate_text_success_dict_format(
        self, mock_get_settings, mock_settings
    ):
        """Test successful translation with dict format response."""
        mock_get_settings.return_value = mock_settings

        # Mock pipeline response
        mock_pipeline = Mock()
        mock_pipeline.return_value = {"translation_text": "Hola"}

        service = TranslationService()
        service.pipeline = mock_pipeline

        result = await service.translate_text("Hello", "es")

        assert result == "Hola"

    @patch("app.services.translation.get_settings")
    @pytest.mark.asyncio
    async def test_translate_text_invalid_format(
        self, mock_get_settings, mock_settings
    ):
        """Test translation with invalid response format."""
        mock_get_settings.return_value = mock_settings

        # Mock pipeline response with invalid format
        mock_pipeline = Mock()
        mock_pipeline.return_value = {"invalid_key": "some_value"}

        service = TranslationService()
        service.pipeline = mock_pipeline

        result = await service.translate_text("Hello", "es")

        assert result == "Hello"  # Should return original text

    @patch("app.services.translation.get_settings")
    @pytest.mark.asyncio
    async def test_translate_text_exception(self, mock_get_settings, mock_settings):
        """Test translation when pipeline raises an exception."""
        mock_get_settings.return_value = mock_settings

        # Mock pipeline that raises an exception
        mock_pipeline = Mock()
        mock_pipeline.side_effect = Exception("Pipeline error")

        service = TranslationService()
        service.pipeline = mock_pipeline

        result = await service.translate_text("Hello", "es")

        assert result == "Hello"  # Should return original text

    @patch("app.services.translation.get_settings")
    @pytest.mark.asyncio
    async def test_translate_text_with_source_language(
        self, mock_get_settings, mock_settings
    ):
        """Test translation with source language specified."""
        mock_get_settings.return_value = mock_settings

        # Mock pipeline response
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"translation_text": "Hola"}]

        service = TranslationService()
        service.pipeline = mock_pipeline

        result = await service.translate_text("Hello", "es", "en")

        assert result == "Hola"
        mock_pipeline.assert_called_once_with("Hello", max_length=512)

    @patch("app.services.translation.get_settings")
    @pytest.mark.asyncio
    async def test_translate_long_text(self, mock_get_settings, mock_settings):
        """Test translation with longer text."""
        mock_get_settings.return_value = mock_settings

        long_text = "This is a very long text that we want to translate. " * 20

        # Mock pipeline response
        mock_pipeline = Mock()
        mock_pipeline.return_value = [{"translation_text": "Texto traducido muy largo"}]

        service = TranslationService()
        service.pipeline = mock_pipeline

        result = await service.translate_text(long_text, "es")

        assert result == "Texto traducido muy largo"
        mock_pipeline.assert_called_once_with(long_text, max_length=512)


@pytest.mark.asyncio
async def test_translation_service_integration():
    """Integration test for the translation service (requires actual model)."""
    # This test is skipped by default as it requires actual model download
    pytest.skip("Integration test requires actual model download")

    # Uncomment to run actual integration test:
    # import os
    # os.environ["TRANSLATION_ENABLED"] = "true"
    # os.environ["TRANSLATION_MODEL_NAME"] = "Helsinki-NLP/opus-mt-en-es"
    # os.environ["TRANSLATION_DEVICE"] = "cpu"
    #
    # service = TranslationService()
    # await service.initialize_model()
    #
    # if service.pipeline:
    #     result = await service.translate_text("Hello world", "es")
    #     assert result != "Hello world"  # Should be translated
    #     assert len(result) > 0
