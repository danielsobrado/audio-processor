"""
Application-wide constants.
"""

# Audio processing constants
AUDIO_SAMPLE_RATE = 16000  # Standard sample rate for Whisper models
AUDIO_CHANNELS = 1  # Mono audio
AUDIO_BIT_DEPTH = 16  # 16-bit audio
LANGUAGE_DETECTION_DURATION_S = 30  # Seconds of audio to use for language detection
LONG_AUDIO_WARNING_S = 3600  # 1 hour in seconds, for audio quality warnings
MIN_PROCESSING_TIME_S = 5.0  # Minimum estimated processing time in seconds

# File size limits
MAX_UPLOAD_FILE_SIZE_MB = 100
MAX_UPLOAD_FILE_SIZE_BYTES = MAX_UPLOAD_FILE_SIZE_MB * 1024 * 1024

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = ["wav", "mp3", "m4a", "flac", "ogg", "opus"]

# Job status/type messages
JOB_STATUS_QUEUED = "queued"
JOB_STATUS_PROCESSING = "processing"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_TYPE_TRANSCRIPTION = "transcription"

# Default model names
DEFAULT_WHISPER_MODEL = "large-v2"
DEFAULT_DIARIZATION_MODEL = "pyannote/speaker-diarization"

# API versions
API_V1_PREFIX = "/api/v1"

# Temporary directory
DEFAULT_TEMP_DIR = "/tmp/audio_processor"

# Default pagination and limits
DEFAULT_API_LIMIT = 50
MAX_API_LIMIT = 500
DEFAULT_API_OFFSET = 0

# Heuristics & Defaults
DEFAULT_HIGH_CONFIDENCE = 0.8
DEFAULT_LOW_CONFIDENCE = 0.6
DEFAULT_CONFIDENCE_WORD_COUNT_THRESHOLD = 5
DEFAULT_LANGUAGE = "auto"
DEFAULT_UTT_SPLIT = 0.8

# Celery Queues
CELERY_DEFAULT_QUEUE = "default"
CELERY_DLQ_NAME = "dead_letter"
