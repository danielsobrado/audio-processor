"""User CRUD operations."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.crud.base import CRUDBase
from app.schemas.api import UserCreateRequest, UserUpdateRequest
from app.schemas.database import User


class CRUDUser(CRUDBase):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> User | None:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()

    async def create(
        self, db: AsyncSession, *, obj_in: UserCreateRequest, hashed_password: str
    ) -> User:
        db_obj = User(
            email=obj_in.email,
            full_name=obj_in.full_name,
            hashed_password=hashed_password,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def create_from_token(self, db: AsyncSession, *, token_data) -> User:
        """Create a new user from JWT token data (JIT Provisioning)."""
        db_obj = User(
            email=token_data.email,
            full_name=token_data.username,
            is_active=True,
            # hashed_password is nullable, so we don't set it for JIT provisioned users
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: User,
        obj_in: UserUpdateRequest | dict[str, Any],
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


user = CRUDUser(User)
