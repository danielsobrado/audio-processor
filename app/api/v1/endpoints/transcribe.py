"""
Transcription endpoint with Deepgram-compatible output format.
Follows Omi's API patterns for audio processing.
"""

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.dependencies import (
    get_current_user_id,
    get_job_queue,
    get_settings_dependency,
    get_transcription_service,
)
from app.config.settings import Settings
from app.core.job_queue import JobQueue
from app.schemas.api import TranscriptionRequest, TranscriptionResponse
from app.schemas.database import JobStatus
from app.services.transcription import TranscriptionService
from app.utils.audio_utils import validate_audio_file
from app.utils.validators import validate_transcription_params
from app.workers.tasks import process_audio_async

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
    file: UploadFile | None = File(None, description="Audio file to transcribe"),
    # Audio URL (alternative to file upload)
    audio_url: str | None = Form(None, description="URL to audio file"),
    # Transcription parameters
    language: str = Form("auto", description="Language code (e.g., 'en', 'ar', 'es', 'auto')"),
    model: str = Form("large-v2", description="Whisper model size"),
    # Processing options
    punctuate: bool = Form(True, description="Add punctuation to transcript"),
    diarize: bool = Form(True, description="Perform speaker diarization"),
    smart_format: bool = Form(True, description="Apply smart formatting"),
    utterances: bool = Form(True, description="Return utterance-level segments"),
    # Advanced options
    utt_split: float = Form(0.8, description="Utterance split threshold"),
    translate: bool = Form(False, description="Translate to a target language"),
    target_language: str | None = Form(
        None,
        description="The target language for translation (e.g., 'es', 'ar', 'fr'). Required if translate=True.",
    ),
    summarize: bool = Form(False, description="Generate summary"),
    # Webhook for completion notification
    callback_url: str | None = Form(None, description="Webhook URL for completion notification"),
    # Dependencies
    user_id: str = Depends(get_current_user_id),
    transcription_service: TranscriptionService = Depends(get_transcription_service),
    job_queue: JobQueue = Depends(get_job_queue),
    settings: Settings = Depends(get_settings_dependency),
) -> TranscriptionResponse:
    """
    Submit audio for transcription processing.
    Returns job information and processes audio asynchronously.
    """

    # Validate input
    if not file and not audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either audio file or audio URL must be provided",
        )

    if file and audio_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either audio file or URL, not both",
        )

    # Feature flag checks
    if file and not settings.enable_audio_upload:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Direct audio file uploads are currently disabled.",
        )

    if audio_url and not settings.enable_url_processing:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Processing from a URL is currently disabled.",
        )

    # Validate translation parameters
    if translate and not target_language:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The 'target_language' parameter is required when 'translate' is set to true.",
        )

    if translate and not settings.translation.enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Translation feature is currently disabled.",
        )

    if summarize and not settings.enable_summarization:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Summarization feature is currently disabled.",
        )

    # Validate parameters
    try:
        validate_transcription_params(
            language=language,
            model=model,
            utt_split=utt_split,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Generate request ID
    request_id = str(uuid.uuid4())

    try:
        # Handle file upload
        audio_data = None
        filename = None

        if file:
            # Validate audio file
            await validate_audio_file(file)

            # Save file to temporary location instead of loading into memory
            from app.utils.audio_utils import save_temp_audio_file

            temp_file_path = await save_temp_audio_file(file)

            filename = file.filename
            file.content_type

            logger.info(f"File upload: {filename} saved to {temp_file_path} for user {user_id}")

            # Pass file path instead of data to avoid memory issues
            audio_data = None
            audio_file_path = str(temp_file_path)

        # Create transcription request
        request = TranscriptionRequest(
            request_id=request_id,
            user_id=user_id,
            audio_url=audio_url,
            language=language,
            model=model,
            include_diarization=diarize if diarize is not None else False,
            include_summarization=summarize if summarize is not None else False,
            include_translation=translate if translate is not None else False,
            target_language=target_language,
        )

        # Create job in queue
        await job_queue.create_job(
            request_id=request_id,
            user_id=user_id,
            job_type="transcription",
            parameters=request.dict(),
            status=JobStatus.PENDING,
        )

        # Submit for async processing
        task_data = request.dict()
        if file:
            task_data["audio_file_path"] = audio_file_path

        # Add graph processing configuration
        task_data["enable_graph_processing"] = settings.graph.enabled

        task = process_audio_async.delay(
            request_data=task_data,
            audio_data=audio_data if not file else None,
        )

        # Update job with task ID
        await job_queue.update_job(request_id, task_id=task.id)

        logger.info(f"Transcription job {request_id} queued for user {user_id}")

        # Return response with job information
        return TranscriptionResponse(
            request_id=request_id,
            status="queued",
            created=datetime.now(UTC),
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
            detail="Failed to submit audio for processing",
        )


@router.delete(
    "/jobs/{request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel transcription job",
    description="Cancel a queued or processing transcription job",
)
async def cancel_job(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    job_queue: JobQueue = Depends(get_job_queue),
) -> None:
    """Cancel a transcription job."""

    # Validate request ID format
    try:
        uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request ID format"
        )

    # Get job from queue
    job = await job_queue.get_job(request_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Check user access
    if str(job.user_id) != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Check if job can be cancelled
    if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel job with status: {job.status.value}",
        )

    try:
        # Cancel Celery task if it exists
        if job.task_id is not None:
            from app.workers.celery_app import celery_app

            celery_app.control.revoke(job.task_id, terminate=True)

        # Update job status
        await job_queue.update_job(request_id, status=JobStatus.FAILED, error="Cancelled by user")

        logger.info(f"Job {request_id} cancelled by user {user_id}")

    except Exception as e:
        logger.error(f"Failed to cancel job {request_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel job",
        )


@router.get(
    "/jobs",
    summary="List user jobs",
    description="Get list of transcription jobs for the current user",
)
async def list_user_jobs(
    limit: int | None = None,
    offset: int | None = None,
    status_filter: str | None = None,
    user_id: str = Depends(get_current_user_id),
    job_queue: JobQueue = Depends(get_job_queue),
    settings: Settings = Depends(get_settings_dependency),
):
    """List transcription jobs for the current user."""

    # Use settings for defaults
    final_limit = limit if limit is not None else settings.api.default_limit
    final_offset = offset if offset is not None else settings.api.default_offset

    # Validate parameters
    if final_limit > settings.api.max_limit:
        final_limit = settings.api.max_limit
    if final_limit < 1:
        final_limit = 1

    if final_offset < 0:
        final_offset = 0

    # Validate status filter
    valid_statuses = [status.value for status in JobStatus]
    if status_filter and status_filter not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status filter. Valid values: {valid_statuses}",
        )

    try:
        jobs = await job_queue.list_user_jobs(
            user_id=user_id,
            limit=final_limit,
            offset=final_offset,
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
            "limit": final_limit,
            "offset": final_offset,
        }

    except Exception as e:
        logger.error(f"Failed to list jobs for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs",
        )
