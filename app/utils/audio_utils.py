"""
Audio processing utilities.
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import HTTPException, UploadFile, status

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def validate_audio_file(file: UploadFile) -> None:
    """
    Validate uploaded audio file.
    
    Args:
        file: Uploaded audio file.
    
    Raises:
        HTTPException: If file is invalid.
    """
    
    # Check file size
    if file.size is None or file.size > settings.max_file_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds limit of {settings.max_file_size / 1024 / 1024:.2f} MB",
        )
    
    # Check content type
    supported_formats = settings.supported_formats
    if isinstance(supported_formats, str):
        supported_formats = [supported_formats]

    if file.content_type is None or file.content_type not in supported_formats:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio format. Supported formats: {settings.supported_formats}",
        )


async def save_temp_audio_file(file: UploadFile) -> Path:
    """
    Save uploaded audio file to a temporary location.
    
    Args:
        file: Uploaded audio file.
    
    Returns:
        Path to the temporary file.
    """
    
    temp_dir = Path(settings.temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # Secure filename handling to prevent path traversal attacks
    safe_filename = f"{uuid.uuid4()}_{os.path.basename(file.filename or 'audio_file')}"
    temp_path = temp_dir / safe_filename
    
    try:
        async with aiofiles.open(temp_path, "wb") as temp_file:
            while chunk := await file.read(1024 * 1024):  # Read in 1MB chunks
                await temp_file.write(chunk)
        
        logger.info(f"Saved temporary audio file: {temp_path}")
        return temp_path
        
    except Exception as e:
        logger.error(f"Failed to save temporary file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save temporary audio file",
        )


async def convert_audio_format(
    input_path: Path,
    output_path: Path,
    target_format: str = "wav",
    sample_rate: int = 16000,
    channels: int = 1,
) -> None:
    """
    Convert audio file to a different format using pydub.
    
    Args:
        input_path: Path to the input audio file.
        output_path: Path to save the converted audio file.
        target_format: Target audio format (e.g., "wav", "mp3").
        sample_rate: Target sample rate.
        channels: Target number of channels.
    """
    
    try:
        from pydub import AudioSegment
        
        # Load audio file
        audio = AudioSegment.from_file(input_path)
        
        # Set channels and sample rate
        audio = audio.set_channels(channels)
        audio = audio.set_frame_rate(sample_rate)
        
        # Export to target format
        audio.export(output_path, format=target_format)
        
        logger.info(f"Converted {input_path} to {output_path} ({target_format})")
        
    except ImportError:
        logger.error("pydub is not installed. Please install it for audio conversion.")
        raise
    except Exception as e:
        logger.error(f"Audio conversion failed: {e}", exc_info=True)
        raise


def get_audio_duration(audio_path: Path) -> float:
    """
    Get the duration of an audio file in seconds.
    
    Args:
        audio_path: Path to the audio file.
    
    Returns:
        Duration in seconds.
    """
    
    try:
        from pydub import AudioSegment
        
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0  # Duration in seconds
        
    except ImportError:
        logger.error("pydub is not installed. Please install it to get audio duration.")
        return 0.0
    except Exception as e:
        logger.error(f"Failed to get audio duration: {e}", exc_info=True)
        return 0.0
