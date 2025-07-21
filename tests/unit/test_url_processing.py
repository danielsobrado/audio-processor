"""
Tests for URL processing functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
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
        mock_job_queue.create_job = AsyncMock(
            return_value=MagicMock(request_id="test-123")
        )
        mock_job_queue.update_job = AsyncMock()

        # Mock validate_transcription_params
        with patch("app.api.v1.endpoints.transcribe.validate_transcription_params"):
            # Mock process_audio_async task
            with patch(
                "app.api.v1.endpoints.transcribe.process_audio_async"
            ) as mock_task:
                mock_task.delay.return_value = MagicMock(id="task-123")

                # Mock uuid generation
                with patch("app.api.v1.endpoints.transcribe.uuid") as mock_uuid:
                    mock_uuid.uuid4.return_value = MagicMock()
                    mock_uuid.uuid4.return_value.__str__ = MagicMock(
                        return_value="test-request-id"
                    )

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

    @pytest.mark.asyncio
    async def test_callback_url_integration_with_transcribe_endpoint(self):
        """Test that callback_url parameter is properly passed through to worker."""

        # Import here to avoid circular import issues in tests
        from app.api.v1.endpoints.transcribe import transcribe_audio
        from app.config.settings import Settings

        # Mock settings with URL processing enabled
        mock_settings = MagicMock(spec=Settings)
        mock_settings.enable_url_processing = True

        # Mock other dependencies
        mock_user_id = "test-user-callback"
        mock_transcription_service = MagicMock()
        mock_job_queue = AsyncMock()
        mock_job_queue.create_job.return_value = MagicMock()
        mock_job_queue.update_job.return_value = None

        callback_url = "https://webhook.example.com/transcription"
        audio_url = "https://example.com/audio.wav"

        # Mock file validation and task processing
        with patch("app.api.v1.endpoints.transcribe.validate_transcription_params"):
            # Mock the Celery task
            with patch(
                "app.api.v1.endpoints.transcribe.process_audio_async"
            ) as mock_task:
                mock_celery_result = MagicMock()
                mock_celery_result.id = "celery-task-123"
                mock_task.delay.return_value = mock_celery_result

                # Mock UUID generation
                with patch("app.api.v1.endpoints.transcribe.uuid") as mock_uuid:
                    mock_uuid.uuid4.return_value.hex = "test-request-id"
                    test_request_id = str(mock_uuid.uuid4.return_value)

                    # Execute the endpoint
                    result = await transcribe_audio(
                        file=None,
                        audio_url=audio_url,
                        callback_url=callback_url,
                        language="auto",
                        model="large-v2",
                        punctuate=True,
                        diarize=True,
                        smart_format=True,
                        utterances=True,
                        utt_split=0.8,
                        translate=False,
                        summarize=False,
                        user_id=mock_user_id,
                        transcription_service=mock_transcription_service,
                        job_queue=mock_job_queue,
                        settings=mock_settings,
                    )

                    # Verify the task was called with callback_url
                    mock_task.delay.assert_called_once()
                    call_args = mock_task.delay.call_args

                    # Check that callback_url is in the request_data
                    request_data = call_args[1]["request_data"]
                    assert "callback_url" in request_data
                    assert request_data["callback_url"] == callback_url

                    # Verify other expected fields
                    assert request_data["audio_url"] == audio_url
                    assert request_data["request_id"] == test_request_id

                    # Verify response
                    assert result.request_id == test_request_id
                    assert result.status == "queued"

    @pytest.mark.asyncio
    async def test_callback_url_optional_parameter(self):
        """Test that callback_url is optional and doesn't break functionality when not provided."""

        # Import here to avoid circular import issues in tests
        from app.api.v1.endpoints.transcribe import transcribe_audio
        from app.config.settings import Settings

        # Mock settings
        mock_settings = MagicMock(spec=Settings)
        mock_settings.enable_url_processing = True

        # Mock other dependencies
        mock_user_id = "test-user-no-callback"
        mock_transcription_service = MagicMock()
        mock_job_queue = AsyncMock()
        mock_job_queue.create_job.return_value = MagicMock()
        mock_job_queue.update_job.return_value = None

        audio_url = "https://example.com/audio.wav"

        # Mock file validation and task processing
        with patch("app.api.v1.endpoints.transcribe.validate_transcription_params"):
            with patch(
                "app.api.v1.endpoints.transcribe.process_audio_async"
            ) as mock_task:
                mock_celery_result = MagicMock()
                mock_celery_result.id = "celery-task-456"
                mock_task.delay.return_value = mock_celery_result

                with patch("app.api.v1.endpoints.transcribe.uuid") as mock_uuid:
                    mock_uuid.uuid4.return_value.hex = "test-request-id-2"
                    test_request_id = str(mock_uuid.uuid4.return_value)

                    # Execute the endpoint WITHOUT callback_url
                    result = await transcribe_audio(
                        file=None,
                        audio_url=audio_url,
                        callback_url=None,  # No callback URL provided
                        language="auto",
                        model="large-v2",
                        punctuate=True,
                        diarize=True,
                        smart_format=True,
                        utterances=True,
                        utt_split=0.8,
                        translate=False,
                        summarize=False,
                        user_id=mock_user_id,
                        transcription_service=mock_transcription_service,
                        job_queue=mock_job_queue,
                        settings=mock_settings,
                    )

                    # Verify the task was called
                    mock_task.delay.assert_called_once()
                    call_args = mock_task.delay.call_args

                    # Check that callback_url is None in the request_data
                    request_data = call_args[1]["request_data"]
                    assert request_data.get("callback_url") is None

                    # Verify response still works
                    assert result.request_id == test_request_id
                    assert result.status == "queued"


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

        with open(tasks_file, encoding="utf-8") as f:
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
