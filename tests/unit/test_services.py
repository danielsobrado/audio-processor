"""
Unit tests for the application services.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.job_queue import JobQueue
from app.services.transcription import TranscriptionService
from app.services.diarization import DiarizationService
from app.services.translation import TranslationService
from app.services.summarization import SummarizationService
from app.services.cache import CacheService
from app.models.requests import TranscriptionRequest


@pytest.fixture
def mock_job_queue():
    """Mock JobQueue instance."""
    return AsyncMock(spec=JobQueue)


@pytest.fixture
def mock_audio_processor():
    """Mock AudioProcessor instance."""
    return AsyncMock()


@pytest.mark.asyncio
async def test_transcription_service_submit_job(mock_job_queue):
    """Test TranscriptionService.submit_transcription_job."""
    service = TranscriptionService(job_queue=mock_job_queue)
    request = TranscriptionRequest(
        request_id="test-request-123",
        user_id="test-user-456",
        audio_url="http://example.com/audio.mp3",
    )
    
    # Mock celery task
    with (
        # Patch the actual process_audio_async for testing
        patch("app.services.transcription.process_audio_async") as mock_celery_task,
        # Patch the delay method of the mocked celery task
        patch.object(mock_celery_task, "delay", return_value=MagicMock(id="celery-task-id"))
    ):
        result_id = await service.submit_transcription_job(request)
        
        mock_job_queue.create_job.assert_called_once()
        mock_celery_task.delay.assert_called_once()
        mock_job_queue.update_job.assert_called_once()
        assert result_id == request.request_id


@pytest.mark.asyncio
async def test_diarization_service_diarize_audio(mock_audio_processor):
    """Test DiarizationService.diarize_audio."""
    service = DiarizationService(audio_processor=mock_audio_processor)
    audio_path = Path("path/to/audio.wav")
    
    mock_audio_processor.process_audio.return_value = {"segments": [{"speaker": "SPEAKER_00", "text": "hello"}]}
    
    segments = await service.diarize_audio(audio_path)
    
    mock_audio_processor.process_audio.assert_called_once_with(
        audio_path=audio_path,
        diarize=True,
        align=False,
    )
    assert len(segments) == 1
    assert segments[0]["speaker"] == "SPEAKER_00"


@pytest.mark.asyncio
async def test_translation_service_translate_text():
    """Test TranslationService.translate_text."""
    service = TranslationService()
    text = "Hello"
    target_language = "es"
    
    translated_text = await service.translate_text(text, target_language)
    assert translated_text == f"Translated to {target_language}: {text}"


@pytest.mark.asyncio
async def test_summarization_service_summarize_text():
    """Test SummarizationService.summarize_text."""
    # Mock settings for summarization service
    with patch('app.services.summarization.get_settings') as mock_get_settings:
        mock_get_settings.return_value.summarization.api_url = "http://mock-api.com/summarize"
        mock_get_settings.return_value.summarization.api_key = "mock-key"
        mock_get_settings.return_value.summarization.model = "mock-model"
        
        service = SummarizationService()
        text = "This is a long text that needs to be summarized."
        expected_summary = "This is a summary."
        
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "choices": [{"message": {"content": expected_summary}}]
            }
            mock_post.return_value.__aenter__.return_value = mock_response
            
            summary = await service.summarize_text(text)
            
            mock_post.assert_called_once()
            assert summary == expected_summary


@pytest.mark.asyncio
async def test_cache_service_set_get_delete():
    """Test CacheService set, get, and delete operations."""
    with patch('app.services.cache.redis.from_url') as mock_from_url:
        mock_redis_client = AsyncMock()
        mock_from_url.return_value = mock_redis_client
        
        service = CacheService()
        key = "test_key"
        value = "test_value"
        
        await service.set(key, value)
        mock_redis_client.set.assert_called_once_with(key, value, ex=3600)
        
        mock_redis_client.get.return_value = value
        retrieved_value = await service.get(key)
        mock_redis_client.get.assert_called_once_with(key)
        assert retrieved_value == value
        
        await service.delete(key)
        mock_redis_client.delete.assert_called_once_with(key)
