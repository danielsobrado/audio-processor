"""
Audio Processing Microservice - Main FastAPI Application
Compatible with Omi backend architecture using PostgreSQL, Keycloak OAuth, and Kubernetes.
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.config.logging import setup_logging
from app.config.settings import get_settings
from app.core.job_queue import JobQueue
from app.db.session import get_database
from app.utils.error_handlers import (
    audio_processing_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)


# Initialize settings
settings = get_settings()

# Setup logging
setup_logging(settings.log_level, settings.environment)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info("Starting Audio Processing Microservice")
    
    # Initialize database connection
    try:
        db = get_database()
        await db.create_tables_async()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    
    # Initialize job queue
    try:
        job_queue = JobQueue()
        await job_queue.initialize()
        app.state.job_queue = job_queue
        logger.info("Job queue initialized")
    except Exception as e:
        logger.error(f"Job queue initialization failed: {e}")
        sys.exit(1)
    
    # Initialize graph database connection
    try:
        from app.db.graph_session import graph_db_manager
        
        if settings.graph.enabled:
            await graph_db_manager.initialize()
            logger.info("Graph database connection established")
        else:
            logger.info("Graph processing is disabled")
    except Exception as e:
        logger.warning(f"Graph database initialization failed: {e}")
        # Don't exit if graph database fails, just log the warning
    
    # Download required models
    try:
        from app.core.audio_processor import AudioProcessor
        processor = AudioProcessor()
        await processor.initialize_models()
        app.state.audio_processor = processor
        logger.info("Audio processing models loaded")
    except Exception as e:
        logger.error(f"Model initialization failed: {e}")
        sys.exit(1)
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Audio Processing Microservice")
    
    # Cleanup resources
    if hasattr(app.state, 'audio_processor'):
        await app.state.audio_processor.cleanup()
    
    if hasattr(app.state, 'job_queue'):
        await app.state.job_queue.cleanup()
    
    # Close graph database connection
    try:
        from app.db.graph_session import graph_db_manager
        await graph_db_manager.shutdown()
        logger.info("Graph database connection closed")
    except Exception as e:
        logger.warning(f"Graph database shutdown failed: {e}")
    
    # Close database connections
    if db:
        await db.close()
    
    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Audio Processing Microservice",
        description="Deepgram-compatible audio processing with WhisperX, diarization, and translation",
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        openapi_url="/openapi.json" if settings.environment != "production" else None,
        lifespan=lifespan,
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add exception handlers
    setup_exception_handlers(app)
    
    # Include routers
    app.include_router(api_router, prefix="/api")
    
    return app


def setup_middleware(app: FastAPI) -> None:
    """Configure application middleware."""
    
    # Trusted hosts
    if settings.allowed_hosts:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts,
        )
    
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    # Request logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(
            "Request started",
            extra={
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent"),
            }
        )
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "url": str(request.url),
                "status_code": response.status_code,
                "process_time": f"{process_time:.3f}s",
            }
        )
        
        return response


def setup_exception_handlers(app: FastAPI) -> None:
    """Configure global exception handlers."""
    
    from fastapi import HTTPException
    from pydantic import ValidationError
    from app.utils.error_handlers import AudioProcessingError
    
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(AudioProcessingError, audio_processing_exception_handler)
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.error(
            "Unhandled exception",
            extra={
                "url": str(request.url),
                "method": request.method,
                "error": str(exc),
            },
            exc_info=True,
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": "An unexpected error occurred",
            }
        )


# Create application instance
app = create_application()


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Root endpoint for health checks."""
    return {
        "service": "Audio Processing Microservice",
        "status": "healthy",
        "version": "1.0.0",
    }


if __name__ == "__main__":
    import time
    
    uvicorn.run(
        "app.main:app",
        host=settings.host or "0.0.0.0",
        port=settings.port or 8000,
        reload=settings.environment == "development",
        log_config=None,  # Use our custom logging
        access_log=False,  # Handled by middleware
    )