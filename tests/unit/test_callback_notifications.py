"""
Unit tests for callback notification functionality.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.workers.tasks import _send_callback_notification


class TestCallbackNotifications:
    """Test callback notification functionality."""

    @pytest.mark.asyncio
    async def test_send_callback_notification_success(self):
        """Test successful callback notification for completed job."""
        # Arrange
        callback_url = "https://example.com/webhook"
        request_id = "test-123"
        status = "completed"
        result = {"transcript": "Hello world", "confidence": 0.95}

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200

        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.return_value = mock_response

            await _send_callback_notification(
                callback_url=callback_url,
                request_id=request_id,
                status=status,
                result=result,
            )

            # Verify HTTP POST was called with correct parameters
            mock_context.post.assert_called_once()
            call_args = mock_context.post.call_args

            assert call_args[1]["json"]["request_id"] == request_id
            assert call_args[1]["json"]["status"] == status
            assert call_args[1]["json"]["result"] == result
            assert "timestamp" in call_args[1]["json"]
            assert call_args[1]["headers"]["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_send_callback_notification_failure(self):
        """Test callback notification for failed job."""
        # Arrange
        callback_url = "https://example.com/webhook"
        request_id = "test-456"
        status = "failed"
        error = "Audio file format not supported"

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200

        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.return_value = mock_response

            await _send_callback_notification(
                callback_url=callback_url,
                request_id=request_id,
                status=status,
                error=error,
            )

            # Verify HTTP POST was called with correct parameters
            mock_context.post.assert_called_once()
            call_args = mock_context.post.call_args

            assert call_args[1]["json"]["request_id"] == request_id
            assert call_args[1]["json"]["status"] == status
            assert call_args[1]["json"]["error"] == error
            assert "result" not in call_args[1]["json"]
            assert "timestamp" in call_args[1]["json"]

    @pytest.mark.asyncio
    async def test_send_callback_notification_empty_url(self):
        """Test that empty callback URL is handled gracefully."""
        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            await _send_callback_notification(
                callback_url="",
                request_id="test-789",
                status="completed",
                result={"transcript": "test"},
            )

            # Verify no HTTP call was made
            mock_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_callback_notification_none_url(self):
        """Test that None callback URL is handled gracefully."""
        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            await _send_callback_notification(
                callback_url=None,
                request_id="test-000",
                status="completed",
                result={"transcript": "test"},
            )

            # Verify no HTTP call was made
            mock_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_callback_notification_http_error(self):
        """Test callback notification with HTTP error response."""
        # Arrange
        callback_url = "https://example.com/webhook"
        request_id = "test-error"
        status = "completed"
        result = {"transcript": "test"}

        mock_response = MagicMock()
        mock_response.is_success = False
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.return_value = mock_response

            # Should not raise exception despite HTTP error
            await _send_callback_notification(
                callback_url=callback_url,
                request_id=request_id,
                status=status,
                result=result,
            )

            # Verify HTTP POST was attempted
            mock_context.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_callback_notification_timeout(self):
        """Test callback notification timeout handling."""
        # Arrange
        callback_url = "https://slow-server.com/webhook"
        request_id = "test-timeout"
        status = "completed"
        result = {"transcript": "test"}

        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.side_effect = httpx.TimeoutException("Request timed out")

            # Should not raise exception despite timeout
            await _send_callback_notification(
                callback_url=callback_url,
                request_id=request_id,
                status=status,
                result=result,
            )

            # Verify HTTP POST was attempted
            mock_context.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_callback_notification_request_error(self):
        """Test callback notification with request error."""
        # Arrange
        callback_url = "https://invalid-domain.nonexistent/webhook"
        request_id = "test-request-error"
        status = "completed"
        result = {"transcript": "test"}

        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.side_effect = httpx.RequestError("Connection failed")

            # Should not raise exception despite request error
            await _send_callback_notification(
                callback_url=callback_url,
                request_id=request_id,
                status=status,
                result=result,
            )

            # Verify HTTP POST was attempted
            mock_context.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_callback_notification_unexpected_error(self):
        """Test callback notification with unexpected error."""
        # Arrange
        callback_url = "https://example.com/webhook"
        request_id = "test-unexpected"
        status = "completed"
        result = {"transcript": "test"}

        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.side_effect = Exception("Unexpected error")

            # Should not raise exception despite unexpected error
            await _send_callback_notification(
                callback_url=callback_url,
                request_id=request_id,
                status=status,
                result=result,
            )

            # Verify HTTP POST was attempted
            mock_context.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_callback_payload_structure_completed(self):
        """Test that completed callback payload has correct structure."""
        # Arrange
        callback_url = "https://example.com/webhook"
        request_id = "test-payload"
        status = "completed"
        result = {
            "results": {
                "channels": [
                    {
                        "alternatives": [
                            {"transcript": "Hello world", "confidence": 0.95}
                        ]
                    }
                ]
            },
            "metadata": {
                "request_id": request_id,
                "model_info": {"name": "whisper-large-v2"},
            },
        }

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200

        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.return_value = mock_response

            await _send_callback_notification(
                callback_url=callback_url,
                request_id=request_id,
                status=status,
                result=result,
            )

            # Verify payload structure
            call_args = mock_context.post.call_args
            payload = call_args[1]["json"]

            assert payload["request_id"] == request_id
            assert payload["status"] == status
            assert payload["result"] == result
            assert "timestamp" in payload
            assert "error" not in payload

            # Verify timestamp format
            timestamp = payload["timestamp"]
            assert timestamp.endswith("Z") or "+" in timestamp  # ISO format

    @pytest.mark.asyncio
    async def test_callback_payload_structure_failed(self):
        """Test that failed callback payload has correct structure."""
        # Arrange
        callback_url = "https://example.com/webhook"
        request_id = "test-failed-payload"
        status = "failed"
        error = "Audio file format not supported: invalid codec"

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200

        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.return_value = mock_response

            await _send_callback_notification(
                callback_url=callback_url,
                request_id=request_id,
                status=status,
                error=error,
            )

            # Verify payload structure
            call_args = mock_context.post.call_args
            payload = call_args[1]["json"]

            assert payload["request_id"] == request_id
            assert payload["status"] == status
            assert payload["error"] == error
            assert "timestamp" in payload
            assert "result" not in payload

    @pytest.mark.asyncio
    async def test_callback_http_client_configuration(self):
        """Test that HTTP client is configured correctly."""
        # Arrange
        callback_url = "https://example.com/webhook"
        request_id = "test-config"
        status = "completed"
        result = {"transcript": "test"}

        mock_response = MagicMock()
        mock_response.is_success = True
        mock_response.status_code = 200

        # Act & Assert
        with patch("httpx.AsyncClient") as mock_client:
            mock_context = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_context
            mock_context.post.return_value = mock_response

            await _send_callback_notification(
                callback_url=callback_url,
                request_id=request_id,
                status=status,
                result=result,
            )

            # Verify HTTP client configuration
            mock_client.assert_called_once_with(timeout=30.0)

            # Verify POST request configuration
            call_args = mock_context.post.call_args
            assert call_args[0][0] == callback_url  # URL
            assert call_args[1]["headers"]["Content-Type"] == "application/json"
            assert call_args[1]["follow_redirects"] is True
