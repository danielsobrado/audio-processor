"""
Core transcription service.
Orchestrates the transcription process, including job creation and task submission.
"""

import logging
from typing import Optional

from fastapi import UploadFile

from app.core.job_queue import JobQueue
from app.models.database import JobStatus
from app.models.requests import TranscriptionRequest
from app.workers.tasks import process_audio_async

logger = logging.getLogger(__name__)


class TranscriptionService:
    """
    Service layer for handling transcription requests.
    """
    
    def __init__(self, job_queue: JobQueue):
        self.job_queue = job_queue
    
    async def submit_transcription_job(
        self,
        request: TranscriptionRequest,
        audio_file: Optional[UploadFile] = None,
    ) -> str:
        """
        Submit a new transcription job.
        
        Args:
            request: The transcription request model.
            audio_file: The uploaded audio file, if any.
        
        Returns:
            The request ID of the created job.
        """
        
        try:
            # Create a job in the database
            job = await self.job_queue.create_job(
                request_id=request.request_id,
                user_id=request.user_id,
                job_type="transcription",
                parameters=request.dict(),
            )
            
            # Read audio data if a file is provided
            audio_data = await audio_file.read() if audio_file else None
            
            # Submit the job to Celery
            task = process_audio_async.delay(
                request_data=request.dict(),
                audio_data=audio_data,
            )
            
            # Update the job with the Celery task ID
            await self.job_queue.update_job(request.request_id, task_id=task.id)
            
            logger.info(f"Transcription job {request.request_id} submitted with task ID {task.id}")
            
            return request.request_id
            
        except Exception as e:
            logger.error(f"Failed to submit transcription job: {e}", exc_info=True)
            # Mark job as failed if submission fails
            if 'job' in locals() and job:
                await self.job_queue.update_job(str(job.request_id), status=JobStatus.FAILED, error=str(e))
            raise
