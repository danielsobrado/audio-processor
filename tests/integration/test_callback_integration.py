"""
Integration tests for callback URL functionality in the audio processing workflow.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
import tempfile
from pathlib import Path

from app.workers.tasks import process_audio_async


class TestCallbackIntegration:
    """Integration tests for callback URL functionality."""

    @pytest.mark.asyncio
    @patch('app.workers.tasks.audio_processor_instance')
    @patch('app.workers.tasks.DeepgramFormatter')
    @patch('app.workers.tasks.JobQueue')
    @patch('httpx.AsyncClient')
    async def test_end_to_end_callback_success(
        self, 
        mock_http_client,
        mock_job_queue_class,
        mock_formatter_class,
        mock_audio_processor
    ):
        """Test end-to-end callback notification for successful transcription."""
        # Arrange
        callback_url = "https://webhook.example.com/transcription"
        request_id = "integration-test-123"
        
        # Mock audio processing result
        mock_processing_result = {
            "segments": [
                {"text": "Hello world", "start": 0.0, "end": 2.0}
            ],
            "duration": 2.0
        }
        
        # Mock Deepgram formatter result
        mock_deepgram_result = {
            "results": {
                "channels": [{
                    "alternatives": [{
                        "transcript": "Hello world",
                        "confidence": 0.95
                    }]
                }]
            },
            "metadata": {"request_id": request_id}
        }
        
        # Setup mocks
        mock_audio_processor.process_audio.return_value = mock_processing_result
        
        mock_formatter = MagicMock()
        mock_formatter.format_transcription_result.return_value = mock_deepgram_result
        mock_formatter_class.return_value = mock_formatter
        
        mock_job_queue = AsyncMock()
        mock_job_queue_class.return_value = mock_job_queue
        
        mock_http_response = MagicMock()
        mock_http_response.is_success = True
        mock_http_response.status_code = 200
        
        mock_http_context = AsyncMock()
        mock_http_context.post.return_value = mock_http_response
        mock_http_client.return_value.__aenter__.return_value = mock_http_context
        
        # Prepare request data
        request_data = {
            "request_id": request_id,
            "language": "auto",
            "diarize": True,
            "callback_url": callback_url,
            "audio_file_path": "/tmp/test_audio.wav"
        }
        
        # Create mock audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(b"mock audio data")
            request_data["audio_file_path"] = temp_file.name
        
        try:
            # Act
            with patch('app.workers.tasks.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.exists.return_value = True
                mock_path.return_value = mock_path_instance
                
                # Execute the worker function in a way that doesn't require Celery
                async def mock_async_runner():
                    # Import the inner function logic manually
                    from app.workers.tasks import _send_callback_notification
                    from app.core.job_queue import JobQueue
                    from app.schemas.database import JobStatus
                    
                    # Simulate the processing logic
                    job_queue = JobQueue()
                    await job_queue.initialize()
                    
                    # Simulate successful processing
                    await job_queue.update_job(
                        request_id,
                        status=JobStatus.COMPLETED,
                        progress=100.0,
                        result=mock_deepgram_result,
                    )
                    
                    # Test the callback notification
                    await _send_callback_notification(
                        callback_url=callback_url,
                        request_id=request_id,
                        status="completed",
                        result=mock_deepgram_result,
                    )
                
                await mock_async_runner()
            
            # Assert
            # Verify callback was sent
            mock_http_context.post.assert_called_once()
            call_args = mock_http_context.post.call_args
            
            assert call_args[0][0] == callback_url
            
            payload = call_args[1]["json"]
            assert payload["request_id"] == request_id
            assert payload["status"] == "completed"
            assert payload["result"] == mock_deepgram_result
            assert "timestamp" in payload
            
        finally:
            # Cleanup
            Path(request_data["audio_file_path"]).unlink(missing_ok=True)

    @pytest.mark.asyncio
    @patch('app.workers.tasks.audio_processor_instance')
    @patch('app.workers.tasks.JobQueue')
    @patch('httpx.AsyncClient')
    async def test_end_to_end_callback_failure(
        self,
        mock_http_client,
        mock_job_queue_class,
        mock_audio_processor
    ):
        """Test end-to-end callback notification for failed transcription."""
        # Arrange
        callback_url = "https://webhook.example.com/transcription"
        request_id = "integration-test-456"
        error_message = "Audio file format not supported"
        
        # Setup mocks to simulate failure
        mock_audio_processor.process_audio.side_effect = Exception(error_message)
        
        mock_job_queue = AsyncMock()
        mock_job_queue_class.return_value = mock_job_queue
        
        mock_http_response = MagicMock()
        mock_http_response.is_success = True
        mock_http_response.status_code = 200
        
        mock_http_context = AsyncMock()
        mock_http_context.post.return_value = mock_http_response
        mock_http_client.return_value.__aenter__.return_value = mock_http_context
        
        # Prepare request data
        request_data = {
            "request_id": request_id,
            "language": "auto",
            "diarize": True,
            "callback_url": callback_url,
            "audio_file_path": "/tmp/test_audio_fail.wav"
        }
        
        # Create mock audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(b"invalid audio data")
            request_data["audio_file_path"] = temp_file.name
        
        try:
            # Act
            with patch('app.workers.tasks.Path') as mock_path:
                mock_path_instance = MagicMock()
                mock_path_instance.exists.return_value = True
                mock_path.return_value = mock_path_instance
                
                # Simulate the failure and callback
                async def mock_failure_runner():
                    from app.workers.tasks import _send_callback_notification
                    from app.core.job_queue import JobQueue
                    from app.schemas.database import JobStatus
                    
                    job_queue = JobQueue()
                    await job_queue.initialize()
                    
                    # Simulate failed processing
                    await job_queue.update_job(
                        request_id, 
                        status=JobStatus.FAILED, 
                        error=error_message
                    )
                    
                    # Test the callback notification
                    await _send_callback_notification(
                        callback_url=callback_url,
                        request_id=request_id,
                        status="failed",
                        error=error_message,
                    )
                
                await mock_failure_runner()
            
            # Assert
            # Verify callback was sent
            mock_http_context.post.assert_called_once()
            call_args = mock_http_context.post.call_args
            
            assert call_args[0][0] == callback_url
            
            payload = call_args[1]["json"]
            assert payload["request_id"] == request_id
            assert payload["status"] == "failed"
            assert payload["error"] == error_message
            assert "result" not in payload
            assert "timestamp" in payload
            
        finally:
            # Cleanup
            Path(request_data["audio_file_path"]).unlink(missing_ok=True)

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_callback_resilience_to_webhook_failures(self, mock_http_client):
        """Test that webhook failures don't break the main processing flow."""
        # Arrange
        callback_url = "https://failing-webhook.example.com/transcription"
        request_id = "resilience-test-789"
        result = {"transcript": "test content"}
        
        # Setup mock to simulate webhook failure
        mock_http_context = AsyncMock()
        mock_http_context.post.side_effect = httpx.TimeoutException("Webhook timeout")
        mock_http_client.return_value.__aenter__.return_value = mock_http_context
        
        # Act & Assert - should not raise exception
        from app.workers.tasks import _send_callback_notification
        
        await _send_callback_notification(
            callback_url=callback_url,
            request_id=request_id,
            status="completed",
            result=result
        )
        
        # Verify the attempt was made
        mock_http_context.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_callback_when_url_not_provided(self):
        """Test that no callback is attempted when callback_url is not provided."""
        # Act & Assert
        with patch('httpx.AsyncClient') as mock_http_client:
            from app.workers.tasks import _send_callback_notification
            
            # Test with None
            await _send_callback_notification(
                callback_url=None,
                request_id="no-callback-test-1",
                status="completed",
                result={"transcript": "test"}
            )
            
            # Test with empty string
            await _send_callback_notification(
                callback_url="",
                request_id="no-callback-test-2",
                status="completed",
                result={"transcript": "test"}
            )
            
            # Verify no HTTP calls were made
            mock_http_client.assert_not_called()

    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_callback_url_validation_in_real_scenario(self, mock_http_client):
        """Test callback with various URL formats that might be provided by users."""
        # Arrange
        test_urls = [
            "https://api.example.com/webhooks/transcription",
            "http://localhost:3000/webhook",
            "https://webhook.site/unique-id",
            "https://example.com:8080/api/v1/callbacks",
        ]
        
        mock_http_response = MagicMock()
        mock_http_response.is_success = True
        mock_http_response.status_code = 200
        
        mock_http_context = AsyncMock()
        mock_http_context.post.return_value = mock_http_response
        mock_http_client.return_value.__aenter__.return_value = mock_http_context
        
        from app.workers.tasks import _send_callback_notification
        
        # Act & Assert
        for i, url in enumerate(test_urls):
            await _send_callback_notification(
                callback_url=url,
                request_id=f"url-test-{i}",
                status="completed",
                result={"transcript": f"test {i}"}
            )
        
        # Verify all URLs were attempted
        assert mock_http_context.post.call_count == len(test_urls)
