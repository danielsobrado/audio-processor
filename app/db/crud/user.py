"""User CRUD operations."""

from typing import Any, Dict, Optional, Union

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash
from app.db.crud.base import CRUDBase
from app.schemas.api import UserCreateRequest, UserUpdateRequest
from app.schemas.database import User


class CRUDUser(CRUDBase):
    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[User]:
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, *, obj_in: UserCreateRequest, hashed_password: str) -> User:
        db_obj = User(
            email=obj_in.email,
            full_name=obj_in.full_name,
            hashed_password=hashed_password,
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
        obj_in: Union[UserUpdateRequest, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


user = CRUDUser(User)
