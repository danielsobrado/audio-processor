# Audio Processor Project Overview

## Purpose
Advanced audio processing application focused on:
- **Multilingual Transcription** (English and Arabic)
- **Speaker Diarization** (identify and separate speakers)
- **Audio Summarization** (generate concise summaries)
- **Translation** (translate transcribed content)

## Key Features
- Asynchronous processing with Celery job queue
- RESTful API with FastAPI
- Deepgram API compatibility using WhisperX
- Containerized deployment (Docker + Kubernetes)
- Database integration with PostgreSQL
- Redis for caching and task brokering

## Tech Stack
- **Backend**: Python 3.9+, FastAPI
- **Audio Processing**: WhisperX, Deepgram SDK
- **Task Queue**: Celery, Redis
- **Database**: PostgreSQL, SQLAlchemy, Alembic
- **Testing**: Pytest
- **Containerization**: Docker
- **Orchestration**: Kubernetes

## Architecture Pattern
- **Service Layer Architecture** with clean separation of concerns
- **Async/await** patterns throughout
- **Dependency injection** for services
- **Repository pattern** for database access
- **Background task processing** with Celery
- **Feature flags** for configuration control