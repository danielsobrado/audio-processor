"""
Integration tests for database interactions.
"""

import pytest
from sqlalchemy.future import select

from app.schemas.database import TranscriptionJob, User
from app.db.session import get_database


@pytest.mark.asyncio
async def test_create_user():
    """Test creating a new user."""
    db = get_database()
    async with db.get_async_session() as session:
        user = User(email="test@example.com", full_name="Test User")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        
        # Clean up
        await session.delete(user)
        await session.commit()


@pytest.mark.asyncio
async def test_create_and_retrieve_job():
    """Test creating and retrieving a transcription job."""
    db = get_database()
    async with db.get_async_session() as session:
        # Create a dummy user first
        user = User(email="job@example.com", full_name="Job User")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        job = TranscriptionJob(
            request_id="job-123",
            user_id=user.id,
            job_type="transcription",
            parameters={"audio_url": "http://audio.com/file.mp3"},
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        
        assert job.id is not None
        assert job.request_id == "job-123"
        assert job.user_id == user.id
        
        retrieved_job = await session.execute(
            select(TranscriptionJob).where(TranscriptionJob.request_id == "job-123")
        )
        retrieved_job = retrieved_job.scalar_one_or_none()
        
        assert retrieved_job is not None
        assert retrieved_job.request_id == "job-123"
        
        # Clean up
        await session.delete(job)
        await session.delete(user)
        await session.commit()
