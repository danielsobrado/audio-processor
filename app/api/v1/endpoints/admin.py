"""
Admin endpoints for job management and system operations.
"""

import logging
from datetime import UTC, datetime
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_async_session,
    get_settings_dependency,
    require_roles,
)
from app.config.settings import Settings
from app.schemas.api import (
    AdminJobListResponse,
    AdminJobRequeueRequest,
    AdminJobRequeueResponse,
    JobResponse,
)
from app.schemas.database import JobStatus
from app.workers.tasks import process_audio_async

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/jobs",
    response_model=AdminJobListResponse,
    dependencies=[Depends(require_roles(["admin"]))],
    summary="List all jobs in the system",
    description="Retrieve all jobs across all users. Admin access required.",
)
async def list_all_jobs(
    status_filter: str | None = Query(None, description="Filter by job status"),
    limit: int | None = Query(None, ge=1, description="Maximum number of jobs to return"),
    offset: int | None = Query(None, ge=0, description="Number of jobs to skip"),
    session: AsyncSession = Depends(get_async_session),
    settings: Settings = Depends(get_settings_dependency),
) -> AdminJobListResponse:
    """
    Retrieve all jobs in the system with pagination and filtering.

    This endpoint provides system administrators with comprehensive access to all
    transcription jobs across all users. It supports filtering by job status and
    includes pagination for handling large datasets.

    Args:
        status_filter: Optional filter to show only jobs with a specific status.
        limit: Maximum number of jobs to return (respects system limits).
        offset: Number of jobs to skip for pagination.
        session: Database session dependency.
        settings: Application settings dependency.

    Returns:
        A paginated list of jobs with metadata including total count.

    Raises:
        HTTPException: 400 for invalid status filter, 500 for database errors.
    """

    # Use settings for defaults
    final_limit = limit if limit is not None else settings.api.default_limit
    final_offset = offset if offset is not None else settings.api.default_offset

    if final_limit > settings.api.max_limit:
        final_limit = settings.api.max_limit

    try:
        from sqlalchemy import desc, func, select

        from app.schemas.database import TranscriptionJob

        # Build base query
        query = select(TranscriptionJob).order_by(desc(TranscriptionJob.created_at))

        # Apply status filter if provided
        job_status = None
        if status_filter:
            try:
                job_status = JobStatus(status_filter.lower())
                query = query.where(TranscriptionJob.status == job_status)
            except ValueError:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}. Valid values: {
                        [s.value for s in JobStatus]
                    }",
                )

        # Get total count for pagination
        count_query = select(func.count()).select_from(TranscriptionJob)
        if status_filter and job_status is not None:
            count_query = count_query.where(TranscriptionJob.status == job_status)

        total_result = await session.execute(count_query)
        total_count = total_result.scalar()

        # Apply pagination
        query = query.offset(final_offset).limit(final_limit)

        # Execute query
        result = await session.execute(query)
        jobs = result.scalars().all()

        # Convert to response format using new unified database schema
        job_responses = []
        for job in jobs:
            # Type casting for pyright compatibility with SQLAlchemy models
            request_id = cast(str, job.request_id)
            user_id = cast(int, job.user_id)
            status = cast(JobStatus, job.status)
            progress = cast(float, job.progress)
            created = cast(datetime, job.created_at)
            updated = cast(datetime, job.updated_at)
            result = cast(dict | None, job.result)
            error = cast(str | None, job.error)
            task_id = cast(str | None, job.task_id)
            job_type = cast(str, job.job_type)
            parameters = cast(dict | None, job.parameters)

            # Fallback to legacy fields if new fields are None
            transcription_result = cast(str | None, job.transcription_result)
            error_message = cast(str | None, job.error_message)

            if result is None and transcription_result:
                result = {"transcription": transcription_result}
            if error is None:
                error = error_message

            job_response = JobResponse(
                request_id=str(request_id),
                user_id=str(user_id),
                status=status.value,
                progress=progress,
                created=created,
                updated=updated,
                result=result,
                error=error,
                task_id=task_id,
                job_type=job_type,
                parameters=parameters,
            )
            job_responses.append(job_response)

        logger.info(f"Admin retrieved {len(job_responses)} jobs (total: {total_count})")

        return AdminJobListResponse(
            jobs=job_responses,
            total_count=total_count or 0,
            limit=final_limit,
            offset=final_offset,
        )

    except HTTPException:
        # Re-raise HTTPExceptions (like 400 errors) as-is
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve admin job list: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job list",
        )


@router.post(
    "/jobs/{request_id}/requeue",
    response_model=AdminJobRequeueResponse,
    dependencies=[Depends(require_roles(["admin"]))],
    summary="Requeue a failed job",
    description="Retry a failed transcription job. Admin access required.",
)
async def requeue_job(
    request_id: str,
    requeue_request: AdminJobRequeueRequest,
    session: AsyncSession = Depends(get_async_session),
) -> AdminJobRequeueResponse:
    """
    Requeue a failed job for retry processing.

    This endpoint allows administrators to retry failed jobs, which is useful for:
    - Temporary infrastructure failures
    - Network issues during processing
    - Service outages that affected job processing

    Args:
        request_id: The unique identifier of the job to requeue.
        requeue_request: Request body containing reason for requeue.
        session: Database session dependency.

    Returns:
        Response containing the new task ID and status information.

    Raises:
        HTTPException: 404 if job not found, 400 if job cannot be requeued,
                      500 for database or task creation errors.
    """

    try:
        from sqlalchemy import select, update

        from app.schemas.database import TranscriptionJob

        # Get the job
        query = select(TranscriptionJob).where(TranscriptionJob.request_id == request_id)
        result = await session.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Job with request_id {request_id} not found",
            )

        # Check if job can be requeued (cast to help pyright)
        job_status = cast(JobStatus, job.status)
        if job_status != JobStatus.FAILED:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"Job status is '{job.status.value}'. Only failed jobs can be requeued.",
            )

        # Update job status to pending
        update_stmt = (
            update(TranscriptionJob)
            .where(TranscriptionJob.request_id == request_id)
            .values(
                status=JobStatus.PENDING,
                progress=0.0,
                error=None,
                updated_at=datetime.now(UTC),
                task_id=None,  # Will be set when new task is created
            )
        )
        await session.execute(update_stmt)
        await session.commit()

        # Create new Celery task
        job_parameters = cast(dict | None, job.parameters)
        task_data = job_parameters.copy() if job_parameters else {}
        task_data["request_id"] = request_id

        # Submit new task
        task = process_audio_async.delay(
            request_data=task_data,
            audio_data=None,  # Audio data should be in file path or URL
        )

        # Update job with new task ID
        update_task_stmt = (
            update(TranscriptionJob)
            .where(TranscriptionJob.request_id == request_id)
            .values(task_id=task.id)
        )
        await session.execute(update_task_stmt)
        await session.commit()

        logger.info(
            f"Admin requeued job {request_id} with new task {task.id}. "
            f"Reason: {requeue_request.reason}"
        )

        return AdminJobRequeueResponse(
            request_id=request_id,
            new_task_id=task.id,
            status="requeued",
            message=f"Job successfully requeued. New task ID: {task.id}",
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Failed to requeue job {request_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to requeue job",
        )


@router.get(
    "/jobs/{request_id}",
    response_model=JobResponse,
    dependencies=[Depends(require_roles(["admin"]))],
    summary="Get detailed job information",
    description=(
        "Retrieve detailed information about any job in the system. Admin access required."
    ),
)
async def get_job_details(
    request_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> JobResponse:
    """
    Get detailed information about a specific job.

    This endpoint provides comprehensive job information for troubleshooting
    and support purposes. It includes all job metadata, execution details,
    and error information if applicable.

    Args:
        request_id: The unique identifier of the job to retrieve.
        session: Database session dependency.

    Returns:
        Complete job information including status, progress, results, and errors.

    Raises:
        HTTPException: 404 if job not found, 500 for database errors.
    """

    try:
        from sqlalchemy import select

        from app.schemas.database import TranscriptionJob

        query = select(TranscriptionJob).where(TranscriptionJob.request_id == request_id)
        result = await session.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Job with request_id {request_id} not found",
            )

        # Type casting for pyright compatibility with SQLAlchemy models
        request_id = cast(str, job.request_id)
        user_id = cast(int, job.user_id)
        status = cast(JobStatus, job.status)
        progress = cast(float, job.progress)
        created = cast(datetime, job.created_at)
        updated = cast(datetime, job.updated_at)
        result = cast(dict | None, job.result)
        error = cast(str | None, job.error)
        task_id = cast(str | None, job.task_id)
        job_type = cast(str, job.job_type)
        parameters = cast(dict | None, job.parameters)

        # Fallback to legacy fields if new fields are None
        transcription_result = cast(str | None, job.transcription_result)
        error_message = cast(str | None, job.error_message)

        if result is None and transcription_result:
            result = {"transcription": transcription_result}
        if error is None:
            error = error_message

        return JobResponse(
            request_id=str(request_id),
            user_id=str(user_id),
            status=status.value,
            progress=progress,
            created=created,
            updated=updated,
            result=result,
            error=error,
            task_id=task_id,
            job_type=job_type,
            parameters=parameters,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve job details for {request_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job details",
        )


@router.delete(
    "/jobs/{request_id}",
    dependencies=[Depends(require_roles(["admin"]))],
    summary="Delete a job",
    description="Permanently delete a job from the system. Admin access required.",
)
async def delete_job(
    request_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Permanently delete a job from the system.

    WARNING: This operation cannot be undone. Use with caution.

    This endpoint is typically used for:
    - Removing test jobs from development/testing
    - Cleaning up corrupted job records
    - GDPR compliance (data deletion requests)
    - System maintenance and cleanup

    Args:
        request_id: The unique identifier of the job to delete.
        session: Database session dependency.

    Returns:
        Confirmation message with the deleted job ID.

    Raises:
        HTTPException: 404 if job not found, 500 for database errors.
    """

    try:
        from sqlalchemy import delete, select

        from app.schemas.database import TranscriptionJob

        # Check if job exists
        query = select(TranscriptionJob).where(TranscriptionJob.request_id == request_id)
        result = await session.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Job with request_id {request_id} not found",
            )

        # Delete the job
        delete_stmt = delete(TranscriptionJob).where(TranscriptionJob.request_id == request_id)
        await session.execute(delete_stmt)
        await session.commit()

        logger.warning(f"Admin deleted job {request_id}")

        return {"message": f"Job {request_id} successfully deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {request_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job",
        )


@router.get(
    "/stats",
    dependencies=[Depends(require_roles(["admin"]))],
    summary="Get system statistics",
    description="Retrieve system-wide job statistics. Admin access required.",
)
async def get_system_stats(
    session: AsyncSession = Depends(get_async_session),
):
    """
    Get comprehensive system statistics for monitoring and reporting.

    This endpoint provides administrators with key metrics about the system's
    job processing performance, including job counts by status, recent activity,
    and overall system health indicators.

    Args:
        session: Database session dependency.

    Returns:
        Dictionary containing total jobs, recent activity, status breakdown,
        and timestamp of when statistics were generated.

    Raises:
        HTTPException: 500 for database errors or statistics calculation failures.
    """

    try:
        from sqlalchemy import func, select

        from app.schemas.database import TranscriptionJob

        # Get job counts by status
        status_query = select(TranscriptionJob.status, func.count()).group_by(
            TranscriptionJob.status
        )
        status_result = await session.execute(status_query)
        status_counts = {status.value: count for status, count in status_result.all()}

        # Get total jobs
        total_query = select(func.count()).select_from(TranscriptionJob)
        total_result = await session.execute(total_query)
        total_jobs = total_result.scalar()

        # Get recent activity (last 24 hours)
        from datetime import timedelta

        yesterday = datetime.now(UTC) - timedelta(days=1)
        recent_query = (
            select(func.count())
            .select_from(TranscriptionJob)
            .where(TranscriptionJob.created_at >= yesterday)
        )
        recent_result = await session.execute(recent_query)
        recent_jobs = recent_result.scalar()

        return {
            "total_jobs": total_jobs,
            "recent_jobs_24h": recent_jobs,
            "status_breakdown": status_counts,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to retrieve system stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics",
        )
