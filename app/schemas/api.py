"""API request and response models."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


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


class UserCreateRequest(BaseModel):
    """Request model for creating a new user."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserUpdateRequest(BaseModel):
    """Request model for updating a user's profile."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


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


# New User Management Models
class UserResponse(BaseModel):
    """Response model for user information."""
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Enhanced Graph Models
class SpeakerProfileResponse(BaseModel):
    """Response model for a detailed speaker profile."""
    speaker_id: str
    name: str
    voice_characteristics: Dict[str, Any]
    conversation_count: int
    total_speaking_time: float
    avg_speaking_time: float
    total_turns: int
    topics_discussed: List[str]


class TopSpeakerResponse(BaseModel):
    """Response model for a top speaker entry."""
    speaker_id: str
    speaker_name: str
    conversation_count: int
    total_speaking_time: float
    total_turns: int
    avg_speaking_time: float


class SimilarSpeakerResponse(BaseModel):
    """Response model for a similar speaker entry."""
    speaker_id: str
    speaker_name: str
    similarity_score: float
    avg_segment_duration: float


class TopicProfileResponse(BaseModel):
    """Response model for a detailed topic profile."""
    topic_id: str
    name: str
    keywords: List[str]
    confidence_score: float
    speaker_count: int
    conversation_count: int
    total_mentions: int
    avg_relevance: float
    discussing_speakers: List[str]


class TrendingTopicResponse(BaseModel):
    """Response model for a trending topic."""
    topic_id: str
    topic_name: str
    keywords: List[str]
    unique_speakers: int
    total_mentions: int
    avg_relevance: float


class TopicCooccurrenceResponse(BaseModel):
    """Response model for topic co-occurrence."""
    cooccurring_topic_id: str
    cooccurring_topic_name: str
    cooccurrence_count: int
    avg_time_distance: float
