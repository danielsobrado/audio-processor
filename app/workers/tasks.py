"""
Celery background tasks for audio processing.
"""

import asyncio
import logging
import tempfile
from pathlib import Path

from app.core.audio_processor import AudioProcessor
from app.core.deepgram_formatter import DeepgramFormatter
from app.core.job_queue import JobQueue
from app.db.models import JobStatus
from typing import Optional
from app.services.summarization import SummarizationService
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="audio_processor.workers.tasks.process_audio")
async def process_audio_async(self, request_data: dict, audio_data: Optional[bytes] = None):
    """
    Asynchronous Celery task to process audio files.
    
    Args:
        request_data: Dictionary containing transcription request details.
        audio_data: Raw audio data for file-based uploads.
    """
    
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
        
        # Initialize audio processor
        audio_processor = AudioProcessor()
        await audio_processor.initialize_models()
        
        # Handle audio source (URL or uploaded data)
        if audio_data:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_data)
                audio_path = Path(temp_file.name)
        elif request_data.get("audio_url"):
            # TODO: Implement audio download from URL
            raise NotImplementedError("Audio download from URL not yet implemented")
        else:
            raise ValueError("No audio data or URL provided")
        
        await job_queue.update_job(request_id, progress=30.0)
        
        # Process audio
        processing_result_coroutine = audio_processor.process_audio(
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
            summary = asyncio.run(
                summarization_service.summarize_text(
                    deepgram_result["results"]["channels"][0]["alternatives"][0][
                        "transcript"
                    ]
                )
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
                graph_result = asyncio.run(
                    graph_processor.process_transcription_result(graph_data)
                )
                
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
        
        # Cleanup temporary file
        if audio_data and audio_path.exists():
            audio_path.unlink()
            
        return {"status": "completed", "request_id": request_id}
        
    except Exception as e:
        logger.error(f"Audio processing for job {request_id} failed: {e}", exc_info=True)
        if request_id:
            await job_queue.update_job(request_id, status=JobStatus.FAILED, error=str(e))
        
        # Cleanup temporary file in case of failure
        if 'audio_path' in locals() and audio_path.exists():
            audio_path.unlink()
            
        raise
