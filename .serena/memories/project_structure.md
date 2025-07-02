# Project Structure and Organization

## Top-Level Structure
```
audio-processor/
├── app/                    # Main application code
├── config/                 # Configuration files
├── deployment/             # Docker and Kubernetes manifests
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── tests/                  # Test files
├── .env.example           # Environment variables template
├── .gitignore            # Git ignore rules
├── alembic.ini           # Database migration config
├── requirements.txt      # Python dependencies
└── README.md            # Project documentation
```

## Application Structure (app/)
```
app/
├── api/                   # API layer
│   └── v1/
│       └── endpoints/     # API endpoints (health, results, status, transcribe)
├── config/               # Application configuration
│   ├── logging.py       # Logging setup
│   └── settings.py      # Pydantic settings classes
├── core/                 # Core business logic
│   ├── audio_processor.py    # Main audio processing
│   ├── deepgram_formatter.py # Deepgram API compatibility
│   └── job_queue.py         # Job queue management
├── db/                   # Database layer
│   ├── base.py          # SQLAlchemy base
│   ├── models.py        # Database models
│   └── session.py       # Database session
├── services/             # Service layer
│   ├── cache.py         # Redis caching service
│   ├── diarization.py   # Speaker diarization
│   ├── summarization.py # Text summarization
│   ├── transcription.py # Transcription orchestration
│   └── translation.py   # Translation service
├── utils/                # Utilities
│   ├── audio_utils.py   # Audio file processing
│   ├── constants.py     # Application constants
│   ├── error_handlers.py # Error handling
│   └── validators.py    # Input validation
├── workers/              # Background tasks
│   ├── celery_app.py    # Celery configuration
│   └── tasks.py         # Celery task definitions
└── main.py              # FastAPI application factory
```

## Test Structure
```
tests/
├── fixtures/             # Test data and fixtures
│   └── audio_samples/   # Sample audio files
├── integration/         # Integration tests
└── unit/               # Unit tests
```

## Deployment Structure
```
deployment/
├── docker/              # Docker configuration
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── Dockerfile.gpu
└── kubernetes/          # Kubernetes manifests
    ├── configmap.yaml
    ├── deployment.yaml
    ├── service.yaml
    └── ingress.yaml
```