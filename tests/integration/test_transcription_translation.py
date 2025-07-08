"""
Integration tests for the translation feature in the transcription API.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app


class TestTranscriptionAPITranslation:
    """Test translation functionality in the transcription API."""

    def setup_method(self):
        """Setup test client."""
        self.client = TestClient(app)

    @patch('app.api.v1.endpoints.transcribe.get_current_user_id')
    @patch('app.api.v1.endpoints.transcribe.get_settings_dependency')
    @patch('app.api.v1.endpoints.transcribe.get_job_queue')
    @patch('app.api.v1.endpoints.transcribe.get_transcription_service')
    @patch('app.api.v1.endpoints.transcribe.process_audio_async')
    def test_transcribe_with_translation_success(
        self,
        mock_process_audio,
        mock_get_transcription_service,
        mock_get_job_queue,
        mock_get_settings,
        mock_get_user_id
    ):
        """Test successful transcription request with translation."""
        
        # Mock dependencies
        mock_get_user_id.return_value = "test-user-123"
        
        mock_settings = Mock()
        mock_settings.enable_audio_upload = True
        mock_settings.translation.enabled = True
        mock_get_settings.return_value = mock_settings
        
        mock_job_queue = AsyncMock()
        mock_job = Mock()
        mock_job_queue.create_job.return_value = mock_job
        mock_get_job_queue.return_value = mock_job_queue
        
        mock_transcription_service = Mock()
        mock_get_transcription_service.return_value = mock_transcription_service
        
        mock_task = Mock()
        mock_task.id = "task-123"
        mock_process_audio.delay.return_value = mock_task
        
        # Prepare test file
        test_file_content = b"fake audio data"
        
        # Make request with translation parameters
        response = self.client.post(
            "/api/v1/transcribe",
            data={
                "language": "en",
                "model": "large-v2",
                "translate": "true",
                "target_language": "es",
                "diarize": "true",
                "summarize": "false",
            },
            files={"file": ("test.wav", test_file_content, "audio/wav")}
        )
        
        # Verify response
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["status"] == "queued"
        assert "request_id" in response_data
        
        # Verify that translate and target_language were included in the task data
        mock_process_audio.delay.assert_called_once()
        call_args = mock_process_audio.delay.call_args
        task_data = call_args[1]["request_data"]  # kwargs
        
        assert task_data["translate"] is True
        assert task_data["target_language"] == "es"

    @patch('app.api.v1.endpoints.transcribe.get_current_user_id')
    @patch('app.api.v1.endpoints.transcribe.get_settings_dependency')
    def test_transcribe_translation_missing_target_language(
        self,
        mock_get_settings,
        mock_get_user_id
    ):
        """Test translation request without target_language should fail."""
        
        # Mock dependencies
        mock_get_user_id.return_value = "test-user-123"
        
        mock_settings = Mock()
        mock_settings.enable_audio_upload = True
        mock_settings.translation.enabled = True
        mock_get_settings.return_value = mock_settings
        
        # Prepare test file
        test_file_content = b"fake audio data"
        
        # Make request with translation but no target_language
        response = self.client.post(
            "/api/v1/transcribe",
            data={
                "language": "en",
                "model": "large-v2",
                "translate": "true",  # Missing target_language
                "diarize": "true",
            },
            files={"file": ("test.wav", test_file_content, "audio/wav")}
        )
        
        # Verify error response
        assert response.status_code == 400
        assert "target_language" in response.json()["detail"]

    @patch('app.api.v1.endpoints.transcribe.get_current_user_id')
    @patch('app.api.v1.endpoints.transcribe.get_settings_dependency')
    def test_transcribe_translation_disabled(
        self,
        mock_get_settings,
        mock_get_user_id
    ):
        """Test translation request when feature is disabled."""
        
        # Mock dependencies
        mock_get_user_id.return_value = "test-user-123"
        
        mock_settings = Mock()
        mock_settings.enable_audio_upload = True
        mock_settings.translation.enabled = False  # Translation disabled
        mock_get_settings.return_value = mock_settings
        
        # Prepare test file
        test_file_content = b"fake audio data"
        
        # Make request with translation
        response = self.client.post(
            "/api/v1/transcribe",
            data={
                "language": "en",
                "model": "large-v2",
                "translate": "true",
                "target_language": "es",
                "diarize": "true",
            },
            files={"file": ("test.wav", test_file_content, "audio/wav")}
        )
        
        # Verify error response
        assert response.status_code == 400
        assert "disabled" in response.json()["detail"].lower()

    @patch('app.api.v1.endpoints.transcribe.get_current_user_id')
    @patch('app.api.v1.endpoints.transcribe.get_settings_dependency')
    @patch('app.api.v1.endpoints.transcribe.get_job_queue')
    @patch('app.api.v1.endpoints.transcribe.get_transcription_service')
    @patch('app.api.v1.endpoints.transcribe.process_audio_async')
    def test_transcribe_with_url_and_translation(
        self,
        mock_process_audio,
        mock_get_transcription_service,
        mock_get_job_queue,
        mock_get_settings,
        mock_get_user_id
    ):
        """Test transcription from URL with translation."""
        
        # Mock dependencies
        mock_get_user_id.return_value = "test-user-123"
        
        mock_settings = Mock()
        mock_settings.enable_url_processing = True
        mock_settings.translation.enabled = True
        mock_get_settings.return_value = mock_settings
        
        mock_job_queue = AsyncMock()
        mock_job = Mock()
        mock_job_queue.create_job.return_value = mock_job
        mock_get_job_queue.return_value = mock_job_queue
        
        mock_transcription_service = Mock()
        mock_get_transcription_service.return_value = mock_transcription_service
        
        mock_task = Mock()
        mock_task.id = "task-123"
        mock_process_audio.delay.return_value = mock_task
        
        # Make request with URL and translation
        response = self.client.post(
            "/api/v1/transcribe",
            data={
                "audio_url": "https://example.com/audio.mp3",
                "language": "en",
                "model": "large-v2",
                "translate": "true",
                "target_language": "fr",
                "diarize": "true",
            }
        )
        
        # Verify response
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["status"] == "queued"
        
        # Verify task data includes translation parameters
        mock_process_audio.delay.assert_called_once()
        call_args = mock_process_audio.delay.call_args
        task_data = call_args[1]["request_data"]
        
        assert task_data["translate"] is True
        assert task_data["target_language"] == "fr"
        assert task_data["audio_url"] == "https://example.com/audio.mp3"

    def test_transcribe_no_translation_params(self):
        """Test that requests without translation work normally."""
        
        with patch('app.api.v1.endpoints.transcribe.get_current_user_id') as mock_get_user_id, \
             patch('app.api.v1.endpoints.transcribe.get_settings_dependency') as mock_get_settings, \
             patch('app.api.v1.endpoints.transcribe.get_job_queue') as mock_get_job_queue, \
             patch('app.api.v1.endpoints.transcribe.get_transcription_service') as mock_get_transcription_service, \
             patch('app.api.v1.endpoints.transcribe.process_audio_async') as mock_process_audio:
            
            # Mock dependencies
            mock_get_user_id.return_value = "test-user-123"
            
            mock_settings = Mock()
            mock_settings.enable_audio_upload = True
            mock_settings.translation.enabled = True
            mock_get_settings.return_value = mock_settings
            
            mock_job_queue = AsyncMock()
            mock_job = Mock()
            mock_job_queue.create_job.return_value = mock_job
            mock_get_job_queue.return_value = mock_job_queue
            
            mock_transcription_service = Mock()
            mock_get_transcription_service.return_value = mock_transcription_service
            
            mock_task = Mock()
            mock_task.id = "task-123"
            mock_process_audio.delay.return_value = mock_task
            
            # Prepare test file
            test_file_content = b"fake audio data"
            
            # Make request without translation
            response = self.client.post(
                "/api/v1/transcribe",
                data={
                    "language": "en",
                    "model": "large-v2",
                    "diarize": "true",
                },
                files={"file": ("test.wav", test_file_content, "audio/wav")}
            )
            
            # Verify response
            assert response.status_code == 201
            
            # Verify task data doesn't include translation
            mock_process_audio.delay.assert_called_once()
            call_args = mock_process_audio.delay.call_args
            task_data = call_args[1]["request_data"]
            
            assert task_data.get("translate", False) is False
            assert task_data.get("target_language") is None
