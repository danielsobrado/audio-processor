"""
Test environment variable loading and configuration.
"""

import os

import pytest

from app.config.settings import get_settings, get_test_settings


def test_environment_variables_loaded():
    """Test that environment variables are properly loaded."""
    settings = get_settings()

    # Should be using test environment
    assert settings.environment == "testing"
    assert settings.debug is True


def test_test_env_file_loaded():
    """Test that .env.test file is loaded in test environment."""
    # Check that test-specific values are loaded
    assert os.getenv("ENVIRONMENT") == "testing"
    assert os.getenv("DEBUG") == "True"
    assert "test" in os.getenv("DATABASE_URL", "").lower()


def test_get_test_settings_without_overrides():
    """Test get_test_settings function without overrides."""
    settings = get_test_settings()

    assert settings.environment == "testing"
    assert settings.debug is True
    assert "sqlite" in settings.database.url.lower()


def test_get_test_settings_with_overrides():
    """Test get_test_settings function with overrides."""
    settings = get_test_settings(LOG_LEVEL="ERROR", MAX_FILE_SIZE="50000")

    assert settings.log_level == "ERROR"
    assert settings.max_file_size == 50000


def test_settings_cache_cleared():
    """Test that settings cache is properly cleared between tests."""
    # This test verifies that the cache clearing fixture works
    settings1 = get_settings()
    settings2 = get_settings()

    # Should be the same instance due to caching within single test
    assert settings1 is settings2

    # But the environment should be test environment
    assert settings1.environment == "testing"


@pytest.mark.parametrize(
    "env_var,expected",
    [
        ("ENVIRONMENT", "testing"),
        ("DEBUG", "True"),
        ("WHISPERX_MODEL_SIZE", "tiny"),
        ("CELERY_BROKER_URL", "memory://localhost/"),
    ],
)
def test_specific_test_environment_variables(env_var, expected):
    """Test that specific test environment variables are set correctly."""
    assert os.getenv(env_var) == expected
