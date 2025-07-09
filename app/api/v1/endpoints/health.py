"""
API endpoint for health checks.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_cache_service
from app.db.session import get_async_session
from app.services.cache import CacheService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=None, summary="Perform a health check")
async def health_check(
    session: AsyncSession = Depends(get_async_session),
    cache_service: CacheService = Depends(get_cache_service),
):
    """
    Checks the health of the service and its dependencies.
    """
    dependencies = {}

    try:
        # Check database connection
        await session.execute(text("SELECT 1"))
        dependencies["database"] = "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        dependencies["database"] = "error"

    try:
        # Check Redis connection
        await cache_service.redis_client.ping()
        dependencies["redis"] = "ok"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        dependencies["redis"] = "error"

    # Check Celery broker and workers
    try:
        from app.workers.celery_app import celery_app

        # Check Celery broker connection (Redis)
        broker_info = celery_app.control.inspect().stats()
        if broker_info:
            dependencies["celery_broker"] = "ok"

            # Check active workers
            active_workers = list(broker_info.keys())
            worker_count = len(active_workers)

            if worker_count > 0:
                dependencies["celery_workers"] = "ok"
                dependencies["worker_count"] = worker_count
                dependencies["active_workers"] = active_workers
            else:
                dependencies["celery_workers"] = "warning"
                dependencies["worker_count"] = 0
                dependencies["active_workers"] = []
                logger.warning("No active Celery workers found")
        else:
            dependencies["celery_broker"] = "error"
            dependencies["celery_workers"] = "error"
            dependencies["worker_count"] = 0
            logger.error("Unable to connect to Celery broker")

    except Exception as e:
        logger.error(f"Celery health check failed: {e}")
        dependencies["celery_broker"] = "error"
        dependencies["celery_workers"] = "error"
        dependencies["worker_count"] = 0

    # Determine overall status
    has_errors = any(status == "error" for status in dependencies.values())
    has_warnings = any(status == "warning" for status in dependencies.values())

    if has_errors:
        raise HTTPException(
            status_code=503, detail={"status": "error", "dependencies": dependencies}
        )
    elif has_warnings:
        return {"status": "warning", "dependencies": dependencies}
    else:
        return {"status": "ok", "dependencies": dependencies}
