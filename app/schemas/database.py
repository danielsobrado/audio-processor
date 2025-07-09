"""Database models for SQLAlchemy."""

from enum import Enum as PyEnum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class JobStatus(PyEnum):
    """Job status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    # Make hashed_password nullable to support users created via JWT token (JIT provisioning)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transcription_jobs = relationship("TranscriptionJob", back_populates="user")


class TranscriptionJob(Base):
    """Transcription job model."""

    __tablename__ = "transcription_jobs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Job details
    status = Column(Enum(JobStatus), default=JobStatus.PENDING)
    progress = Column(Float, default=0.0, nullable=False)
    audio_url = Column(String, nullable=True)
    audio_filename = Column(String, nullable=True)

    # Task management
    task_id = Column(String, nullable=True, index=True)
    job_type = Column(String, default="transcription", nullable=False)

    # Configuration
    language = Column(String, nullable=True)
    model = Column(String, nullable=True)
    include_diarization = Column(Boolean, default=False)
    include_summarization = Column(Boolean, default=False)
    include_translation = Column(Boolean, default=False)
    parameters = Column(JSON, nullable=True)

    # Results (unified field names for API consistency)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)

    # Legacy fields (keep for backward compatibility during migration)
    transcription_result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="transcription_jobs")
