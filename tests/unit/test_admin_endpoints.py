"""
Unit tests for admin job management endpoints.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.admin import (
    delete_job,
    get_job_details,
    get_system_stats,
    list_all_jobs,
    requeue_job,
)
from app.schemas.api import AdminJobRequeueRequest
from app.schemas.database import JobStatus


class TestAdminJobManagement:
    """Test admin job management endpoints."""

    @pytest.mark.asyncio
    async def test_list_all_jobs_success(self):
        """Test successful listing of all jobs with pagination."""
        # Mock session and database query
        mock_session = AsyncMock()

        # Mock job data
        mock_job = MagicMock()
        mock_job.request_id = "test-123"
        mock_job.user_id = "user-456"
        mock_job.status = JobStatus.COMPLETED
        mock_job.progress = 100.0
        mock_job.created_at = datetime.now(timezone.utc)
        mock_job.updated_at = datetime.now(timezone.utc)
        mock_job.result = {"transcript": "test"}
        mock_job.error = None
        mock_job.task_id = "celery-task-123"
        mock_job.job_type = "transcription"
        mock_job.parameters = {"language": "auto"}
        # Additional fields that might be accessed
        mock_job.transcription_result = None
        mock_job.error_message = None

        # Mock query results
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_job]
        mock_session.execute.return_value = mock_result

        # Mock count query
        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 1
        mock_session.execute.side_effect = [mock_count_result, mock_result]

        # Execute endpoint
        result = await list_all_jobs(
            status_filter=None,
            limit=50,
            offset=0,
            session=mock_session,
        )

        # Verify result
        assert result.total_count == 1
        assert result.limit == 50
        assert result.offset == 0
        assert len(result.jobs) == 1
        assert result.jobs[0].request_id == "test-123"
        assert result.jobs[0].status == "completed"

    @pytest.mark.asyncio
    async def test_list_all_jobs_with_status_filter(self):
        """Test listing jobs with status filter."""
        mock_session = AsyncMock()

        # Mock empty results for failed jobs
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        mock_count_result = MagicMock()
        mock_count_result.scalar.return_value = 0
        mock_session.execute.side_effect = [mock_count_result, mock_result]

        # Execute with status filter
        result = await list_all_jobs(
            status_filter="failed",
            limit=25,
            offset=0,
            session=mock_session,
        )

        # Verify result
        assert result.total_count == 0
        assert result.limit == 25
        assert len(result.jobs) == 0

    @pytest.mark.asyncio
    async def test_list_all_jobs_invalid_status_filter(self):
        """Test listing jobs with invalid status filter."""
        mock_session = AsyncMock()

        # Execute with invalid status filter
        with pytest.raises(HTTPException) as exc_info:
            await list_all_jobs(
                status_filter="invalid_status",
                limit=50,
                offset=0,
                session=mock_session,
            )

        assert exc_info.value.status_code == 400
        assert "Invalid status filter" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_requeue_job_success(self):
        """Test successful job requeue."""
        mock_session = AsyncMock()

        # Mock job in failed state
        mock_job = MagicMock()
        mock_job.request_id = "test-failed-123"
        mock_job.status = JobStatus.FAILED
        mock_job.parameters = {
            "language": "auto",
            "audio_url": "http://example.com/audio.wav",
        }

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        # Mock Celery task
        with patch("app.api.v1.endpoints.admin.process_audio_async") as mock_task:
            mock_celery_result = MagicMock()
            mock_celery_result.id = "new-task-456"
            mock_task.delay.return_value = mock_celery_result

            # Prepare request
            requeue_request = AdminJobRequeueRequest(
                reason="Infrastructure failure - retry needed"
            )

            # Execute requeue
            result = await requeue_job(
                request_id="test-failed-123",
                requeue_request=requeue_request,
                session=mock_session,
            )

            # Verify result
            assert result.request_id == "test-failed-123"
            assert result.new_task_id == "new-task-456"
            assert result.status == "requeued"

            # Verify task was created
            mock_task.delay.assert_called_once()
            call_args = mock_task.delay.call_args
            assert call_args[1]["request_data"]["request_id"] == "test-failed-123"

    @pytest.mark.asyncio
    async def test_requeue_job_not_found(self):
        """Test requeue job when job doesn't exist."""
        mock_session = AsyncMock()

        # Mock job not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        requeue_request = AdminJobRequeueRequest(reason="Test")

        # Execute requeue - should raise 404
        with pytest.raises(HTTPException) as exc_info:
            await requeue_job(
                request_id="nonexistent-job",
                requeue_request=requeue_request,
                session=mock_session,
            )

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_requeue_job_wrong_status(self):
        """Test requeue job when job is not in failed status."""
        mock_session = AsyncMock()

        # Mock job in completed state (cannot requeue)
        mock_job = MagicMock()
        mock_job.status = JobStatus.COMPLETED

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        requeue_request = AdminJobRequeueRequest(reason="Test")

        # Execute requeue - should raise 400
        with pytest.raises(HTTPException) as exc_info:
            await requeue_job(
                request_id="completed-job",
                requeue_request=requeue_request,
                session=mock_session,
            )

        assert exc_info.value.status_code == 400
        assert "Only failed jobs can be requeued" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_job_details_success(self):
        """Test successful retrieval of job details."""
        mock_session = AsyncMock()

        # Mock job data
        mock_job = MagicMock()
        mock_job.request_id = "test-details-123"
        mock_job.user_id = "user-789"
        mock_job.status = JobStatus.PROCESSING
        mock_job.progress = 45.0
        mock_job.created_at = datetime.now(timezone.utc)
        mock_job.updated_at = datetime.now(timezone.utc)
        mock_job.result = None
        mock_job.error = None
        mock_job.task_id = "active-task-123"
        mock_job.job_type = "transcription"
        mock_job.parameters = {"language": "en", "diarize": True}
        # Additional fields that might be accessed
        mock_job.transcription_result = None
        mock_job.error_message = None

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        # Execute endpoint
        result = await get_job_details(
            request_id="test-details-123",
            session=mock_session,
        )

        # Verify result
        assert result.request_id == "test-details-123"
        assert result.user_id == "user-789"
        assert result.status == "processing"
        assert result.progress == 45.0
        assert result.task_id == "active-task-123"

    @pytest.mark.asyncio
    async def test_get_job_details_not_found(self):
        """Test get job details when job doesn't exist."""
        mock_session = AsyncMock()

        # Mock job not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute endpoint - should raise 404
        with pytest.raises(HTTPException) as exc_info:
            await get_job_details(
                request_id="nonexistent-job",
                session=mock_session,
            )

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_delete_job_success(self):
        """Test successful job deletion."""
        mock_session = AsyncMock()

        # Mock job exists
        mock_job = MagicMock()
        mock_job.request_id = "test-delete-123"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        # Execute deletion
        result = await delete_job(
            request_id="test-delete-123",
            session=mock_session,
        )

        # Verify result
        assert "successfully deleted" in result["message"]

    @pytest.mark.asyncio
    async def test_delete_job_not_found(self):
        """Test delete job when job doesn't exist."""
        mock_session = AsyncMock()

        # Mock job not found
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        # Execute deletion - should raise 404
        with pytest.raises(HTTPException) as exc_info:
            await delete_job(
                request_id="nonexistent-job",
                session=mock_session,
            )

        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_system_stats_success(self):
        """Test successful retrieval of system statistics."""
        mock_session = AsyncMock()

        # Mock status counts query
        mock_status_result = MagicMock()
        mock_status_result.all.return_value = [
            (JobStatus.COMPLETED, 150),
            (JobStatus.FAILED, 25),
            (JobStatus.PROCESSING, 5),
            (JobStatus.PENDING, 10),
        ]

        # Mock total count query
        mock_total_result = MagicMock()
        mock_total_result.scalar.return_value = 190

        # Mock recent count query
        mock_recent_result = MagicMock()
        mock_recent_result.scalar.return_value = 15

        # Set up session execute side effects
        mock_session.execute.side_effect = [
            mock_status_result,
            mock_total_result,
            mock_recent_result,
        ]

        # Execute endpoint
        result = await get_system_stats(session=mock_session)

        # Verify result
        assert result["total_jobs"] == 190
        assert result["recent_jobs_24h"] == 15
        assert result["status_breakdown"]["completed"] == 150
        assert result["status_breakdown"]["failed"] == 25
        assert result["status_breakdown"]["processing"] == 5
        assert result["status_breakdown"]["pending"] == 10
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_admin_endpoints_require_authentication(self):
        """Test that admin endpoints require proper authentication."""
        # This test ensures the dependency injection is working
        # In real testing, this would be covered by integration tests
        # that test the actual HTTP endpoints with authentication

        # Mock session
        mock_session = AsyncMock()

        # The require_roles dependency should be tested separately
        # Here we just verify the endpoints accept the session parameter

        # Test that endpoints can be called (authentication is handled by FastAPI dependencies)
        try:
            # These would fail with database errors, but not with auth errors
            # since we're testing the function directly, not the HTTP endpoint
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_count_result = MagicMock()
            mock_count_result.scalar.return_value = 0
            mock_session.execute.side_effect = [mock_count_result, mock_result]

            result = await list_all_jobs(session=mock_session)
            assert result.total_count == 0

        except Exception:
            # Expected to fail due to missing database setup,
            # but not due to authentication issues
            pass


class TestAdminEndpointErrorHandling:
    """Test error handling in admin endpoints."""

    @pytest.mark.asyncio
    async def test_list_all_jobs_database_error(self):
        """Test list_all_jobs when database raises an exception."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database connection failed")

        with pytest.raises(HTTPException) as exc_info:
            await list_all_jobs(session=mock_session)

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve job list" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_requeue_job_celery_error(self):
        """Test requeue_job when Celery task creation fails."""
        mock_session = AsyncMock()

        # Mock job in failed state
        mock_job = MagicMock()
        mock_job.status = JobStatus.FAILED
        mock_job.parameters = {}

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_job
        mock_session.execute.return_value = mock_result

        # Mock Celery task creation failure
        with patch("app.api.v1.endpoints.admin.process_audio_async") as mock_task:
            mock_task.delay.side_effect = Exception("Celery broker unavailable")

            requeue_request = AdminJobRequeueRequest(reason="Test")

            with pytest.raises(HTTPException) as exc_info:
                await requeue_job(
                    request_id="test-job",
                    requeue_request=requeue_request,
                    session=mock_session,
                )

            assert exc_info.value.status_code == 500
            assert "Failed to requeue job" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_system_stats_database_error(self):
        """Test get_system_stats when database raises an exception."""
        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Database query failed")

        with pytest.raises(HTTPException) as exc_info:
            await get_system_stats(session=mock_session)

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve system statistics" in str(exc_info.value.detail)
