"""API request and response models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Request Models
class TranscriptionRequest(BaseModel):
    """Request model for transcription job submissions."""

    request_id: str = Field(..., description="Unique request identifier")
    user_id: int = Field(..., description="User identifier")
    audio_url: str | None = Field(None, description="URL to audio file")
    language: str | None = Field("auto", description="Language code or 'auto'")
    model: str | None = Field("base", description="Transcription model size")
    include_diarization: bool = Field(False, description="Enable speaker diarization")
    include_summarization: bool = Field(False, description="Enable text summarization")
    include_translation: bool = Field(False, description="Enable translation")
    target_language: str | None = Field(None, description="Target language for translation")


class UserCreateRequest(BaseModel):
    """Request model for creating a new user."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class UserUpdateRequest(BaseModel):
    """Request model for updating a user's profile."""

    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None


# Response Models
class JobStatusResponse(BaseModel):
    """Response model for job status queries."""

    request_id: str
    status: str
    created: datetime
    updated: datetime
    progress: float | None = None
    error: str | None = None


class JobResponse(BaseModel):
    """Detailed job response model for admin operations."""

    request_id: str
    user_id: str
    status: str
    progress: float
    created: datetime
    updated: datetime
    result: dict[str, Any] | None = None
    error: str | None = None
    task_id: str | None = None
    job_type: str | None = None
    parameters: dict[str, Any] | None = None


class AdminJobListResponse(BaseModel):
    """Response model for admin job listing."""

    jobs: list[JobResponse]
    total_count: int
    limit: int
    offset: int


class AdminJobRequeueRequest(BaseModel):
    """Request model for requeuing a job."""

    reason: str | None = Field(None, description="Reason for requeuing the job")


class AdminJobRequeueResponse(BaseModel):
    """Response model for job requeue operation."""

    request_id: str
    new_task_id: str
    status: str
    message: str


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
    segments: list[dict[str, Any]]
    metadata: dict[str, Any]
    summary: str | None = None
    translation: str | None = None


class GraphStatsResponse(BaseModel):
    """Response model for graph statistics."""

    enabled: bool
    stats: dict[str, Any]


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
    speakers: list[str]
    topics: list[str]
    entities: list[str]
    interactions: list[dict[str, Any]]
    metadata: dict[str, Any]


class SpeakerNetworkResponse(BaseModel):
    """Response model for speaker network."""

    speaker_id: str
    name: str
    direct_interactions: list[dict[str, Any]]
    network_stats: dict[str, Any]


class TopicFlowResponse(BaseModel):
    """Response model for topic flow."""

    topic_id: str
    name: str
    flow_patterns: list[dict[str, Any]]
    keywords: list[str]
    usage_stats: dict[str, Any]


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    timestamp: datetime
    services: dict[str, str]
    version: str


# New User Management Models
class UserResponse(BaseModel):
    """Response model for user information."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None


# Enhanced Graph Models
class SpeakerProfileResponse(BaseModel):
    """Response model for a detailed speaker profile."""

    speaker_id: str
    name: str
    voice_characteristics: dict[str, Any]
    conversation_count: int
    total_speaking_time: float
    avg_speaking_time: float
    total_turns: int
    topics_discussed: list[str]


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
    keywords: list[str]
    confidence_score: float
    speaker_count: int
    conversation_count: int
    total_mentions: int
    avg_relevance: float
    discussing_speakers: list[str]


class TrendingTopicResponse(BaseModel):
    """Response model for a trending topic."""

    topic_id: str
    topic_name: str
    keywords: list[str]
    unique_speakers: int
    total_mentions: int
    avg_relevance: float


class TopicCooccurrenceResponse(BaseModel):
    """Response model for topic co-occurrence."""

    cooccurring_topic_id: str
    cooccurring_topic_name: str
    cooccurrence_count: int
    avg_time_distance: float
