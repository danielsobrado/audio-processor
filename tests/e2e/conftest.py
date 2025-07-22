"""
Pytest configuration for E2E tests.
"""

import asyncio
import os
from pathlib import Path

import pytest
import pytest_asyncio


# Configure pytest to handle async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables."""
    # Set environment variables for testing
    os.environ.update({
        "ENVIRONMENT": "testing",
        "DEBUG": "True",
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "DATABASE_URL": "sqlite+aiosqlite:///./test.db",
        "REDIS_URL": "redis://localhost:6379/15",
        "CELERY_BROKER_URL": "memory://localhost/",
        "CELERY_RESULT_BACKEND": "cache+memory://",
        "CELERY_ACCEPT_CONTENT": "[\"json\"]",
        "LOG_LEVEL": "DEBUG",
        "WHISPERX_MODEL_SIZE": "tiny",
        "ENABLE_AUDIO_UPLOAD": "True",
        "ENABLE_URL_PROCESSING": "True",
        "ENABLE_TRANSLATION": "False",
        "ENABLE_SUMMARIZATION": "False",
        "GRAPH_ENABLED": "True",
        "GRAPH_DATABASE_URL": "bolt://localhost:7687",
        "GRAPH_DATABASE_USERNAME": "neo4j",
        "GRAPH_DATABASE_PASSWORD": "devpassword",
        "JWT_VERIFY_SIGNATURE": "False",
        "JWT_VERIFY_AUDIENCE": "False",
        "DIARIZATION_ENABLED": "false",
    })

    # Load test environment from .env.test file
    from dotenv import load_dotenv
    load_dotenv(".env.test")

    return
