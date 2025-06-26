"""
Database models for the audio processing microservice.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class JobStatus(str, Enum):
    """Enumeration for transcription job statuses."""
    
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    jobs = relationship("TranscriptionJob", back_populates="user")


class TranscriptionJob(Base):
    """Transcription job model."""
    
    __tablename__ = "transcription_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String(36), unique=True, index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Job details
    job_type = Column(String(50), nullable=False, default="transcription")
    status = Column(String(20), nullable=False, default=JobStatus.QUEUED)
    task_id = Column(String(36), unique=True, nullable=True)  # Celery task ID
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Job parameters
    parameters = Column(JSON, nullable=True)
    
    # Progress and results
    progress = Column(Float, default=0.0)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="jobs")
