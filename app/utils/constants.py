"""
Application-wide constants.
"""

# Audio processing constants
AUDIO_SAMPLE_RATE = 16000  # Standard sample rate for Whisper models
AUDIO_CHANNELS = 1        # Mono audio
AUDIO_BIT_DEPTH = 16      # 16-bit audio

# File size limits
MAX_UPLOAD_FILE_SIZE_MB = 100
MAX_UPLOAD_FILE_SIZE_BYTES = MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = ["wav", "mp3", "m4a", "flac", "ogg", "opus"]

# Job status messages
JOB_STATUS_QUEUED = "queued"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"

# Default model names
DEFAULT_WHISPER_MODEL = "large-v2"
DEFAULT_DIARIZATION_MODEL = "pyannote/speaker-diarization"

# API versions
API_V1_PREFIX = "/api/v1"

# Temporary directory
DEFAULT_TEMP_DIR = "/tmp/audio_processor"
