"""Conversation graph service for conversation-specific graph operations."""

import logging
from typing import Any

from app.config.settings import get_settings
from app.db.graph_session import get_graph_db_manager
from app.schemas.graph import ConversationNode, TranscriptSegmentNode

logger = logging.getLogger(__name__)


class ConversationGraphService:
    """Service for conversation-specific graph operations."""

    def __init__(self):
        self.settings = get_settings()
        self.batch_size = self.settings.graph.processing_batch_size

    async def create_conversation(self, conversation_data: dict[str, Any]) -> bool:
        """Create a conversation node in the graph."""
        if not self.settings.graph.enabled:
            logger.debug("Graph processing is disabled")
            return False

        try:
            conversation_node = ConversationNode(
                conversation_id=conversation_data["conversation_id"],
                audio_file_id=conversation_data.get("audio_file_id", ""),
                duration=conversation_data.get("duration", 0.0),
                language=conversation_data.get("language", "en"),
            )

            manager = await get_graph_db_manager()
            query = """
            CREATE (c:Conversation $props)
            RETURN c.id as id
            """
            result = await manager.execute_write_transaction(
                query, {"props": conversation_node.to_cypher_props()}
            )

            if result:
                logger.info(f"Created conversation: {conversation_data['conversation_id']}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            return False

    async def add_transcript_segments(
        self, conversation_id: str, segments: list[dict[str, Any]]
    ) -> int:
        """Add transcript segments to a conversation."""
        if not self.settings.graph.enabled:
            return 0

        try:
            manager = await get_graph_db_manager()
            created_count = 0

            # Create segments in batches
            for i in range(0, len(segments), self.batch_size):
                batch = segments[i : i + self.batch_size]

                # Prepare segment nodes
                segment_props = []
                for segment in batch:
                    segment_node = TranscriptSegmentNode(
                        segment_id=f"{conversation_id}_{segment['start']:.2f}",
                        conversation_id=conversation_id,
                        text=segment["text"],
                        start_time=segment["start"],
                        end_time=segment["end"],
                        speaker_id=segment.get("speaker_id", "unknown"),
                        confidence_score=segment.get("confidence", 0.9),
                    )
                    segment_props.append(segment_node.to_cypher_props())

                # Create segments and link to conversation
                query = """
                MATCH (c:Conversation {id: $conversation_id})
                UNWIND $segments AS segment
                CREATE (s:TranscriptSegment segment)
                CREATE (c)-[:CONTAINS]->(s)
                RETURN count(s) as created_count
                """

                result = await manager.execute_write_transaction(
                    query,
                    {"conversation_id": conversation_id, "segments": segment_props},
                )

                if result:
                    created_count += result[0]["created_count"]

            logger.info(f"Added {created_count} segments to conversation {conversation_id}")
            return created_count

        except Exception as e:
            logger.error(f"Failed to add transcript segments: {e}")
            return 0

    async def get_conversation_overview(self, conversation_id: str) -> dict[str, Any]:
        """Get conversation overview with basic statistics."""
        if not self.settings.graph.enabled:
            return {}

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (c:Conversation {id: $conversation_id})
            OPTIONAL MATCH (c)-[:CONTAINS]->(s:TranscriptSegment)
            OPTIONAL MATCH (speaker:Speaker)-[:SPEAKS_IN]->(c)
            RETURN c,
                   count(DISTINCT s) as segment_count,
                   count(DISTINCT speaker) as speaker_count,
                   sum(s.duration) as total_duration,
                   collect(DISTINCT speaker.name) as speakers
            """

            result = await manager.execute_read_transaction(
                query, {"conversation_id": conversation_id}
            )

            if result:
                data = result[0]
                return {
                    "conversation_id": conversation_id,
                    "segment_count": data.get("segment_count", 0),
                    "speaker_count": data.get("speaker_count", 0),
                    "total_duration": data.get("total_duration", 0.0),
                    "speakers": data.get("speakers", []),
                }
            return {}

        except Exception as e:
            logger.error(f"Failed to get conversation overview: {e}")
            return {}

    async def get_conversation_timeline(self, conversation_id: str) -> list[dict[str, Any]]:
        """Get chronological timeline of conversation segments."""
        if not self.settings.graph.enabled:
            return []

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (c:Conversation {id: $conversation_id})-[:CONTAINS]->(s:TranscriptSegment)
            OPTIONAL MATCH (speaker:Speaker {id: s.speaker_id})
            RETURN s.start_time as start_time,
                   s.end_time as end_time,
                   s.text as text,
                   s.speaker_id as speaker_id,
                   speaker.name as speaker_name,
                   s.confidence_score as confidence
            ORDER BY s.start_time ASC
            """

            result = await manager.execute_read_transaction(
                query, {"conversation_id": conversation_id}
            )

            return result

        except Exception as e:
            logger.error(f"Failed to get conversation timeline: {e}")
            return []

    async def get_speaker_interactions(self, conversation_id: str) -> list[dict[str, Any]]:
        """Get speaker interaction patterns in conversation."""
        if not self.settings.graph.enabled:
            return []

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (c:Conversation {id: $conversation_id})-[:CONTAINS]->(s1:TranscriptSegment)
            MATCH (c)-[:CONTAINS]->(s2:TranscriptSegment)
            WHERE s1.speaker_id <> s2.speaker_id
            AND s1.end_time <= s2.start_time
            AND s2.start_time <= s1.end_time + 10.0  // Within 10 seconds
            MATCH (sp1:Speaker {id: s1.speaker_id})
            MATCH (sp2:Speaker {id: s2.speaker_id})
            RETURN sp1.name as from_speaker,
                   sp2.name as to_speaker,
                   count(*) as interaction_count,
                   avg(s2.start_time - s1.end_time) as avg_response_time
            ORDER BY interaction_count DESC
            """

            result = await manager.execute_read_transaction(
                query, {"conversation_id": conversation_id}
            )

            return result

        except Exception as e:
            logger.error(f"Failed to get speaker interactions: {e}")
            return []

    async def search_conversation_content(
        self, conversation_id: str, search_term: str
    ) -> list[dict[str, Any]]:
        """Search for specific content within a conversation."""
        if not self.settings.graph.enabled:
            return []

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (c:Conversation {id: $conversation_id})-[:CONTAINS]->(s:TranscriptSegment)
            WHERE toLower(s.text) CONTAINS toLower($search_term)
            OPTIONAL MATCH (speaker:Speaker {id: s.speaker_id})
            RETURN s.start_time as start_time,
                   s.end_time as end_time,
                   s.text as text,
                   s.speaker_id as speaker_id,
                   speaker.name as speaker_name,
                   s.confidence_score as confidence
            ORDER BY s.start_time ASC
            """

            result = await manager.execute_read_transaction(
                query, {"conversation_id": conversation_id, "search_term": search_term}
            )

            return result

        except Exception as e:
            logger.error(f"Failed to search conversation content: {e}")
            return []

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its related data."""
        if not self.settings.graph.enabled:
            return False

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (c:Conversation {id: $conversation_id})
            OPTIONAL MATCH (c)-[:CONTAINS]->(s:TranscriptSegment)
            DETACH DELETE c, s
            RETURN count(c) as deleted_count
            """

            result = await manager.execute_write_transaction(
                query, {"conversation_id": conversation_id}
            )

            if result and result[0]["deleted_count"] > 0:
                logger.info(f"Deleted conversation: {conversation_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to delete conversation: {e}")
            return False


# Global service instance
conversation_graph_service = ConversationGraphService()


# Dependency injection
async def get_conversation_graph_service() -> ConversationGraphService:
    """Get conversation graph service instance."""
    return conversation_graph_service
