"""
API Response Models

Defines Pydantic models for API response contracts, ensuring type safety
and automatic documentation generation.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobStatusResponse(BaseModel):
    """Response model for job status queries."""
    
    request_id: str
    status: str
    created: datetime
    updated: datetime
    progress: Optional[float] = None
    error: Optional[str] = None


class TranscriptionResponse(BaseModel):
    """Response model for transcription job submissions."""
    
    request_id: str
    status: str
    created: datetime
    message: str


class TranscriptionRequest(BaseModel):
    """Request model for transcription job submissions."""
    
    # TODO: Define request fields based on endpoint requirements
    # This requires analysis of actual endpoint parameter usage
    pass
