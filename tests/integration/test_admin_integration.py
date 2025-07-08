"""
Integration tests for admin endpoints with authentication and database.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from app.main import app


class TestAdminEndpointsIntegration:
    """Integration tests for admin endpoints."""

    def setup_method(self):
        """Set up test client and common mocks."""
        self.client = TestClient(app)
        self.admin_headers = {"Authorization": "Bearer admin-token"}

    @patch('app.api.dependencies.require_roles')
    @patch('app.api.dependencies.get_async_session')
    def test_list_all_jobs_requires_admin_role(self, mock_get_session, mock_require_roles):
        """Test that listing all jobs requires admin role."""
        # Mock admin role requirement
        mock_require_roles.return_value = lambda: None  # Mock admin check
        
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Mock successful database query
        with patch('app.api.v1.endpoints.admin.select') as mock_select:
            with patch('app.api.v1.endpoints.admin.func') as mock_func:
                # Mock job query results
                mock_job_result = MagicMock()
                mock_job_result.scalars.return_value.all.return_value = []
                
                # Mock count query results
                mock_count_result = MagicMock()
                mock_count_result.scalar.return_value = 0
                
                # Set up session execute side effects
                mock_session.execute.side_effect = [mock_count_result, mock_job_result]
                
                # Make request
                response = self.client.get(
                    "/api/v1/admin/jobs",
                    headers=self.admin_headers
                )
                
                # Verify admin role was required
                mock_require_roles.assert_called_with(["admin"])
                
                # Verify response (would be 200 if mocks work correctly)
                # In real integration test, this would test the actual auth flow

    @patch('app.api.dependencies.require_roles')
    @patch('app.api.dependencies.get_async_session')
    def test_list_all_jobs_with_pagination(self, mock_get_session, mock_require_roles):
        """Test listing jobs with pagination parameters."""
        # Mock admin auth
        mock_require_roles.return_value = lambda: None
        
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        with patch('app.api.v1.endpoints.admin.select'):
            with patch('app.api.v1.endpoints.admin.func'):
                # Mock results
                mock_job_result = MagicMock()
                mock_job_result.scalars.return_value.all.return_value = []
                
                mock_count_result = MagicMock()
                mock_count_result.scalar.return_value = 100
                
                mock_session.execute.side_effect = [mock_count_result, mock_job_result]
                
                # Make request with pagination
                response = self.client.get(
                    "/api/v1/admin/jobs?limit=25&offset=50&status_filter=completed",
                    headers=self.admin_headers
                )
                
                # Verify the query parameters are passed through
                # (would need to inspect actual database calls in real test)

    @patch('app.api.dependencies.require_roles')
    @patch('app.api.dependencies.get_async_session')
    def test_requeue_job_endpoint(self, mock_get_session, mock_require_roles):
        """Test job requeue endpoint."""
        # Mock admin auth
        mock_require_roles.return_value = lambda: None
        
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        with patch('app.api.v1.endpoints.admin.select'):
            with patch('app.api.v1.endpoints.admin.update'):
                with patch('app.api.v1.endpoints.admin.process_audio_async') as mock_task:
                    # Mock job in failed state
                    mock_job = MagicMock()
                    mock_job.status.value = "failed"
                    mock_job.parameters = {"language": "auto"}
                    
                    # Mock database query
                    mock_result = MagicMock()
                    mock_result.scalar_one_or_none.return_value = mock_job
                    mock_session.execute.return_value = mock_result
                    
                    # Mock Celery task
                    mock_celery_result = MagicMock()
                    mock_celery_result.id = "new-task-123"
                    mock_task.delay.return_value = mock_celery_result
                    
                    # Make request
                    response = self.client.post(
                        "/api/v1/admin/jobs/test-job-123/requeue",
                        headers=self.admin_headers,
                        json={"reason": "Infrastructure failure"}
                    )
                    
                    # Verify admin role required
                    mock_require_roles.assert_called_with(["admin"])

    @patch('app.api.dependencies.require_roles')
    @patch('app.api.dependencies.get_async_session')
    def test_get_job_details_endpoint(self, mock_get_session, mock_require_roles):
        """Test get job details endpoint."""
        # Mock admin auth
        mock_require_roles.return_value = lambda: None
        
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        with patch('app.api.v1.endpoints.admin.select'):
            # Mock job data
            mock_job = MagicMock()
            mock_job.request_id = "test-job-456"
            mock_job.user_id = "user-123"
            mock_job.status.value = "completed"
            mock_job.progress = 100.0
            mock_job.created_at = datetime.now(timezone.utc)
            mock_job.updated_at = datetime.now(timezone.utc)
            mock_job.result = {"transcript": "Hello world"}
            mock_job.error = None
            mock_job.task_id = "task-456"
            mock_job.job_type = "transcription"
            mock_job.parameters = {"language": "en"}
            
            mock_result = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_job
            mock_session.execute.return_value = mock_result
            
            # Make request
            response = self.client.get(
                "/api/v1/admin/jobs/test-job-456",
                headers=self.admin_headers
            )
            
            # Verify admin role required
            mock_require_roles.assert_called_with(["admin"])

    @patch('app.api.dependencies.require_roles')
    @patch('app.api.dependencies.get_async_session')
    def test_delete_job_endpoint(self, mock_get_session, mock_require_roles):
        """Test delete job endpoint."""
        # Mock admin auth
        mock_require_roles.return_value = lambda: None
        
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        with patch('app.api.v1.endpoints.admin.select'):
            with patch('app.api.v1.endpoints.admin.delete'):
                # Mock job exists
                mock_job = MagicMock()
                mock_job.request_id = "test-job-789"
                
                mock_result = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_job
                mock_session.execute.return_value = mock_result
                
                # Make request
                response = self.client.delete(
                    "/api/v1/admin/jobs/test-job-789",
                    headers=self.admin_headers
                )
                
                # Verify admin role required
                mock_require_roles.assert_called_with(["admin"])

    @patch('app.api.dependencies.require_roles')
    @patch('app.api.dependencies.get_async_session')
    def test_get_system_stats_endpoint(self, mock_get_session, mock_require_roles):
        """Test get system stats endpoint."""
        # Mock admin auth
        mock_require_roles.return_value = lambda: None
        
        # Mock database session
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        with patch('app.api.v1.endpoints.admin.select'):
            with patch('app.api.v1.endpoints.admin.func'):
                # Mock statistics query results
                mock_status_result = MagicMock()
                mock_status_result.all.return_value = [("completed", 100), ("failed", 10)]
                
                mock_total_result = MagicMock()
                mock_total_result.scalar.return_value = 110
                
                mock_recent_result = MagicMock()
                mock_recent_result.scalar.return_value = 15
                
                mock_session.execute.side_effect = [
                    mock_status_result,
                    mock_total_result,
                    mock_recent_result,
                ]
                
                # Make request
                response = self.client.get(
                    "/api/v1/admin/stats",
                    headers=self.admin_headers
                )
                
                # Verify admin role required
                mock_require_roles.assert_called_with(["admin"])

    def test_admin_endpoints_require_authentication(self):
        """Test that admin endpoints require authentication."""
        # Test without authentication headers
        endpoints = [
            ("/api/v1/admin/jobs", "GET"),
            ("/api/v1/admin/jobs/test-123", "GET"),
            ("/api/v1/admin/jobs/test-123/requeue", "POST"),
            ("/api/v1/admin/jobs/test-123", "DELETE"),
            ("/api/v1/admin/stats", "GET"),
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = self.client.get(endpoint)
            elif method == "POST":
                response = self.client.post(endpoint, json={"reason": "test"})
            elif method == "DELETE":
                response = self.client.delete(endpoint)
            
            # Should require authentication (exact response depends on auth implementation)
            # Typically would be 401 or 403
            assert response.status_code in [401, 403]

    @patch('app.api.dependencies.require_roles')
    def test_non_admin_user_forbidden(self, mock_require_roles):
        """Test that non-admin users are forbidden from admin endpoints."""
        # Mock require_roles to simulate non-admin user
        from fastapi import HTTPException
        mock_require_roles.side_effect = HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Test any admin endpoint
        response = self.client.get(
            "/api/v1/admin/jobs",
            headers={"Authorization": "Bearer user-token"}
        )
        
        # Should be forbidden
        assert response.status_code == 403


class TestHealthCheckIntegration:
    """Integration tests for enhanced health check endpoint."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    @patch('app.api.v1.endpoints.health.get_async_session')
    @patch('app.api.v1.endpoints.health.get_cache_service')
    def test_health_check_all_services_healthy(self, mock_get_cache, mock_get_session):
        """Test health check when all services are healthy."""
        # Mock database session
        mock_session = MagicMock()
        mock_session.execute.return_value = MagicMock()
        mock_get_session.return_value = mock_session
        
        # Mock cache service
        mock_cache_service = MagicMock()
        mock_cache_service.redis_client.ping.return_value = MagicMock()
        mock_get_cache.return_value = mock_cache_service
        
        # Mock Celery health check
        with patch('app.api.v1.endpoints.health.celery_app') as mock_celery:
            mock_inspect = MagicMock()
            mock_inspect.stats.return_value = {
                'worker@hostname1': {'pool': {'max-concurrency': 4}},
            }
            mock_celery.control.inspect.return_value = mock_inspect
            
            # Make request
            response = self.client.get("/api/v1/health")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert data["dependencies"]["database"] == "ok"
            assert data["dependencies"]["redis"] == "ok"
            assert data["dependencies"]["celery_broker"] == "ok"
            assert data["dependencies"]["celery_workers"] == "ok"
            assert data["dependencies"]["worker_count"] == 1

    @patch('app.api.v1.endpoints.health.get_async_session')
    @patch('app.api.v1.endpoints.health.get_cache_service')
    def test_health_check_celery_workers_warning(self, mock_get_cache, mock_get_session):
        """Test health check when no Celery workers are active."""
        # Mock database and cache as healthy
        mock_session = MagicMock()
        mock_session.execute.return_value = MagicMock()
        mock_get_session.return_value = mock_session
        
        mock_cache_service = MagicMock()
        mock_cache_service.redis_client.ping.return_value = MagicMock()
        mock_get_cache.return_value = mock_cache_service
        
        # Mock Celery with no workers
        with patch('app.api.v1.endpoints.health.celery_app') as mock_celery:
            mock_inspect = MagicMock()
            mock_inspect.stats.return_value = {}  # No workers
            mock_celery.control.inspect.return_value = mock_inspect
            
            # Make request
            response = self.client.get("/api/v1/health")
            
            # Verify response
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "warning"
            assert data["dependencies"]["celery_workers"] == "warning"
            assert data["dependencies"]["worker_count"] == 0

    @patch('app.api.v1.endpoints.health.get_async_session')
    @patch('app.api.v1.endpoints.health.get_cache_service')
    def test_health_check_service_error(self, mock_get_cache, mock_get_session):
        """Test health check when a service has an error."""
        # Mock database failure
        mock_session = MagicMock()
        mock_session.execute.side_effect = Exception("Database connection failed")
        mock_get_session.return_value = mock_session
        
        # Mock cache as healthy
        mock_cache_service = MagicMock()
        mock_cache_service.redis_client.ping.return_value = MagicMock()
        mock_get_cache.return_value = mock_cache_service
        
        # Mock Celery as healthy
        with patch('app.api.v1.endpoints.health.celery_app') as mock_celery:
            mock_inspect = MagicMock()
            mock_inspect.stats.return_value = {'worker@hostname1': {}}
            mock_celery.control.inspect.return_value = mock_inspect
            
            # Make request
            response = self.client.get("/api/v1/health")
            
            # Verify response
            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["status"] == "error"
            assert data["detail"]["dependencies"]["database"] == "error"
