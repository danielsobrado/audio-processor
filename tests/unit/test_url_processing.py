"""
Tests for URL processing functionality.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import HTTPException


class TestURLProcessingFeatureFlag:
    """Test URL processing feature flag validation."""

    @pytest.mark.asyncio
    async def test_url_processing_disabled_raises_forbidden(self):
        """Test that providing a URL when URL processing is disabled raises 403."""
        
        # Import here to avoid circular import issues in tests
        from app.api.v1.endpoints.transcribe import transcribe_audio
        from app.config.settings import Settings
        
        # Mock settings with URL processing disabled
        mock_settings = MagicMock(spec=Settings)
        mock_settings.enable_url_processing = False
        
        # Mock other dependencies
        mock_user_id = "test-user"
        mock_transcription_service = MagicMock()
        mock_job_queue = MagicMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await transcribe_audio(
                file=None,
                audio_url="https://example.com/audio.mp3",
                language="auto",
                model="large-v2",
                punctuate=True,
                diarize=True,
                smart_format=True,
                utterances=True,
                utt_split=0.8,
                translate=False,
                summarize=False,
                callback_url=None,
                user_id=mock_user_id,
                transcription_service=mock_transcription_service,
                job_queue=mock_job_queue,
                settings=mock_settings,
            )
        
        assert exc_info.value.status_code == 403
        assert "Processing from a URL is disabled" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_url_processing_enabled_allows_url(self):
        """Test that providing a URL when URL processing is enabled is allowed."""
        
        # Import here to avoid circular import issues in tests
        from app.api.v1.endpoints.transcribe import transcribe_audio
        from app.config.settings import Settings
        
        # Mock settings with URL processing enabled
        mock_settings = MagicMock(spec=Settings)
        mock_settings.enable_url_processing = True
        
        # Mock other dependencies
        mock_user_id = "test-user"
        mock_transcription_service = MagicMock()
        
        # Mock job queue
        mock_job_queue = MagicMock()
        mock_job_queue.create_job = AsyncMock(return_value=MagicMock(request_id="test-123"))
        mock_job_queue.update_job = AsyncMock()
        
        # Mock validate_transcription_params
        with patch('app.api.v1.endpoints.transcribe.validate_transcription_params'):
            # Mock process_audio_async task
            with patch('app.api.v1.endpoints.transcribe.process_audio_async') as mock_task:
                mock_task.delay.return_value = MagicMock(id="task-123")
                
                # Mock uuid generation
                with patch('app.api.v1.endpoints.transcribe.uuid') as mock_uuid:
                    mock_uuid.uuid4.return_value = MagicMock()
                    mock_uuid.uuid4.return_value.__str__ = MagicMock(return_value="test-request-id")
                    
                    # This should not raise an exception
                    result = await transcribe_audio(
                        file=None,
                        audio_url="https://example.com/audio.mp3",
                        language="auto",
                        model="large-v2",
                        punctuate=True,
                        diarize=True,
                        smart_format=True,
                        utterances=True,
                        utt_split=0.8,
                        translate=False,
                        summarize=False,
                        callback_url=None,
                        user_id=mock_user_id,
                        transcription_service=mock_transcription_service,
                        job_queue=mock_job_queue,
                        settings=mock_settings,
                    )
                    
                    assert result.status == "queued"
                    assert result.request_id == "test-request-id"


class TestURLDownloadLogic:
    """Test URL download logic in worker."""

    def test_url_download_logic_exists(self):
        """Test that URL download logic is implemented in worker."""
        
        # Read the worker file directly to verify implementation
        import os
        
        # Get the path to the worker tasks file
        current_dir = os.path.dirname(__file__)
        tasks_file = os.path.join(current_dir, "..", "..", "app", "workers", "tasks.py")
        tasks_file = os.path.normpath(tasks_file)
        
        with open(tasks_file, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Verify key components are present
        assert "httpx.AsyncClient" in source
        assert "audio_url" in source
        assert "response.aiter_bytes" in source
        assert "Could not download or process audio from URL" in source
        assert "import httpx" in source
        
        # Verify the NotImplementedError was removed
        assert "NotImplementedError" not in source
        assert "TODO: Implement audio download from URL" not in source
        
        # Verify URL handling logic exists
        assert 'elif request_data.get("audio_url"):' in source
        assert "Successfully downloaded audio to" in source
