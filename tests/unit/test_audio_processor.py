"""
Unit tests for the AudioProcessor class.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.audio_processor import AudioProcessor


@pytest.fixture
def audio_processor():
    """Fixture for AudioProcessor."""
    with patch('app.core.audio_processor.get_settings') as mock_get_settings:
        mock_get_settings.return_value.whisperx.device = "cpu"
        mock_get_settings.return_value.whisperx.compute_type = "int8"
        mock_get_settings.return_value.whisperx.batch_size = 1
        processor = AudioProcessor()
        processor.whisper_model = MagicMock()
        processor.alignment_model = MagicMock()
        processor.alignment_metadata = MagicMock()
        processor.diarization_pipeline = MagicMock()
        return processor


@pytest.mark.asyncio
async def test_process_audio(audio_processor: AudioProcessor):
    """Test the process_audio method."""
    audio_path = Path("tests/fixtures/audio_samples/sample.wav")
    
    # Mock the external calls
    if audio_processor.whisper_model:
        audio_processor.whisper_model.transcribe.return_value = AsyncMock(return_value={"segments": [], "language": "en"})
    if audio_processor.diarization_pipeline:
        audio_processor.diarization_pipeline.return_value = AsyncMock(return_value="diarization_result")
    
    with patch("app.core.audio_processor.whisperx.align", return_value={"segments": []}) as mock_align:
        with patch("app.core.audio_processor.whisperx.assign_word_speakers", return_value={"segments": []}) as mock_assign_speakers:
            result = await audio_processor.process_audio(audio_path)
            
            assert "segments" in result
            assert result["language"] == "en"
            
            audio_processor.whisper_model.transcribe.assert_called_once()
            mock_align.assert_called_once()
            mock_assign_speakers.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_models_success(audio_processor: AudioProcessor):
    """Test successful model initialization."""
    with patch("app.core.audio_processor.whisperx.load_model", return_value=MagicMock()) as mock_load_model:
        with patch("app.core.audio_processor.Pipeline.from_pretrained", return_value=MagicMock()) as mock_from_pretrained:
            await audio_processor.initialize_models()
            mock_load_model.assert_called_once()
            mock_from_pretrained.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_models_failure(audio_processor: AudioProcessor):
    """Test model initialization failure."""
    with patch("app.core.audio_processor.whisperx.load_model", side_effect=Exception("Load error")):
        with pytest.raises(Exception):
            await audio_processor.initialize_models()
