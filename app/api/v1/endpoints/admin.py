"""
Admin endpoints for job management and system operations.
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_async_session, require_roles
from app.core.job_queue import JobQueue
from app.schemas.database import JobStatus
from app.schemas.api import (
    JobResponse,
    AdminJobListResponse,
    AdminJobRequeueRequest,
    AdminJobRequeueResponse,
)
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
    status_filter: Optional[str] = Query(None, description="Filter by job status"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    session: AsyncSession = Depends(get_async_session),
) -> AdminJobListResponse:
    """
    Retrieve all jobs in the system with pagination and filtering.
    Admin-only endpoint for system monitoring and support.
    """
    
    try:
        from sqlalchemy import select, func, desc
        from app.schemas.database import TranscriptionJob
        
        # Build base query
        query = select(TranscriptionJob).order_by(desc(TranscriptionJob.created_at))
        
        # Apply status filter if provided
        if status_filter:
            try:
                job_status = JobStatus(status_filter.lower())
                query = query.where(TranscriptionJob.status == job_status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}. Valid values: {[s.value for s in JobStatus]}"
                )
        
        # Get total count for pagination
        count_query = select(func.count()).select_from(TranscriptionJob)
        if status_filter:
            count_query = count_query.where(TranscriptionJob.status == job_status)
        
        total_result = await session.execute(count_query)
        total_count = total_result.scalar()
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        # Execute query
        result = await session.execute(query)
        jobs = result.scalars().all()
        
        # Convert to response format
        job_responses = []
        for job in jobs:
            job_response = JobResponse(
                request_id=job.request_id,
                user_id=job.user_id,
                status=job.status.value,
                progress=job.progress or 0.0,
                created=job.created_at,
                updated=job.updated_at,
                result=job.result,
                error=job.error,
                task_id=job.task_id,
                job_type=job.job_type,
                parameters=job.parameters,
            )
            job_responses.append(job_response)
        
        logger.info(f"Admin retrieved {len(job_responses)} jobs (total: {total_count})")
        
        return AdminJobListResponse(
            jobs=job_responses,
            total_count=total_count,
            limit=limit,
            offset=offset,
        )
        
    except Exception as e:
        logger.error(f"Failed to retrieve admin job list: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job list"
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
    
    The job must be in 'failed' status to be requeued.
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
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with request_id {request_id} not found"
            )
        
        # Check if job can be requeued
        if job.status != JobStatus.FAILED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job status is '{job.status.value}'. Only failed jobs can be requeued."
            )
        
        # Update job status to pending
        update_stmt = (
            update(TranscriptionJob)
            .where(TranscriptionJob.request_id == request_id)
            .values(
                status=JobStatus.PENDING,
                progress=0.0,
                error=None,
                updated_at=datetime.now(timezone.utc),
                task_id=None,  # Will be set when new task is created
            )
        )
        await session.execute(update_stmt)
        await session.commit()
        
        # Create new Celery task
        task_data = job.parameters.copy() if job.parameters else {}
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to requeue job"
        )


@router.get(
    "/jobs/{request_id}",
    response_model=JobResponse,
    dependencies=[Depends(require_roles(["admin"]))],
    summary="Get detailed job information",
    description="Retrieve detailed information about any job in the system. Admin access required.",
)
async def get_job_details(
    request_id: str,
    session: AsyncSession = Depends(get_async_session),
) -> JobResponse:
    """
    Get detailed information about a specific job.
    Admin-only endpoint for troubleshooting and support.
    """
    
    try:
        from sqlalchemy import select
        from app.schemas.database import TranscriptionJob
        
        query = select(TranscriptionJob).where(TranscriptionJob.request_id == request_id)
        result = await session.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with request_id {request_id} not found"
            )
        
        return JobResponse(
            request_id=job.request_id,
            user_id=job.user_id,
            status=job.status.value,
            progress=job.progress or 0.0,
            created=job.created_at,
            updated=job.updated_at,
            result=job.result,
            error=job.error,
            task_id=job.task_id,
            job_type=job.job_type,
            parameters=job.parameters,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve job details for {request_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job details"
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
    Typically used for:
    - Removing test jobs
    - Cleaning up corrupted job records
    - GDPR compliance (data deletion requests)
    """
    
    try:
        from sqlalchemy import select, delete
        from app.schemas.database import TranscriptionJob
        
        # Check if job exists
        query = select(TranscriptionJob).where(TranscriptionJob.request_id == request_id)
        result = await session.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with request_id {request_id} not found"
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
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job"
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
    """
    
    try:
        from sqlalchemy import select, func
        from app.schemas.database import TranscriptionJob
        
        # Get job counts by status
        status_query = (
            select(TranscriptionJob.status, func.count())
            .group_by(TranscriptionJob.status)
        )
        status_result = await session.execute(status_query)
        status_counts = {status.value: count for status, count in status_result.all()}
        
        # Get total jobs
        total_query = select(func.count()).select_from(TranscriptionJob)
        total_result = await session.execute(total_query)
        total_jobs = total_result.scalar()
        
        # Get recent activity (last 24 hours)
        from datetime import timedelta
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
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
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve system stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics"
        )
