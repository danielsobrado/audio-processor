from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings

# Synchronous database setup
engine = create_engine(get_settings().database.url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async database setup for hybrid compatibility
async_engine = create_async_engine(
    get_settings().database.url.replace("postgresql://", "postgresql+asyncpg://")
)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


class DatabaseService:
    """Database service providing session management and lifecycle."""

    def __init__(self):
        self.engine = engine
        self.async_engine = async_engine
        self.SessionLocal = SessionLocal
        self.AsyncSessionLocal = AsyncSessionLocal

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get synchronous database session with proper cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get asynchronous database session with proper cleanup."""
        session = self.AsyncSessionLocal()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    def create_tables(self):
        """Create database tables."""
        from app.db.base import Base

        Base.metadata.create_all(bind=self.engine)

    async def create_tables_async(self):
        """Create database tables asynchronously."""
        from app.db.base import Base

        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def close(self):
        """Close database connections."""
        self.engine.dispose()

    async def close_async(self):
        """Close async database connections."""
        await self.async_engine.dispose()


# Service instance
_database_service = DatabaseService()


def get_database() -> DatabaseService:
    """Get database service instance."""
    return _database_service


def get_session() -> Generator[Session, None, None]:
    """Synchronous dependency injection for database sessions."""
    with _database_service.get_session() as session:
        yield session


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Asynchronous dependency injection for database sessions."""
    async with _database_service.get_async_session() as session:
        yield session
