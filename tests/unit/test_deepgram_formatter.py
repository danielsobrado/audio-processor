"""
Unit tests for the DeepgramFormatter.
"""

from datetime import UTC, datetime, timezone

import pytest

from app.core.deepgram_formatter import DeepgramFormatter


@pytest.fixture
def formatter():
    """Fixture for DeepgramFormatter."""
    return DeepgramFormatter()


def test_format_transcription_result_empty(formatter):
    """Test formatting an empty WhisperX result."""
    whisperx_result = {"segments": [], "language": "en"}
    request_id = "test-123"

    result = formatter.format_transcription_result(whisperx_result, request_id)

    assert "metadata" in result
    assert "results" in result
    assert result["metadata"]["request_id"] == request_id
    assert len(result["results"]["channels"]) == 1
    assert len(result["results"]["channels"][0]["alternatives"]) == 1
    assert result["results"]["channels"][0]["alternatives"][0]["transcript"] == ""


def test_format_transcription_result_basic(formatter):
    """Test formatting a basic WhisperX result."""
    whisperx_result = {
        "segments": [
            {
                "text": "Hello world.",
                "start": 0.0,
                "end": 1.5,
                "words": [
                    {"word": "Hello", "start": 0.0, "end": 0.5, "score": 0.9},
                    {"word": "world.", "start": 0.5, "end": 1.5, "score": 0.9},
                ],
            },
        ],
        "language": "en",
        "duration": 1.5,
    }
    request_id = "test-456"

    result = formatter.format_transcription_result(whisperx_result, request_id)

    assert result["metadata"]["request_id"] == request_id
    assert result["metadata"]["duration"] == 1.5
    assert (
        result["results"]["channels"][0]["alternatives"][0]["transcript"]
        == "Hello world."
    )
    assert len(result["results"]["channels"][0]["alternatives"][0]["words"]) == 2


def test_add_summary_data(formatter):
    """Test adding summary data to Deepgram response."""
    deepgram_response = {
        "metadata": {},
        "results": {"channels": [{"alternatives": [{"transcript": "Original text."}]}]},
    }
    summary = "This is a summary."

    result = formatter.add_summary_data(deepgram_response, summary)

    assert "summary" in result["metadata"]
    assert result["metadata"]["summary"]["text"] == summary
    assert "summary" in result["results"]
    assert result["results"]["summary"]["text"] == summary


def test_validate_deepgram_format_valid(formatter):
    """Test validation of a valid Deepgram format."""
    valid_response = {
        "metadata": {
            "request_id": "123",
            "created": datetime.now(UTC).isoformat(),
            "duration": 10.0,
            "channels": 1,
        },
        "results": {
            "channels": [
                {
                    "alternatives": [
                        {"transcript": "Test", "confidence": 0.9, "words": []}
                    ]
                }
            ]
        },
    }
    assert formatter.validate_deepgram_format(valid_response)


def test_validate_deepgram_format_invalid(formatter):
    """Test validation of an invalid Deepgram format."""
    invalid_response = {
        "metadata": {},  # Missing required keys
        "results": {},
    }
    assert not formatter.validate_deepgram_format(invalid_response)
