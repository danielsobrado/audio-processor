"""
API endpoint for checking the status of a transcription job.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException
from typing import cast, Optional
from datetime import datetime
from fastapi import status

from app.api.dependencies import get_current_user_id
from app.core.job_queue import JobQueue
from app.schemas.responses import JobStatusResponse

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
    if cast(str, job.user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    
    return JobStatusResponse(
        request_id=cast(str, job.request_id),
        status=cast(str, job.status),
        created=cast(datetime, job.created_at),
        updated=cast(datetime, job.updated_at),
        progress=cast(Optional[float], job.progress),
        error=cast(Optional[str], job.error),
    )
