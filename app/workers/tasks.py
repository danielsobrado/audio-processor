"""
Celery background tasks for audio processing.
"""

import asyncio
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

# --- BEGIN: Import Strategies ---
from app.core.processing_strategies import (
    FormattingStrategy,
    GraphProcessingStrategy,
    ProcessingContext,
    SummarizationStrategy,
    TranscriptionStrategy,
    TranslationStrategy,
)
# --- END: Import Strategies ---

from app.core.job_queue import JobQueue
from app.schemas.database import JobStatus
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _send_callback_notification(
    callback_url: Optional[str],
    request_id: str,
    status: str,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> None:
    """
    Send HTTP POST notification to callback URL.

    Args:
        callback_url: The URL to send the callback to.
        request_id: The job request ID.
        status: The final job status ('completed' or 'failed').
        result: The transcription result data (if successful).
        error: The error message (if failed).
    """
    if not callback_url:
        return

    try:
        logger.info(
            f"Sending callback notification for job {request_id} to {callback_url}"
        )

        # Prepare callback payload
        payload: Dict[str, Any] = {
            "request_id": request_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if status == "completed" and result:
            payload["result"] = result
        elif status == "failed" and error:
            payload["error"] = error

        # Send HTTP POST with timeout and retry logic
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                callback_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                follow_redirects=True,
            )

            # Log response for debugging
            if response.is_success:
                logger.info(
                    f"Callback notification sent successfully for job {
                        request_id}: {response.status_code}"
                )
            else:
                logger.warning(
                    f"Callback notification failed for job {request_id}: "
                    f"HTTP {response.status_code} - {response.text[:200]}"
                )

    except httpx.TimeoutException:
        logger.error(
            f"Callback notification timed out for job {request_id} to {callback_url}"
        )
    except httpx.RequestError as e:
        logger.error(f"Callback notification request failed for job {request_id}: {e}")
    except Exception as e:
        logger.error(
            f"Unexpected error sending callback for job {request_id}: {e}",
            exc_info=True,
        )


# --- BEGIN: Update Task Decorator for Retries ---
@celery_app.task(
    bind=True,
    name="audio_processor.workers.tasks.process_audio",
    autoretry_for=(Exception,),  # Retry on any standard exception
    retry_kwargs={'max_retries': 3},  # Retry a maximum of 3 times
    retry_backoff=True,  # Enable exponential backoff (e.g., 2s, 4s, 8s)
    retry_backoff_max=600,  # Cap backoff delay at 10 minutes
    task_acks_late=True,  # Ensure task is only ack'd on success
    # Don't retry on certain exceptions that indicate permanent failure
    dont_autoretry_for=(ValueError, FileNotFoundError, KeyError),
)
# --- END: Update Task Decorator for Retries ---
def process_audio_async(self, request_data: dict, audio_data: Optional[bytes] = None):
    """
    Celery task to process audio files using a strategy-based pipeline.
    
    Args:
        request_data: Dictionary containing transcription request details.
        audio_data: Raw audio data for file-based uploads.
    """

    async def _process_audio_async():
        """Inner async function that contains the actual processing logic."""
        request_id = request_data.get("request_id")
        if request_id is None:
            logger.error("Request ID is missing from request_data.")
            return

        job_queue = JobQueue()
        await job_queue.initialize()

        # --- BEGIN: Idempotency Check ---
        # Check the job status before starting any processing.
        job = await job_queue.get_job(request_id)
        if job is not None:
            current_status = getattr(job, "status", None)
            if current_status == JobStatus.COMPLETED:
                logger.info(
                    f"Job {request_id} is already completed. Skipping duplicate processing."
                )
                return {"status": "skipped_duplicate", "request_id": request_id}
        # --- END: Idempotency Check ---
        
        audio_path = None  # Initialize to None for cleanup

        try:
            logger.info(f"Starting audio processing for job {request_id}")

            # --- BEGIN: Audio Source Handling ---
            if request_data.get("audio_file_path"):
                audio_path = Path(request_data["audio_file_path"])
            elif audio_data:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_file.write(audio_data)
                    audio_path = Path(temp_file.name)
            elif request_data.get("audio_url"):
                audio_url = request_data["audio_url"]
                with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_file:
                    audio_path = Path(temp_file.name)
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        async with client.stream("GET", audio_url, follow_redirects=True) as response:
                            response.raise_for_status()
                            async for chunk in response.aiter_bytes():
                                temp_file.write(chunk)
            else:
                raise ValueError("No audio source provided.")
            # --- END: Audio Source Handling ---

            await job_queue.update_job(request_id, status=JobStatus.PROCESSING, progress=10.0)

            # --- BEGIN: Strategy Pipeline ---
            context = ProcessingContext(request_data, audio_path)
            
            # 1. Build the pipeline of strategies based on request
            pipeline = [TranscriptionStrategy(), FormattingStrategy()]
            if request_data.get("summarize"):
                pipeline.append(SummarizationStrategy())
            if request_data.get("translate"):
                pipeline.append(TranslationStrategy())
            
            # Graph processing can run in parallel or at the end
            if request_data.get("enable_graph_processing", True):
                pipeline.append(GraphProcessingStrategy())

            # 2. Execute the pipeline
            for i, strategy in enumerate(pipeline):
                if context.is_failed():
                    break
                context = await strategy.process(context)
                # Update progress based on pipeline completion
                progress = 10.0 + (80.0 * (i + 1) / len(pipeline))
                await job_queue.update_job(request_id, progress=progress)

            # 3. Check for errors from the pipeline
            if context.is_failed():
                raise context.error if context.error else RuntimeError("Unknown processing error")
            # --- END: Strategy Pipeline ---

            # Store final result
            await job_queue.update_job(
                request_id,
                status=JobStatus.COMPLETED,
                progress=100.0,
                result=context.deepgram_result,
            )
            logger.info(f"Job {request_id} completed successfully.")

            # Send callback notification
            if request_data.get("callback_url"):
                await _send_callback_notification(
                    callback_url=request_data["callback_url"],
                    request_id=request_id,
                    status="completed",
                    result=context.deepgram_result,
                )
            
            return {"status": "completed", "request_id": request_id}

        except Exception as e:
            logger.error(f"Processing for job {request_id} failed: {e}", exc_info=True)
            if request_id:
                await job_queue.update_job(request_id, status=JobStatus.FAILED, error=str(e))
                if request_data.get("callback_url"):
                    await _send_callback_notification(
                        callback_url=request_data["callback_url"],
                        request_id=request_id,
                        status="failed",
                        error=str(e),
                    )
            raise

        finally:
            # Cleanup temporary file if it was created by this worker
            if audio_path and audio_path.exists() and (audio_data or request_data.get("audio_url")):
                logger.debug(f"Cleaning up temporary file: {audio_path}")
                audio_path.unlink()

    # Run the async function in a new event loop
    return asyncio.run(_process_audio_async())
