"""
Integration tests for the API endpoints.
"""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """Test the /health endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "dependencies": {"database": "ok"}}


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test the root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "Audio Processing Microservice"

# TODO: Add more comprehensive integration tests for transcribe, status, and results endpoints.
# This would require mocking or setting up a test database, Redis, and Celery.
