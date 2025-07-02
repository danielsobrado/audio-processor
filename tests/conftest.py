"""
Pytest configuration and shared fixtures for all tests.
"""

import os
import pytest
from unittest.mock import patch
from functools import lru_cache

# Clear the settings cache before importing anything from app
from app.config.settings import get_settings
get_settings.cache_clear()

# Set test environment variables before importing app modules
os.environ.update({
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
})


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
    with patch('redis.asyncio.from_url') as mock:
        yield mock


@pytest.fixture
def mock_database():
    """Mock database for tests."""
    with patch('app.db.session.SessionLocal') as mock:
        yield mock


@pytest.fixture
def mock_celery():
    """Mock Celery for tests."""
    with patch('app.workers.celery_app.celery_app') as mock:
        yield mock
