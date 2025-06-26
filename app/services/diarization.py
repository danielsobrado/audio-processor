"""
Diarization service for speaker identification.
"""

import logging
from typing import Dict, List

from app.core.audio_processor import AudioProcessor

logger = logging.getLogger(__name__)


class DiarizationService:
    """
    Service for performing speaker diarization on audio files.
    """
    
    def __init__(self, audio_processor: AudioProcessor):
        self.audio_processor = audio_processor
    
    async def diarize_audio(self, audio_path: str) -> List[Dict]:
        """
        Perform speaker diarization on an audio file.
        
        Args:
            audio_path: The path to the audio file.
        
        Returns:
            A list of segments with speaker labels.
        """
        
        try:
            logger.info(f"Performing diarization on {audio_path}")
            
            # This is a simplified example. In a real application,
            # you would call a specific diarization method on the audio_processor.
            result = await self.audio_processor.process_audio(
                audio_path=audio_path,
                diarize=True,
                align=False,  # No need for alignment for pure diarization
            )
            
            return result.get("segments", [])
            
        except Exception as e:
            logger.error(f"Diarization failed for {audio_path}: {e}", exc_info=True)
            raise
