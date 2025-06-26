"""
API endpoint for checking the status of a transcription job.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user_id
from app.core.job_queue import JobQueue
from app.models.responses import JobStatusResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/status/{request_id}",
    response_model=JobStatusResponse,
    summary="Get transcription job status",
    description="Check the processing status of a transcription job",
)
async def get_job_status(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    job_queue: JobQueue = Depends(),
) -> JobStatusResponse:
    """Get status of transcription job."""
    
    # Validate request ID format
    try:
        uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request ID format",
        )
    
    # Get job from queue
    job = await job_queue.get_job(request_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    
    # Check user access
    if job.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return JobStatusResponse(
        request_id=request_id,
        status=job.status.value,
        created=job.created_at,
        updated=job.updated_at,
        progress=job.progress,
        error=job.error,
    )
