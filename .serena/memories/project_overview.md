# Audio Processor Project Overview

## Purpose
Advanced audio processing application focused on:
- **Multilingual Transcription** (English and Arabic)
- **Speaker Diarization** (identify and separate speakers)
- **Audio Summarization** (generate concise summaries)
- **Translation** (translate transcribed content)
- **Graph-based Conversation Analysis** (speaker networks, topic flows, entity extraction)

## Key Features
- Asynchronous processing with Celery job queue
- RESTful API with FastAPI
- Deepgram API compatibility using WhisperX
- **Graph Database Integration** with Neo4j for conversation analysis
- **Speaker Network Analysis** (interaction patterns, speaking time)
- **Topic Flow Tracking** (conversation transitions, keyword extraction)
- **Entity Extraction** (emails, phones, dates, URLs, mentions)
- Containerized deployment (Docker + Kubernetes)
- Database integration with PostgreSQL
- Redis for caching and task brokering

## Tech Stack
- **Backend**: Python 3.12+, FastAPI
- **Audio Processing**: WhisperX, Deepgram SDK
- **Task Queue**: Celery, Redis
- **Database**: PostgreSQL, SQLAlchemy, Alembic
- **Graph Database**: Neo4j
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
- **Optional graph processing** with graceful degradation
