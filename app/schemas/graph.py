"""Neo4j graph models for audio processing domain."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeType(str, Enum):
    """Graph node types."""

    SPEAKER = "Speaker"
    TOPIC = "Topic"
    ENTITY = "Entity"
    CONVERSATION = "Conversation"
    TRANSCRIPT_SEGMENT = "TranscriptSegment"


class RelationshipType(str, Enum):
    """Graph relationship types."""

    SPEAKS_IN = "SPEAKS_IN"
    DISCUSSES = "DISCUSSES"
    MENTIONS = "MENTIONS"
    FOLLOWS = "FOLLOWS"
    CONTAINS = "CONTAINS"
    RELATED_TO = "RELATED_TO"
    INTERRUPTS = "INTERRUPTS"


@dataclass
class GraphNode:
    """Base class for graph nodes."""

    id: str
    node_type: NodeType
    properties: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    def to_cypher_props(self) -> Dict[str, Any]:
        """Convert to Cypher-compatible properties."""
        props = self.properties.copy()
        props.update(
            {
                "id": self.id,
                "node_type": self.node_type.value,
                "created_at": self.created_at.isoformat(),
                "updated_at": self.updated_at.isoformat(),
            }
        )
        return props


@dataclass
class SpeakerNode(GraphNode):
    """Speaker node model."""

    def __init__(
        self,
        speaker_id: str,
        name: Optional[str] = None,
        voice_characteristics: Optional[Dict] = None,
    ):
        super().__init__(
            id=speaker_id,
            node_type=NodeType.SPEAKER,
            properties={
                "name": name or f"Speaker_{speaker_id}",
                "voice_characteristics": voice_characteristics or {},
                "total_speaking_time": 0.0,
                "conversation_count": 0,
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


@dataclass
class TopicNode(GraphNode):
    """Topic node model."""

    def __init__(
        self,
        topic_id: str,
        topic_name: str,
        confidence_score: float,
        keywords: List[str],
    ):
        super().__init__(
            id=topic_id,
            node_type=NodeType.TOPIC,
            properties={
                "name": topic_name,
                "confidence_score": confidence_score,
                "keywords": keywords,
                "mention_count": 0,
                "relevance_score": 0.0,
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


@dataclass
class EntityNode(GraphNode):
    """Named entity node model."""

    def __init__(
        self,
        entity_id: str,
        entity_text: str,
        entity_type: str,
        confidence_score: float,
    ):
        super().__init__(
            id=entity_id,
            node_type=NodeType.ENTITY,
            properties={
                "text": entity_text,
                "entity_type": entity_type,  # PERSON, ORG, LOCATION, etc.
                "confidence_score": confidence_score,
                "mention_count": 0,
                "context_variations": [],
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


@dataclass
class ConversationNode(GraphNode):
    """Conversation/audio session node model."""

    def __init__(
        self, conversation_id: str, audio_file_id: str, duration: float, language: str
    ):
        super().__init__(
            id=conversation_id,
            node_type=NodeType.CONVERSATION,
            properties={
                "audio_file_id": audio_file_id,
                "duration": duration,
                "language": language,
                "speaker_count": 0,
                "topic_count": 0,
                "entity_count": 0,
                "processing_status": "pending",
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


@dataclass
class TranscriptSegmentNode(GraphNode):
    """Transcript segment node model."""

    def __init__(
        self,
        segment_id: str,
        conversation_id: str,
        text: str,
        start_time: float,
        end_time: float,
        speaker_id: str,
        confidence_score: float,
    ):
        super().__init__(
            id=segment_id,
            node_type=NodeType.TRANSCRIPT_SEGMENT,
            properties={
                "conversation_id": conversation_id,
                "text": text,
                "start_time": start_time,
                "end_time": end_time,
                "speaker_id": speaker_id,
                "confidence_score": confidence_score,
                "duration": end_time - start_time,
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )


@dataclass
class GraphRelationship:
    """Base class for graph relationships."""

    from_node_id: str
    to_node_id: str
    relationship_type: RelationshipType
    properties: Dict[str, Any]
    created_at: datetime

    def to_cypher_props(self) -> Dict[str, Any]:
        """Convert to Cypher-compatible properties."""
        props = self.properties.copy()
        props.update(
            {
                "created_at": self.created_at.isoformat(),
                "relationship_type": self.relationship_type.value,
            }
        )
        return props


@dataclass
class SpeaksInRelationship(GraphRelationship):
    """Speaker speaks in conversation."""

    def __init__(
        self,
        speaker_id: str,
        conversation_id: str,
        speaking_time: float,
        turn_count: int,
    ):
        super().__init__(
            from_node_id=speaker_id,
            to_node_id=conversation_id,
            relationship_type=RelationshipType.SPEAKS_IN,
            properties={
                "speaking_time": speaking_time,
                "turn_count": turn_count,
                "participation_ratio": 0.0,
            },
            created_at=datetime.utcnow(),
        )


@dataclass
class DiscussesRelationship(GraphRelationship):
    """Speaker discusses topic."""

    def __init__(
        self,
        speaker_id: str,
        topic_id: str,
        mention_count: int,
        context_relevance: float,
    ):
        super().__init__(
            from_node_id=speaker_id,
            to_node_id=topic_id,
            relationship_type=RelationshipType.DISCUSSES,
            properties={
                "mention_count": mention_count,
                "context_relevance": context_relevance,
                "sentiment_score": 0.0,
            },
            created_at=datetime.utcnow(),
        )


@dataclass
class MentionsRelationship(GraphRelationship):
    """Transcript segment mentions entity."""

    def __init__(
        self,
        segment_id: str,
        entity_id: str,
        mention_position: int,
        confidence_score: float,
    ):
        super().__init__(
            from_node_id=segment_id,
            to_node_id=entity_id,
            relationship_type=RelationshipType.MENTIONS,
            properties={
                "mention_position": mention_position,
                "confidence_score": confidence_score,
                "context_window": "",
            },
            created_at=datetime.utcnow(),
        )


@dataclass
class FollowsRelationship(GraphRelationship):
    """Sequential relationship between segments."""

    def __init__(
        self,
        from_segment_id: str,
        to_segment_id: str,
        time_gap: float,
        speaker_change: bool,
    ):
        super().__init__(
            from_node_id=from_segment_id,
            to_node_id=to_segment_id,
            relationship_type=RelationshipType.FOLLOWS,
            properties={
                "time_gap": time_gap,
                "speaker_change": speaker_change,
                "conversation_flow": "normal",
            },
            created_at=datetime.utcnow(),
        )
