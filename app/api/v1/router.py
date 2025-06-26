"""
API router for version 1 of the audio processing microservice.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import health, results, status, transcribe

api_router = APIRouter()

api_router.include_router(transcribe.router, tags=["Transcription"])
api_router.include_router(status.router, tags=["Job Status"])
api_router.include_router(results.router, tags=["Job Results"])
api_router.include_router(health.router, tags=["Health"])
