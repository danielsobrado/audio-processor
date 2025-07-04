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


@router.get("/health", summary="Perform a health check")
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
    
    # In a real application, you would also check other dependencies
    # like Celery, etc.
    
    if any(status == "error" for status in dependencies.values()):
        raise HTTPException(status_code=503, detail={"status": "error", "dependencies": dependencies})
    
    return {"status": "ok", "dependencies": dependencies}
