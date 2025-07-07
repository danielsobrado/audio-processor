"""API request and response models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# Request Models
class TranscriptionRequest(BaseModel):
    """Request model for transcription job submissions."""
    
    request_id: str = Field(..., description="Unique request identifier")
    user_id: str = Field(..., description="User identifier")
    audio_url: Optional[str] = Field(None, description="URL to audio file")
    language: Optional[str] = Field("auto", description="Language code or 'auto'")
    model: Optional[str] = Field("base", description="Transcription model size")
    include_diarization: bool = Field(False, description="Enable speaker diarization")
    include_summarization: bool = Field(False, description="Enable text summarization")
    include_translation: bool = Field(False, description="Enable translation")
    target_language: Optional[str] = Field(None, description="Target language for translation")


# Response Models
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


class TranscriptionResult(BaseModel):
    """Complete transcription result."""
    
    request_id: str
    conversation_id: str
    segments: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    summary: Optional[str] = None
    translation: Optional[str] = None


class GraphStatsResponse(BaseModel):
    """Response model for graph statistics."""
    
    enabled: bool
    stats: Dict[str, Any]


class SpeakerResponse(BaseModel):
    """Response model for speaker information."""
    
    speaker_id: str
    name: str
    total_speaking_time: float
    segment_count: int
    conversation_count: int


class TopicResponse(BaseModel):
    """Response model for topic information."""
    
    topic_id: str
    name: str
    keyword_count: int
    conversation_count: int
    relevance_score: float


class ConversationGraphResponse(BaseModel):
    """Response model for conversation graph."""
    
    conversation_id: str
    speakers: List[str]
    topics: List[str]
    entities: List[str]
    interactions: List[Dict[str, Any]]
    metadata: Dict[str, Any]


class SpeakerNetworkResponse(BaseModel):
    """Response model for speaker network."""
    
    speaker_id: str
    name: str
    direct_interactions: List[Dict[str, Any]]
    network_stats: Dict[str, Any]


class TopicFlowResponse(BaseModel):
    """Response model for topic flow."""
    
    topic_id: str
    name: str
    flow_patterns: List[Dict[str, Any]]
    keywords: List[str]
    usage_stats: Dict[str, Any]


class HealthResponse(BaseModel):
    """Response model for health check."""
    
    status: str
    timestamp: datetime
    services: Dict[str, str]
    version: str
