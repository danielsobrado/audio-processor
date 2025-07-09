"""
API endpoints for user management.
"""

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_roles
from app.core.security import get_password_hash
from app.db.session import get_async_session
from app.schemas.api import UserCreateRequest, UserResponse, UserUpdateRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Public endpoint to register a new user.",
)
async def create_user(
    user_in: UserCreateRequest,
    db: AsyncSession = Depends(get_async_session),
):
    """Create a new user in the database."""
    try:
        # Import here to avoid circular imports
        from app.db import crud

        db_user = await crud.user.get_by_email(db, email=user_in.email)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists.",
            )

        hashed_password = get_password_hash(user_in.password)
        created_user = await crud.user.create(
            db, obj_in=user_in, hashed_password=hashed_password
        )
        return created_user
    except ImportError:
        logger.error("CRUD module not available - user creation disabled")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="User management not implemented yet",
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get the profile of the currently authenticated user.",
)
async def read_current_user(
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    """
    Returns the profile of the currently authenticated user.
    If the user exists in the JWT but not in the local database,
    a local profile is created automatically (Just-In-Time Provisioning).
    """
    try:
        # Import here to avoid circular imports
        from app.db import crud

        # Look for the user in our local database by email from the token
        db_user = await crud.user.get_by_email(db, email=current_user.email)

        if not db_user:
            # User is authenticated but doesn't have a local profile yet.
            # Create one now (JIT Provisioning).
            logger.info(
                f"User '{current_user.email}' not found locally. Provisioning new user."
            )
            db_user = await crud.user.create_from_token(db, token_data=current_user)

        return db_user
    except ImportError:
        logger.error("CRUD module not available - database configuration error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database configuration error - unable to process user data",
        )


@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update the profile of the currently authenticated user.",
)
async def update_current_user(
    user_in: UserUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user=Depends(get_current_user),
):
    """Update the current user's full name or active status."""
    try:
        # Import here to avoid circular imports
        from app.db import crud

        # Get current user from database or create if not exists (JIT Provisioning)
        db_user = await crud.user.get_by_email(db, email=current_user.email)
        if not db_user:
            logger.info(
                f"User '{
                    current_user.email}' not found locally. Provisioning new user for update."
            )
            db_user = await crud.user.create_from_token(db, token_data=current_user)

        updated_user = await crud.user.update(db, db_obj=db_user, obj_in=user_in)
        return updated_user
    except ImportError:
        logger.error("CRUD module not available - user update disabled")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="User management not implemented yet",
        )


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List all users (Admin only)",
    dependencies=[Depends(require_roles(["admin"]))],
)
async def list_users(
    db: AsyncSession = Depends(get_async_session),
    skip: int = 0,
    limit: int = 100,
):
    """Retrieve a list of all users. Requires 'admin' role."""
    try:
        # Import here to avoid circular imports
        from app.db import crud

        users = await crud.user.get_multi(db, skip=skip, limit=limit)
        return users
    except ImportError:
        logger.error("CRUD module not available - user listing disabled")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="User management not implemented yet",
        )
