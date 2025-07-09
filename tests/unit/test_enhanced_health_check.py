"""
Unit tests for enhanced health check functionality with Celery monitoring.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.health import health_check


class TestEnhancedHealthCheck:
    """Test enhanced health check with Celery monitoring."""

    @pytest.mark.asyncio
    async def test_health_check_all_services_ok(self):
        """Test health check when all services are healthy."""
        # Mock database session
        mock_session = AsyncMock()
        mock_session.execute.return_value = MagicMock()

        # Mock cache service
        mock_cache_service = MagicMock()
        mock_cache_service.redis_client.ping.return_value = AsyncMock()

        # Mock Celery
        with patch("app.api.v1.endpoints.health.celery_app") as mock_celery:
            mock_inspect = MagicMock()
            mock_inspect.stats.return_value = {
                "worker@hostname1": {"pool": {"max-concurrency": 4}},
                "worker@hostname2": {"pool": {"max-concurrency": 4}},
            }
            mock_celery.control.inspect.return_value = mock_inspect

            # Execute health check
            result = await health_check(mock_session, mock_cache_service)

            # Verify result
            assert result["status"] == "ok"
            assert result["dependencies"]["database"] == "ok"
            assert result["dependencies"]["redis"] == "ok"
            assert result["dependencies"]["celery_broker"] == "ok"
            assert result["dependencies"]["celery_workers"] == "ok"
            assert result["dependencies"]["worker_count"] == 2
            assert len(result["dependencies"]["active_workers"]) == 2

    @pytest.mark.asyncio
    async def test_health_check_no_workers_warning(self):
        """Test health check when broker is ok but no workers are active."""
        # Mock database and cache as healthy
        mock_session = AsyncMock()
        mock_session.execute.return_value = MagicMock()

        mock_cache_service = MagicMock()
        mock_cache_service.redis_client.ping.return_value = AsyncMock()

        # Mock Celery with no workers
        with patch("app.api.v1.endpoints.health.celery_app") as mock_celery:
            mock_inspect = MagicMock()
            mock_inspect.stats.return_value = {}  # No workers
            mock_celery.control.inspect.return_value = mock_inspect

            # Execute health check
            result = await health_check(mock_session, mock_cache_service)

            # Verify result
            assert result["status"] == "warning"
            assert result["dependencies"]["database"] == "ok"
            assert result["dependencies"]["redis"] == "ok"
            assert result["dependencies"]["celery_broker"] == "ok"
            assert result["dependencies"]["celery_workers"] == "warning"
            assert result["dependencies"]["worker_count"] == 0
            assert result["dependencies"]["active_workers"] == []

    @pytest.mark.asyncio
    async def test_health_check_celery_broker_error(self):
        """Test health check when Celery broker is unreachable."""
        # Mock database and cache as healthy
        mock_session = AsyncMock()
        mock_session.execute.return_value = MagicMock()

        mock_cache_service = MagicMock()
        mock_cache_service.redis_client.ping.return_value = AsyncMock()

        # Mock Celery broker failure
        with patch("app.api.v1.endpoints.health.celery_app") as mock_celery:
            mock_inspect = MagicMock()
            mock_inspect.stats.return_value = None  # Broker unreachable
            mock_celery.control.inspect.return_value = mock_inspect

            # Execute health check - should raise 503
            with pytest.raises(HTTPException) as exc_info:
                await health_check(mock_session, mock_cache_service)

            assert exc_info.value.status_code == 503
            assert exc_info.value.detail["status"] == "error"
            assert exc_info.value.detail["dependencies"]["celery_broker"] == "error"
            assert exc_info.value.detail["dependencies"]["celery_workers"] == "error"

    @pytest.mark.asyncio
    async def test_health_check_celery_exception(self):
        """Test health check when Celery check raises an exception."""
        # Mock database and cache as healthy
        mock_session = AsyncMock()
        mock_session.execute.return_value = MagicMock()

        mock_cache_service = MagicMock()
        mock_cache_service.redis_client.ping.return_value = AsyncMock()

        # Mock Celery exception
        with patch("app.api.v1.endpoints.health.celery_app") as mock_celery:
            mock_celery.control.inspect.side_effect = Exception("Connection refused")

            # Execute health check - should raise 503
            with pytest.raises(HTTPException) as exc_info:
                await health_check(mock_session, mock_cache_service)

            assert exc_info.value.status_code == 503
            assert exc_info.value.detail["status"] == "error"
            assert exc_info.value.detail["dependencies"]["celery_broker"] == "error"
            assert exc_info.value.detail["dependencies"]["celery_workers"] == "error"

    @pytest.mark.asyncio
    async def test_health_check_database_error(self):
        """Test health check when database is unhealthy."""
        # Mock database failure
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database connection failed")

        # Mock cache and Celery as healthy
        mock_cache_service = MagicMock()
        mock_cache_service.redis_client.ping.return_value = AsyncMock()

        with patch("app.api.v1.endpoints.health.celery_app") as mock_celery:
            mock_inspect = MagicMock()
            mock_inspect.stats.return_value = {"worker@hostname1": {}}
            mock_celery.control.inspect.return_value = mock_inspect

            # Execute health check - should raise 503
            with pytest.raises(HTTPException) as exc_info:
                await health_check(mock_session, mock_cache_service)

            assert exc_info.value.status_code == 503
            assert exc_info.value.detail["status"] == "error"
            assert exc_info.value.detail["dependencies"]["database"] == "error"

    @pytest.mark.asyncio
    async def test_health_check_redis_error(self):
        """Test health check when Redis is unhealthy."""
        # Mock database as healthy
        mock_session = AsyncMock()
        mock_session.execute.return_value = MagicMock()

        # Mock Redis failure
        mock_cache_service = MagicMock()
        mock_cache_service.redis_client.ping.side_effect = Exception(
            "Redis connection failed"
        )

        # Mock Celery as healthy
        with patch("app.api.v1.endpoints.health.celery_app") as mock_celery:
            mock_inspect = MagicMock()
            mock_inspect.stats.return_value = {"worker@hostname1": {}}
            mock_celery.control.inspect.return_value = mock_inspect

            # Execute health check - should raise 503
            with pytest.raises(HTTPException) as exc_info:
                await health_check(mock_session, mock_cache_service)

            assert exc_info.value.status_code == 503
            assert exc_info.value.detail["status"] == "error"
            assert exc_info.value.detail["dependencies"]["redis"] == "error"

    @pytest.mark.asyncio
    async def test_health_check_multiple_errors(self):
        """Test health check when multiple services are unhealthy."""
        # Mock all services as failing
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database error")

        mock_cache_service = MagicMock()
        mock_cache_service.redis_client.ping.side_effect = Exception("Redis error")

        with patch("app.api.v1.endpoints.health.celery_app") as mock_celery:
            mock_celery.control.inspect.side_effect = Exception("Celery error")

            # Execute health check - should raise 503
            with pytest.raises(HTTPException) as exc_info:
                await health_check(mock_session, mock_cache_service)

            assert exc_info.value.status_code == 503
            assert exc_info.value.detail["status"] == "error"
            assert exc_info.value.detail["dependencies"]["database"] == "error"
            assert exc_info.value.detail["dependencies"]["redis"] == "error"
            assert exc_info.value.detail["dependencies"]["celery_broker"] == "error"

    @pytest.mark.asyncio
    async def test_health_check_mixed_status_with_warning(self):
        """Test health check with mixed status including warnings."""
        # Mock database and Redis as healthy
        mock_session = AsyncMock()
        mock_session.execute.return_value = MagicMock()

        mock_cache_service = MagicMock()
        mock_cache_service.redis_client.ping.return_value = AsyncMock()

        # Mock Celery with no workers (warning condition)
        with patch("app.api.v1.endpoints.health.celery_app") as mock_celery:
            mock_inspect = MagicMock()
            mock_inspect.stats.return_value = {}  # No workers = warning
            mock_celery.control.inspect.return_value = mock_inspect

            # Execute health check
            result = await health_check(mock_session, mock_cache_service)

            # Should return warning status, not error
            assert result["status"] == "warning"
            assert result["dependencies"]["database"] == "ok"
            assert result["dependencies"]["redis"] == "ok"
            assert result["dependencies"]["celery_broker"] == "ok"
            assert result["dependencies"]["celery_workers"] == "warning"
