"""
Pytest configuration and shared fixtures for all tests.
"""

import os
import sys
from functools import lru_cache
from unittest.mock import patch

import pytest

# Add the project root to sys.path to ensure app package is discoverable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Explicitly import the app package (now discoverable)
import app

# Clear the settings cache before importing anything from app
from app.config.settings import get_settings

get_settings.cache_clear()

# Set test environment variables before importing app modules
os.environ.update(
    {
        "ENVIRONMENT": "testing",
        "DEBUG": "True",
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
        "REDIS_URL": "redis://localhost:6379/15",  # Use different Redis DB for tests
        "CELERY_BROKER_URL": "memory://localhost/",
        "CELERY_RESULT_BACKEND": "cache+memory://",
        "LOG_LEVEL": "DEBUG",
        "DEEPGRAM_API_KEY": "test-api-key",
        "WHISPERX_MODEL_SIZE": "tiny",  # Use smallest model for faster tests
        "ENABLE_AUDIO_UPLOAD": "True",
        "ENABLE_URL_PROCESSING": "True",
        "ENABLE_TRANSLATION": "False",  # Disable external services in tests
        "ENABLE_SUMMARIZATION": "False",
        # Graph database test configuration
        "GRAPH_ENABLED": "False",  # Disable graph by default in tests
        "NEO4J_URL": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "test-password",
    }
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables and configuration."""
    # Clear any cached settings
    get_settings.cache_clear()

    yield

    # Cleanup after all tests
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear settings cache before each test to ensure fresh config."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def test_settings():
    """Provide test-specific settings instance."""
    from app.config.settings import Settings

    return Settings()


@pytest.fixture
def mock_redis():
    """Mock Redis client for tests."""
    with patch("redis.asyncio.from_url") as mock:
        yield mock


@pytest.fixture
def mock_database():
    """Mock database for tests."""
    with patch("app.db.session.SessionLocal") as mock:
        yield mock


@pytest.fixture
def mock_celery():
    """Mock Celery for tests."""
    with patch("app.workers.celery_app.celery_app") as mock:
        yield mock


@pytest.fixture
def mock_neo4j():
    """Mock Neo4j for tests."""
    with patch("app.db.neo4j_session.get_neo4j_session") as mock:
        yield mock


@pytest.fixture
def mock_graph_enabled():
    """Mock graph functionality enabled."""
    with patch("app.config.settings.get_settings") as mock_settings:
        mock_settings.return_value.graph.enabled = True
        mock_settings.return_value.graph.neo4j.url = "bolt://localhost:7687"
        mock_settings.return_value.graph.neo4j.username = "neo4j"
        mock_settings.return_value.graph.neo4j.password = "test-password"
        yield mock_settings


@pytest.fixture
def mock_graph_disabled():
    """Mock graph functionality disabled."""
    with patch("app.config.settings.get_settings") as mock_settings:
        mock_settings.return_value.graph.enabled = False
        yield mock_settings


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        "conversation_id": "test-conv-123",
        "request_id": "test-req-456",
        "segments": [
            {
                "start": 0.0,
                "end": 3.5,
                "text": "Hello, this is John speaking about the project.",
                "speaker": "Speaker_1",
                "speaker_id": "john-doe",
            },
            {
                "start": 3.5,
                "end": 8.2,
                "text": "Hi John, this is Jane. Let's discuss the budget at jane@company.com",
                "speaker": "Speaker_2",
                "speaker_id": "jane-smith",
            },
            {
                "start": 8.2,
                "end": 12.0,
                "text": "Great idea! Call me at 555-123-4567 tomorrow.",
                "speaker": "Speaker_1",
                "speaker_id": "john-doe",
            },
        ],
        "metadata": {
            "duration": 12.0,
            "language": "en",
            "created_at": "2024-01-15T10:30:00Z",
        },
    }
