"""
Job queue management for audio processing tasks.
Handles job creation, status updates, and retrieval from the database.
"""

import logging

from sqlalchemy.future import select

from app.db.session import DatabaseService, get_database
from app.schemas.database import JobStatus, TranscriptionJob

logger = logging.getLogger(__name__)


class JobQueue:
    """
    Manages transcription job lifecycle and database operations.
    This class acts as a repository for TranscriptionJob objects.
    """

    def __init__(self, db: DatabaseService | None = None):
        self._db = db

    async def initialize(self) -> None:
        """
        Initialize database connection if not provided.
        Must be called before any other method if the service was instantiated
        without a database service.
        """
        if not self._db:
            self._db = get_database()
        logger.info("JobQueue initialized with database connection")

    def _ensure_database(self) -> DatabaseService:
        """Ensure database service is available with type safety."""
        if self._db is None:
            raise RuntimeError("JobQueue not initialized. Call initialize() first.")
        return self._db

    async def create_job(
        self,
        request_id: str,
        user_id: str,
        job_type: str,
        parameters: dict,
        status: JobStatus = JobStatus.PENDING,
    ) -> TranscriptionJob:
        """
        Create a new transcription job in the database.

        Args:
            request_id: Unique identifier for the request.
            user_id: ID of the user submitting the job.
            job_type: Type of job (e.g., "transcription").
            parameters: Dictionary of job parameters.
            status: Initial status of the job.

        Returns:
            The created TranscriptionJob object.
        """
        try:
            async with self._ensure_database().get_async_session() as session:
                job = TranscriptionJob(
                    request_id=request_id,
                    user_id=user_id,
                    job_type=job_type,
                    parameters=parameters,
                    status=status,
                )
                session.add(job)
                await session.commit()
                await session.refresh(job)

                logger.info(f"Job {request_id} created for user {user_id}")
                return job

        except Exception as e:
            logger.error(f"Failed to create job {request_id}: {e}", exc_info=True)
            raise

    async def get_job(self, request_id: str) -> TranscriptionJob | None:
        """
        Retrieve a job by its request ID.

        Args:
            request_id: The request ID of the job.

        Returns:
            The TranscriptionJob object or None if not found.
        """
        try:
            async with self._ensure_database().get_async_session() as session:
                result = await session.execute(
                    select(TranscriptionJob).where(TranscriptionJob.request_id == request_id)
                )
                job = result.scalar_one_or_none()

                # Force attribute loading within session scope to prevent detached object issues
                if job:
                    # Access attributes to ensure they're loaded
                    _ = (
                        job.request_id,
                        job.status,
                        job.created_at,
                        job.updated_at,
                        job.progress,
                        job.error,
                        job.user_id,
                        job.task_id,
                    )

                return job

        except Exception as e:
            logger.error(f"Failed to retrieve job {request_id}: {e}", exc_info=True)
            return None

    async def update_job(
        self,
        request_id: str,
        status: JobStatus | None = None,
        task_id: str | None = None,
        progress: float | None = None,
        result: dict | None = None,
        error: str | None = None,
    ) -> TranscriptionJob | None:
        """
        Update an existing job in the database.

        Args:
            request_id: The request ID of the job to update.
            status: New status of the job.
            task_id: Celery task ID associated with the job.
            progress: Current processing progress (0.0 to 100.0).
            result: Final result of the job (e.g., Deepgram JSON).
            error: Error message if the job failed.

        Returns:
            The updated TranscriptionJob object or None if not found.
        """
        try:
            async with self._ensure_database().get_async_session() as session:
                # Query and update within the same session to avoid detached object issues
                result_query = await session.execute(
                    select(TranscriptionJob).where(TranscriptionJob.request_id == request_id)
                )
                job = result_query.scalar_one_or_none()

                if not job:
                    logger.warning(f"Job {request_id} not found for update")
                    return None

                # Update only the fields that are provided
                update_data = {
                    "status": status,
                    "task_id": task_id,
                    "progress": progress,
                    "result": result,
                    "error": error,
                }

                for key, value in update_data.items():
                    if value is not None:
                        setattr(job, key, value)

                await session.commit()
                await session.refresh(job)

                logger.info(f"Job {request_id} updated: status={status}, progress={progress}")
                return job

        except Exception as e:
            logger.error(f"Failed to update job {request_id}: {e}", exc_info=True)
            raise

    async def list_user_jobs(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        status_filter: JobStatus | None = None,
    ) -> list[TranscriptionJob]:
        """
        List all jobs for a specific user.

        Args:
            user_id: The ID of the user.
            limit: Maximum number of jobs to return.
            offset: Number of jobs to skip.
            status_filter: Filter jobs by status.

        Returns:
            A list of TranscriptionJob objects.
        """
        try:
            async with self._ensure_database().get_async_session() as session:
                query = select(TranscriptionJob).where(TranscriptionJob.user_id == user_id)

                if status_filter:
                    query = query.where(TranscriptionJob.status == status_filter)

                query = (
                    query.order_by(TranscriptionJob.created_at.desc()).limit(limit).offset(offset)
                )

                result = await session.execute(query)
                return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to list jobs for user {user_id}: {e}", exc_info=True)
            return []

    async def cleanup(self):
        """Cleanup resources."""
        # No-op for now, as database connection is managed externally
        logger.info("JobQueue cleanup complete")
