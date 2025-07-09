"""
Integration tests for the API endpoints.
"""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check(app: FastAPI):
    """Test the /health endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        # In test environment, database might not be available
        assert "dependencies" in data


@pytest.mark.asyncio
async def test_root_endpoint(app: FastAPI):
    """Test the root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Audio Processing Microservice"


@pytest.mark.asyncio
async def test_transcribe_endpoint_requires_auth(app: FastAPI):
    """Test that transcribe endpoint requires authentication."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/transcribe")
        # Should return 401 or 422 depending on auth setup
        assert response.status_code in [401, 422]


@pytest.mark.asyncio
async def test_app_uses_test_settings(test_settings):
    """Test that the application is using test configuration."""
    assert test_settings.environment == "testing"
    assert test_settings.debug is True
    assert "test" in test_settings.database.database_url.lower()
    assert "15" in test_settings.redis.redis_url  # Test Redis DB


# TODO: Add more comprehensive integration tests for transcribe, status, and results endpoints.
# This would require mocking or setting up a test database, Redis, and Celery.
