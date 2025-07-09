"""
API endpoint for retrieving the results of a transcription job.
"""

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_current_user_id, get_job_queue
from app.core.job_queue import JobQueue
from app.schemas.database import JobStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/results/{request_id}",
    summary="Get transcription results",
    description="Retrieve the completed transcription results in Deepgram format",
)
async def get_transcription_results(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    job_queue: JobQueue = Depends(get_job_queue),
) -> JSONResponse:
    """
    Get transcription results in Deepgram-compatible format.
    Returns the full Deepgram JSON response structure.
    """

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
    if str(job.user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Check job status
    current_status = getattr(job, "status", None)
    if current_status == JobStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Job failed: {getattr(job, 'error', None) or 'Unknown error'}",
        )

    if current_status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Job not completed. Current status: {current_status}",
        )

    # Get results
    if not job.result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job completed but no results available",
        )

    logger.info(
        f"Transcription results retrieved for job {request_id} by user {user_id}"
    )

    # Return Deepgram-formatted results
    return JSONResponse(content=job.result)
