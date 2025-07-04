"""
Transcription endpoint with Deepgram-compatible output format.
Follows Omi's API patterns for audio processing.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_current_user_id
from app.core.job_queue import JobQueue
from app.models.requests import TranscriptionRequest
from app.models.responses import TranscriptionResponse, JobStatusResponse
from app.services.transcription import TranscriptionService
from app.utils.audio_utils import validate_audio_file
from app.utils.validators import validate_transcription_params
from app.workers.tasks import process_audio_async
from app.models.database import JobStatus

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit audio for transcription",
    description="Upload audio file or provide URL for transcription with Deepgram-compatible output",
)
async def transcribe_audio(
    # Audio file upload
    file: Optional[UploadFile] = File(None, description="Audio file to transcribe"),
    
    # Audio URL (alternative to file upload)
    audio_url: Optional[str] = Form(None, description="URL to audio file"),
    
    # Transcription parameters
    language: str = Form("auto", description="Language code (e.g., 'en', 'es', 'auto')"),
    model: str = Form("large-v2", description="Whisper model size"),
    
    # Processing options
    punctuate: bool = Form(True, description="Add punctuation to transcript"),
    diarize: bool = Form(True, description="Perform speaker diarization"),
    smart_format: bool = Form(True, description="Apply smart formatting"),
    utterances: bool = Form(True, description="Return utterance-level segments"),
    
    # Advanced options
    utt_split: float = Form(0.8, description="Utterance split threshold"),
    translate: bool = Form(False, description="Translate to English"),
    summarize: bool = Form(False, description="Generate summary"),
    
    # Webhook for completion notification
    callback_url: Optional[str] = Form(None, description="Webhook URL for completion notification"),
    
    # Dependencies
    user_id: str = Depends(get_current_user_id),
    transcription_service: TranscriptionService = Depends(),
    job_queue: JobQueue = Depends(),
) -> TranscriptionResponse:
    """
    Submit audio for transcription processing.
    Returns job information and processes audio asynchronously.
    """
    
    # Validate input
    if not file and not audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either audio file or audio URL must be provided"
        )
    
    if file and audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either audio file or URL, not both"
        )
    
    # Validate parameters
    try:
        validate_transcription_params(
            language=language,
            model=model,
            utt_split=utt_split,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Generate request ID
    request_id = str(uuid.uuid4())
    
    try:
        # Handle file upload
        audio_data = None
        filename = None
        content_type = None
        
        if file:
            # Validate audio file
            await validate_audio_file(file)
            
            # Read file data
            audio_data = await file.read()
            filename = file.filename
            content_type = file.content_type
            
            logger.info(f"File upload: {filename} ({len(audio_data)} bytes) for user {user_id}")
        
        # Create transcription request
        request = TranscriptionRequest(
            request_id=request_id,
            user_id=user_id,
            audio_url=audio_url,
            language=language,
            model=model,
            punctuate=punctuate,
            diarize=diarize,
            smart_format=smart_format,
            utterances=utterances,
            utt_split=utt_split,
            translate=translate,
            summarize=summarize,
            callback_url=callback_url,
            filename=filename,
            content_type=content_type,
        )
        
        # Create job in queue
        job = await job_queue.create_job(
            request_id=request_id,
            user_id=user_id,
            job_type="transcription",
            parameters=request.dict(),
            status=JobStatus.QUEUED.value,
        )
        
        # Submit for async processing
        task = process_audio_async.delay(
            request_data=request.dict(),
            audio_data=audio_data,
        )
        
        # Update job with task ID
        await job_queue.update_job(request_id, task_id=task.id)
        
        logger.info(f"Transcription job {request_id} queued for user {user_id}")
        
        # Return response with job information
        return TranscriptionResponse(
            request_id=request_id,
            status="queued",
            created=datetime.now(timezone.utc),
            message="Audio submitted for processing",
        )
        
    except Exception as e:
        logger.error(f"Transcription submission failed: {e}", exc_info=True)
        
        # Update job status if created
        try:
            await job_queue.update_job(request_id, status=JobStatus.FAILED, error=str(e))
        except Exception:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit audio for processing"
        )


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
            detail="Invalid request ID format"
        )
    
    # Get job from queue
    job = await job_queue.get_job(request_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check user access
    if str(job.user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Calculate progress based on status
    progress = 0
    if job.status == JobStatus.QUEUED.value:
        progress = 0
    elif job.status == JobStatus.PROCESSING.value:
        progress = job.progress or 50  # Default progress if not set
    elif job.status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
        progress = 100
    
    return JobStatusResponse(
        request_id=request_id,
        status=job.status.value,
        created=job.created_at,
        updated=job.updated_at,
        progress=progress,
        error=job.error,
    )


@router.get(
    "/results/{request_id}",
    summary="Get transcription results",
    description="Retrieve the completed transcription results in Deepgram format",
)
async def get_transcription_results(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    job_queue: JobQueue = Depends(),
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
            detail="Invalid request ID format"
        )
    
    # Get job from queue
    job = await job_queue.get_job(request_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check user access
    if str(job.user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check job status
    if job.status == JobStatus.FAILED.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Job failed: {job.error or 'Unknown error'}"
        )
    
    if job.status != JobStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail=f"Job not completed. Current status: {job.status.value}"
        )
    
    # Get results
    if not job.result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job completed but no results available"
        )
    
    logger.info(f"Transcription results retrieved for job {request_id} by user {user_id}")
    
    # Return Deepgram-formatted results
    return JSONResponse(content=job.result)


@router.delete(
    "/jobs/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel transcription job",
    description="Cancel a queued or processing transcription job",
)
async def cancel_job(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    job_queue: JobQueue = Depends(),
) -> None:
    """Cancel a transcription job."""
    
    # Validate request ID format
    try:
        uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request ID format"
        )
    
    # Get job from queue
    job = await job_queue.get_job(request_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Check user access
    if str(job.user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if job can be cancelled
    if job.status in [JobStatus.COMPLETED.value, JobStatus.FAILED.value]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel job with status: {job.status.value}"
        )
    
    try:
        # Cancel Celery task if it exists
        if job.task_id:
            from app.workers.celery_app import celery_app
            celery_app.control.revoke(job.task_id, terminate=True)
        
        # Update job status
        await job_queue.update_job(
            request_id,
            status=JobStatus.FAILED.value,
            error="Cancelled by user"
        )
        
        logger.info(f"Job {request_id} cancelled by user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to cancel job {request_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel job"
        )


@router.get(
    "/jobs",
    summary="List user jobs",
    description="Get list of transcription jobs for the current user",
)
async def list_user_jobs(
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    job_queue: JobQueue = Depends(),
):
    """List transcription jobs for the current user."""
    
    # Validate parameters
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 1
    
    if offset < 0:
        offset = 0
    
    # Validate status filter
    valid_statuses = [status.value for status in JobStatus]
    if status_filter and status_filter not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status filter. Valid values: {valid_statuses}"
        )
    
    try:
        jobs = await job_queue.list_user_jobs(
            user_id=user_id,
            limit=limit,
            offset=offset,
            status_filter=JobStatus(status_filter) if status_filter else None,
        )
        
        return {
            "jobs": [
                {
                    "request_id": job.request_id,
                    "status": job.status.value,
                    "created": job.created_at,
                    "updated": job.updated_at,
                    "progress": job.progress,
                }
                for job in jobs
            ],
            "limit": limit,
            "offset": offset,
        }
        
    except Exception as e:
        logger.error(f"Failed to list jobs for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs"
        )