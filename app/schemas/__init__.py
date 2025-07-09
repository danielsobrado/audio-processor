"""Models package initialization and exports."""

# Database models
# API models
from app.schemas.api import (
    ConversationGraphResponse,
    GraphStatsResponse,
    HealthResponse,
    JobStatusResponse,
    SpeakerNetworkResponse,
    SpeakerResponse,
    TopicFlowResponse,
    TopicResponse,
    TranscriptionRequest,
    TranscriptionResponse,
    TranscriptionResult,
)
from app.schemas.database import JobStatus, TranscriptionJob, User

# Graph models
from app.schemas.graph import (
    ConversationNode,
    DiscussesRelationship,
    EntityNode,
    FollowsRelationship,
    GraphNode,
    GraphRelationship,
    MentionsRelationship,
    NodeType,
    RelationshipType,
    SpeakerNode,
    SpeaksInRelationship,
    TopicNode,
    TranscriptSegmentNode,
)

__all__ = [
    # Database models
    "User",
    "TranscriptionJob",
    "JobStatus",
    # Graph models
    "NodeType",
    "RelationshipType",
    "GraphNode",
    "SpeakerNode",
    "TopicNode",
    "EntityNode",
    "ConversationNode",
    "TranscriptSegmentNode",
    "GraphRelationship",
    "SpeaksInRelationship",
    "DiscussesRelationship",
    "MentionsRelationship",
    "FollowsRelationship",
    # API models
    "TranscriptionRequest",
    "TranscriptionResponse",
    "TranscriptionResult",
    "JobStatusResponse",
    "GraphStatsResponse",
    "SpeakerResponse",
    "TopicResponse",
    "ConversationGraphResponse",
    "SpeakerNetworkResponse",
    "TopicFlowResponse",
    "HealthResponse",
]
