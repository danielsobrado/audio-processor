"""
Diarization service for speaker identification.
"""

import logging
from pathlib import Path

from app.core.audio_processor import AudioProcessor
from app.utils.error_handlers import AudioProcessingError

logger = logging.getLogger(__name__)


class DiarizationService:
    """
    Service for performing speaker diarization on audio files.
    """

    def __init__(self, audio_processor: AudioProcessor):
        self.audio_processor = audio_processor

    async def diarize_audio(self, audio_path: Path) -> list[dict]:
        """
        Perform speaker diarization on an audio file.

        Args:
            audio_path: The path to the audio file.

        Returns:
            A list of segments, each with an assigned speaker label.

        Raises:
            AudioProcessingError: If the underlying audio processing fails.
        """
        try:
            logger.info(f"Performing diarization on {audio_path}")
            result = await self.audio_processor.process_audio(
                audio_path=audio_path,
                diarize=True,
                align=False,  # No need for alignment for pure diarization
            )
            return result.get("segments", [])
        except Exception as e:
            logger.error(f"Diarization failed for {audio_path}: {e}", exc_info=True)
            raise AudioProcessingError(f"Diarization failed: {e}")
