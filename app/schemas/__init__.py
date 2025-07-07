"""Models package initialization and exports."""

# Database models
from app.schemas.database import (
    User,
    TranscriptionJob,
    JobStatus,
)

# Graph models
from app.schemas.graph import (
    NodeType,
    RelationshipType,
    GraphNode,
    SpeakerNode,
    TopicNode,
    EntityNode,
    ConversationNode,
    TranscriptSegmentNode,
    GraphRelationship,
    SpeaksInRelationship,
    DiscussesRelationship,
    MentionsRelationship,
    FollowsRelationship,
)

# API models
from app.schemas.api import (
    TranscriptionRequest,
    TranscriptionResponse,
    TranscriptionResult,
    JobStatusResponse,
    GraphStatsResponse,
    SpeakerResponse,
    TopicResponse,
    ConversationGraphResponse,
    SpeakerNetworkResponse,
    TopicFlowResponse,
    HealthResponse,
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
