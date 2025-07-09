"""Speaker graph service for speaker network analysis and operations."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.config.settings import get_settings
from app.db.graph_session import get_graph_db_manager
from app.schemas.graph import (
    GraphNode,
    GraphRelationship,
    SpeakerNode,
    SpeaksInRelationship,
)

logger = logging.getLogger(__name__)


class SpeakerGraphService:
    """Service for speaker-specific graph operations and network analysis."""

    def __init__(self):
        self.settings = get_settings()
        self.batch_size = self.settings.graph.processing_batch_size

    async def create_speaker(self, speaker_data: Dict[str, Any]) -> bool:
        """Create a speaker node in the graph."""
        if not self.settings.graph.enabled:
            logger.debug("Graph processing is disabled")
            return False

        try:
            speaker_node = SpeakerNode(
                speaker_id=speaker_data["speaker_id"],
                name=speaker_data.get("name"),
                voice_characteristics=speaker_data.get("voice_characteristics", {}),
            )

            manager = await get_graph_db_manager()
            query = """
            MERGE (s:Speaker {id: $speaker_id})
            ON CREATE SET s += $props
            ON MATCH SET s.updated_at = $updated_at
            RETURN s.id as id
            """

            props = speaker_node.to_cypher_props()
            result = await manager.execute_write_transaction(
                query,
                {
                    "speaker_id": speaker_data["speaker_id"],
                    "props": props,
                    "updated_at": datetime.utcnow().isoformat(),
                },
            )

            if result:
                logger.info(f"Created/updated speaker: {speaker_data['speaker_id']}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to create speaker: {e}")
            return False

    async def link_speaker_to_conversation(
        self, speaker_id: str, conversation_id: str, speaking_stats: Dict[str, Any]
    ) -> bool:
        """Link a speaker to a conversation with speaking statistics."""
        if not self.settings.graph.enabled:
            return False

        try:
            relationship = SpeaksInRelationship(
                speaker_id=speaker_id,
                conversation_id=conversation_id,
                speaking_time=speaking_stats.get("speaking_time", 0.0),
                turn_count=speaking_stats.get("turn_count", 0),
            )

            manager = await get_graph_db_manager()
            query = """
            MATCH (s:Speaker {id: $speaker_id})
            MATCH (c:Conversation {id: $conversation_id})
            MERGE (s)-[r:SPEAKS_IN]->(c)
            SET r += $props
            RETURN r
            """

            result = await manager.execute_write_transaction(
                query,
                {
                    "speaker_id": speaker_id,
                    "conversation_id": conversation_id,
                    "props": relationship.to_cypher_props(),
                },
            )

            if result:
                logger.info(
                    f"Linked speaker {speaker_id} to conversation {conversation_id}"
                )
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to link speaker to conversation: {e}")
            return False

    async def get_speaker_profile(self, speaker_id: str) -> Dict[str, Any]:
        """Get comprehensive speaker profile with statistics."""
        if not self.settings.graph.enabled:
            return {}

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (s:Speaker {id: $speaker_id})
            OPTIONAL MATCH (s)-[r:SPEAKS_IN]->(c:Conversation)
            OPTIONAL MATCH (s)-[:DISCUSSES]->(t:Topic)
            RETURN s,
                   count(DISTINCT c) as conversation_count,
                   sum(r.speaking_time) as total_speaking_time,
                   avg(r.speaking_time) as avg_speaking_time,
                   sum(r.turn_count) as total_turns,
                   collect(DISTINCT t.name) as topics_discussed
            """

            result = await manager.execute_read_transaction(
                query, {"speaker_id": speaker_id}
            )

            if result:
                data = result[0]
                speaker_info = data.get("s", {})
                return {
                    "speaker_id": speaker_id,
                    "name": speaker_info.get("name", f"Speaker_{speaker_id}"),
                    "voice_characteristics": speaker_info.get(
                        "voice_characteristics", {}
                    ),
                    "conversation_count": data.get("conversation_count", 0),
                    "total_speaking_time": data.get("total_speaking_time", 0.0),
                    "avg_speaking_time": data.get("avg_speaking_time", 0.0),
                    "total_turns": data.get("total_turns", 0),
                    "topics_discussed": data.get("topics_discussed", []),
                }
            return {}

        except Exception as e:
            logger.error(f"Failed to get speaker profile: {e}")
            return {}

    async def get_speaker_network(
        self, speaker_id: str, max_depth: int = 2
    ) -> Dict[str, Any]:
        """Get speaker's interaction network up to specified depth."""
        if not self.settings.graph.enabled:
            return {}

        try:
            manager = await get_graph_db_manager()
            query = f"""
            MATCH (s:Speaker {{id: $speaker_id}})
            MATCH (s)-[:SPEAKS_IN]->(c:Conversation)<-[:SPEAKS_IN]-(other:Speaker)
            WHERE other.id <> s.id
            WITH s, other, collect(DISTINCT c.id) as shared_conversations
            RETURN s.name as speaker_name,
                   other.id as connected_speaker_id,
                   other.name as connected_speaker_name,
                   size(shared_conversations) as shared_conversation_count,
                   shared_conversations
            ORDER BY shared_conversation_count DESC
            LIMIT 50
            """

            result = await manager.execute_read_transaction(
                query, {"speaker_id": speaker_id}
            )

            network_data = {
                "speaker_id": speaker_id,
                "connections": [],
                "network_stats": {
                    "total_connections": len(result),
                    "max_shared_conversations": max(
                        [r["shared_conversation_count"] for r in result], default=0
                    ),
                },
            }

            for record in result:
                network_data["connections"].append(
                    {
                        "speaker_id": record["connected_speaker_id"],
                        "speaker_name": record["connected_speaker_name"],
                        "shared_conversations": record["shared_conversation_count"],
                        "conversation_ids": record["shared_conversations"],
                    }
                )

            return network_data

        except Exception as e:
            logger.error(f"Failed to get speaker network: {e}")
            return {}

    async def get_speaker_interaction_patterns(self, speaker_id: str) -> Dict[str, Any]:
        """Analyze speaker's interaction patterns and communication style."""
        if not self.settings.graph.enabled:
            return {}

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (s:Speaker {id: $speaker_id})-[:SPEAKS_IN]->(c:Conversation)
            MATCH (c)-[:CONTAINS]->(seg:TranscriptSegment {speaker_id: $speaker_id})
            WITH s, c, seg, 
                 avg(seg.duration) as avg_segment_duration,
                 count(seg) as segment_count,
                 sum(seg.duration) as total_speaking_time
            OPTIONAL MATCH (c)-[:CONTAINS]->(other_seg:TranscriptSegment)
            WHERE other_seg.speaker_id <> $speaker_id
            AND other_seg.start_time > seg.end_time
            AND other_seg.start_time <= seg.end_time + 30.0  // Within 30 seconds
            WITH s, c, avg_segment_duration, segment_count, total_speaking_time,
                 avg(other_seg.start_time - seg.end_time) as avg_pause_duration
            RETURN s.name as speaker_name,
                   count(DISTINCT c) as conversation_count,
                   avg(avg_segment_duration) as avg_segment_duration,
                   sum(segment_count) as total_segments,
                   sum(total_speaking_time) as total_speaking_time,
                   avg(avg_pause_duration) as avg_pause_between_turns
            """

            result = await manager.execute_read_transaction(
                query, {"speaker_id": speaker_id}
            )

            if result:
                data = result[0]
                return {
                    "speaker_id": speaker_id,
                    "speaker_name": data.get("speaker_name", f"Speaker_{speaker_id}"),
                    "conversation_count": data.get("conversation_count", 0),
                    "avg_segment_duration": data.get("avg_segment_duration", 0.0),
                    "total_segments": data.get("total_segments", 0),
                    "total_speaking_time": data.get("total_speaking_time", 0.0),
                    "avg_pause_between_turns": data.get("avg_pause_between_turns", 0.0),
                    "communication_style": self._analyze_communication_style(data),
                }
            return {}

        except Exception as e:
            logger.error(f"Failed to get speaker interaction patterns: {e}")
            return {}

    def _analyze_communication_style(self, data: Dict[str, Any]) -> str:
        """Analyze communication style based on speaking patterns."""
        avg_duration = data.get("avg_segment_duration", 0.0)
        avg_pause = data.get("avg_pause_between_turns", 0.0)

        if avg_duration > 15.0:
            if avg_pause > 5.0:
                return "Thoughtful - Long segments with pauses"
            else:
                return "Dominant - Long segments with quick responses"
        elif avg_duration > 5.0:
            if avg_pause > 3.0:
                return "Conversational - Moderate segments with natural pauses"
            else:
                return "Engaging - Moderate segments with quick responses"
        else:
            if avg_pause > 2.0:
                return "Reactive - Short segments with pauses"
            else:
                return "Rapid - Short segments with quick responses"

    async def get_top_speakers(
        self, limit: int = 10, metric: str = "speaking_time"
    ) -> List[Dict[str, Any]]:
        """Get top speakers based on specified metric."""
        if not self.settings.graph.enabled:
            return []

        try:
            manager = await get_graph_db_manager()

            order_by = {
                "speaking_time": "total_speaking_time DESC",
                "conversations": "conversation_count DESC",
                "turns": "total_turns DESC",
            }.get(metric, "total_speaking_time DESC")

            query = f"""
            MATCH (s:Speaker)-[r:SPEAKS_IN]->(c:Conversation)
            RETURN s.id as speaker_id,
                   s.name as speaker_name,
                   count(DISTINCT c) as conversation_count,
                   sum(r.speaking_time) as total_speaking_time,
                   sum(r.turn_count) as total_turns,
                   avg(r.speaking_time) as avg_speaking_time
            ORDER BY {order_by}
            LIMIT $limit
            """

            result = await manager.execute_read_transaction(query, {"limit": limit})

            return result

        except Exception as e:
            logger.error(f"Failed to get top speakers: {e}")
            return []

    async def find_similar_speakers(
        self, speaker_id: str, similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Find speakers with similar communication patterns."""
        if not self.settings.graph.enabled:
            return []

        try:
            # Get target speaker's pattern
            target_pattern = await self.get_speaker_interaction_patterns(speaker_id)
            if not target_pattern:
                return []

            # Find speakers with similar patterns
            manager = await get_graph_db_manager()
            query = """
            MATCH (s:Speaker)-[:SPEAKS_IN]->(c:Conversation)
            WHERE s.id <> $speaker_id
            MATCH (c)-[:CONTAINS]->(seg:TranscriptSegment {speaker_id: s.id})
            WITH s, 
                 avg(seg.duration) as avg_segment_duration,
                 count(seg) as segment_count,
                 sum(seg.duration) as total_speaking_time
            RETURN s.id as speaker_id,
                   s.name as speaker_name,
                   avg_segment_duration,
                   segment_count,
                   total_speaking_time
            """

            result = await manager.execute_read_transaction(
                query, {"speaker_id": speaker_id}
            )

            similar_speakers = []
            target_avg_duration = target_pattern.get("avg_segment_duration", 0.0)

            for record in result:
                duration_diff = abs(
                    record["avg_segment_duration"] - target_avg_duration
                )
                similarity = max(0, 1 - (duration_diff / max(target_avg_duration, 1.0)))

                if similarity >= similarity_threshold:
                    similar_speakers.append(
                        {
                            "speaker_id": record["speaker_id"],
                            "speaker_name": record["speaker_name"],
                            "similarity_score": similarity,
                            "avg_segment_duration": record["avg_segment_duration"],
                        }
                    )

            return sorted(
                similar_speakers, key=lambda x: x["similarity_score"], reverse=True
            )

        except Exception as e:
            logger.error(f"Failed to find similar speakers: {e}")
            return []


# Global service instance
speaker_graph_service = SpeakerGraphService()


# Dependency injection
async def get_speaker_graph_service() -> SpeakerGraphService:
    """Get speaker graph service instance."""
    return speaker_graph_service
