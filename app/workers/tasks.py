"""
Celery background tasks for audio processing.
"""

import asyncio
import logging
import tempfile
from pathlib import Path

import httpx
from app.core.deepgram_formatter import DeepgramFormatter
from app.core.job_queue import JobQueue
from app.schemas.database import JobStatus
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from app.services.summarization import SummarizationService
from app.workers.celery_app import celery_app, audio_processor_instance

logger = logging.getLogger(__name__)



async def _send_callback_notification(
    callback_url: str,
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
        logger.info(f"Sending callback notification for job {request_id} to {callback_url}")
        
        # Prepare callback payload
        payload = {
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
                logger.info(f"Callback notification sent successfully for job {request_id}: {response.status_code}")
            else:
                logger.warning(
                    f"Callback notification failed for job {request_id}: "
                    f"HTTP {response.status_code} - {response.text[:200]}"
                )
                
    except httpx.TimeoutException:
        logger.error(f"Callback notification timed out for job {request_id} to {callback_url}")
    except httpx.RequestError as e:
        logger.error(f"Callback notification request failed for job {request_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending callback for job {request_id}: {e}", exc_info=True)


@celery_app.task(bind=True, name="audio_processor.workers.tasks.process_audio")
def process_audio_async(self, request_data: dict, audio_data: Optional[bytes] = None):
    """
    Celery task to process audio files (sync wrapper for async operations).
    
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
        
        try:
            logger.info(f"Starting audio processing for job {request_id}")
            
            # Update job status to processing
            await job_queue.update_job(request_id, status=JobStatus.PROCESSING, progress=10.0)
            
            # Use the pre-initialized global AudioProcessor instance
            if audio_processor_instance is None:
                raise RuntimeError("AudioProcessor not initialized. Worker may not have started properly.")
            
            # Handle audio source (file path, URL, or uploaded data)
            if request_data.get("audio_file_path"):
                # File was saved to temp location by API endpoint
                audio_path = Path(request_data["audio_file_path"])
            elif audio_data:
                # Fallback for direct data upload (less efficient)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                    temp_file.write(audio_data)
                    audio_path = Path(temp_file.name)
            elif request_data.get("audio_url"):
                # Download audio from URL
                audio_url = request_data["audio_url"]
                logger.info(f"Downloading audio from URL: {audio_url}")
                
                # Use a temporary file to stream the download, avoiding memory issues
                with tempfile.NamedTemporaryFile(delete=False, suffix=".tmp") as temp_file:
                    audio_path = Path(temp_file.name)
                    try:
                        async with httpx.AsyncClient(timeout=60.0) as client:
                            async with client.stream("GET", audio_url, follow_redirects=True) as response:
                                response.raise_for_status()
                                async for chunk in response.aiter_bytes():
                                    temp_file.write(chunk)
                        logger.info(f"Successfully downloaded audio to {audio_path}")
                    except Exception as e:
                        logger.error(f"Failed to download audio from {audio_url}: {e}")
                        # Clean up the failed download
                        if audio_path.exists():
                            audio_path.unlink()
                        raise ValueError(f"Could not download or process audio from URL: {e}")
            else:
                raise ValueError("No audio data, file path, or URL provided")
            
            await job_queue.update_job(request_id, progress=30.0)
            
            # Process audio using the global instance
            processing_result_coroutine = audio_processor_instance.process_audio(
                audio_path=audio_path,
                language=request_data.get("language", "auto"),
                diarize=request_data.get("diarize", True),
            )
            processing_result = await processing_result_coroutine
            
            await job_queue.update_job(request_id, progress=70.0)
            
            # Format results
            formatter = DeepgramFormatter()
            deepgram_result = formatter.format_transcription_result(
                whisperx_result=processing_result,
                request_id=request_id,
                model_name=request_data.get("model", "large-v2"),
                audio_duration=processing_result.get("duration"),
                punctuate=request_data.get("punctuate", True),
                diarize=request_data.get("diarize", True),
                smart_format=request_data.get("smart_format", True),
                utterances=request_data.get("utterances", True),
            )
            
            await job_queue.update_job(request_id, progress=90.0)
            
            # Summarization
            if request_data.get("summarize"):
                summarization_service = SummarizationService()
                summary = await summarization_service.summarize_text(
                    deepgram_result["results"]["channels"][0]["alternatives"][0][
                        "transcript"
                    ]
                )
                formatter.add_summary_data(deepgram_result, summary)
            
            # TODO: Implement translation
            
            # Graph processing
            if request_data.get("enable_graph_processing", True):
                try:
                    from app.core.graph_processor import graph_processor
                    
                    # Prepare graph data from the processing result
                    graph_data = {
                        'job_id': request_id,
                        'audio_file_id': request_data.get('audio_file_id', request_id),
                        'language': request_data.get('language', 'auto'),
                        'segments': processing_result.get('segments', [])
                    }
                    
                    # Process graph asynchronously
                    graph_result = await graph_processor.process_transcription_result(graph_data)
                    
                    # Add graph processing result to the final result
                    if 'metadata' not in deepgram_result:
                        deepgram_result['metadata'] = {}
                    deepgram_result['metadata']['graph_processing'] = graph_result
                    
                    logger.info(f"Graph processing completed for job {request_id}")
                    
                except Exception as e:
                    logger.warning(f"Graph processing failed for job {request_id}: {e}")
                    # Don't fail the entire job if graph processing fails
                    if 'metadata' not in deepgram_result:
                        deepgram_result['metadata'] = {}
                    deepgram_result['metadata']['graph_processing'] = {
                        'success': False,
                        'error': str(e)
                    }
            
            # Store final result
            await job_queue.update_job(
                request_id,
                status=JobStatus.COMPLETED,
                progress=100.0,
                result=deepgram_result,
            )
            
            logger.info(f"Audio processing for job {request_id} completed successfully")
            
            # Send callback notification if URL provided
            callback_url = request_data.get("callback_url")
            if callback_url:
                await _send_callback_notification(
                    callback_url=callback_url,
                    request_id=request_id,
                    status="completed",
                    result=deepgram_result,
                )
            
            # Cleanup temporary file for both file uploads and URL downloads
            if (audio_data or request_data.get("audio_url")) and audio_path.exists():
                audio_path.unlink()
                
            return {"status": "completed", "request_id": request_id}
            
        except Exception as e:
            logger.error(f"Audio processing for job {request_id} failed: {e}", exc_info=True)
            if request_id:
                await job_queue.update_job(request_id, status=JobStatus.FAILED, error=str(e))
                
                # Send callback notification if URL provided
                callback_url = request_data.get("callback_url")
                if callback_url:
                    await _send_callback_notification(
                        callback_url=callback_url,
                        request_id=request_id,
                        status="failed",
                        error=str(e),
                    )
            
            # Cleanup temporary file in case of failure for both uploads and URL downloads
            if 'audio_path' in locals() and audio_path.exists():
                audio_path.unlink()
                
            raise
    
    # Run the async function in a new event loop
    return asyncio.run(_process_audio_async())
