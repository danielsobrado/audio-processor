"""Topic graph service for topic analysis and flow tracking."""

import logging
from datetime import datetime
from typing import Any, Dict, List

from app.config.settings import get_settings
from app.db.graph_session import get_graph_db_manager
from app.schemas.graph import DiscussesRelationship, TopicNode

logger = logging.getLogger(__name__)


class TopicGraphService:
    """Service for topic-specific graph operations and flow analysis."""

    def __init__(self):
        self.settings = get_settings()
        self.batch_size = self.settings.graph.processing_batch_size

    async def create_topic(self, topic_data: Dict[str, Any]) -> bool:
        """Create a topic node in the graph."""
        if not self.settings.graph.enabled:
            logger.debug("Graph processing is disabled")
            return False

        try:
            topic_node = TopicNode(
                topic_id=topic_data["topic_id"],
                topic_name=topic_data["name"],
                confidence_score=topic_data.get("confidence_score", 0.0),
                keywords=topic_data.get("keywords", []),
            )

            manager = await get_graph_db_manager()
            query = """
            MERGE (t:Topic {id: $topic_id})
            ON CREATE SET t += $props
            ON MATCH SET t.updated_at = $updated_at,
                        t.mention_count = t.mention_count + 1
            RETURN t.id as id
            """

            props = topic_node.to_cypher_props()
            result = await manager.execute_write_transaction(
                query,
                {
                    "topic_id": topic_data["topic_id"],
                    "props": props,
                    "updated_at": datetime.utcnow().isoformat(),
                },
            )

            if result:
                logger.info(f"Created/updated topic: {topic_data['topic_id']}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to create topic: {e}")
            return False

    async def link_speaker_to_topic(
        self, speaker_id: str, topic_id: str, discussion_stats: Dict[str, Any]
    ) -> bool:
        """Link a speaker to a topic with discussion statistics."""
        if not self.settings.graph.enabled:
            return False

        try:
            relationship = DiscussesRelationship(
                speaker_id=speaker_id,
                topic_id=topic_id,
                mention_count=discussion_stats.get("mention_count", 1),
                context_relevance=discussion_stats.get("context_relevance", 0.5),
            )

            manager = await get_graph_db_manager()
            query = """
            MATCH (s:Speaker {id: $speaker_id})
            MATCH (t:Topic {id: $topic_id})
            MERGE (s)-[r:DISCUSSES]->(t)
            ON CREATE SET r += $props
            ON MATCH SET r.mention_count = r.mention_count + $mention_count,
                        r.context_relevance = ($context_relevance + r.context_relevance) / 2
            RETURN r
            """

            result = await manager.execute_write_transaction(
                query,
                {
                    "speaker_id": speaker_id,
                    "topic_id": topic_id,
                    "props": relationship.to_cypher_props(),
                    "mention_count": discussion_stats.get("mention_count", 1),
                    "context_relevance": discussion_stats.get("context_relevance", 0.5),
                },
            )

            if result:
                logger.info(f"Linked speaker {speaker_id} to topic {topic_id}")
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to link speaker to topic: {e}")
            return False

    async def get_topic_profile(self, topic_id: str) -> Dict[str, Any]:
        """Get comprehensive topic profile with statistics."""
        if not self.settings.graph.enabled:
            return {}

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (t:Topic {id: $topic_id})
            OPTIONAL MATCH (s:Speaker)-[r:DISCUSSES]->(t)
            OPTIONAL MATCH (c:Conversation)-[:CONTAINS]->(seg:TranscriptSegment)-[:MENTIONS]->(t)
            RETURN t,
                   count(DISTINCT s) as speaker_count,
                   count(DISTINCT c) as conversation_count,
                   sum(r.mention_count) as total_mentions,
                   avg(r.context_relevance) as avg_relevance,
                   collect(DISTINCT s.name) as discussing_speakers
            """

            result = await manager.execute_read_transaction(
                query, {"topic_id": topic_id}
            )

            if result:
                data = result[0]
                topic_info = data.get("t", {})
                return {
                    "topic_id": topic_id,
                    "name": topic_info.get("name", topic_id),
                    "keywords": topic_info.get("keywords", []),
                    "confidence_score": topic_info.get("confidence_score", 0.0),
                    "speaker_count": data.get("speaker_count", 0),
                    "conversation_count": data.get("conversation_count", 0),
                    "total_mentions": data.get("total_mentions", 0),
                    "avg_relevance": data.get("avg_relevance", 0.0),
                    "discussing_speakers": data.get("discussing_speakers", []),
                }
            return {}

        except Exception as e:
            logger.error(f"Failed to get topic profile: {e}")
            return {}

    async def get_topic_flow_in_conversation(
        self, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Get topic flow and transitions within a specific conversation."""
        if not self.settings.graph.enabled:
            return []

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (c:Conversation {id: $conversation_id})-[:CONTAINS]->(s1:TranscriptSegment)
            MATCH (s1)-[:FOLLOWS]->(s2:TranscriptSegment)
            MATCH (s1)-[:MENTIONS]->(t1:Topic)
            MATCH (s2)-[:MENTIONS]->(t2:Topic)
            WHERE t1.id <> t2.id
            RETURN t1.name as from_topic,
                   t2.name as to_topic,
                   t1.id as from_topic_id,
                   t2.id as to_topic_id,
                   s1.end_time as transition_start,
                   s2.start_time as transition_end,
                   s2.start_time - s1.end_time as transition_duration,
                   s1.speaker_id as from_speaker,
                   s2.speaker_id as to_speaker
            ORDER BY s1.start_time ASC
            """

            result = await manager.execute_read_transaction(
                query, {"conversation_id": conversation_id}
            )

            return result

        except Exception as e:
            logger.error(f"Failed to get topic flow: {e}")
            return []

    async def get_global_topic_transitions(
        self, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get most common topic transitions across all conversations."""
        if not self.settings.graph.enabled:
            return []

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (s1:TranscriptSegment)-[:FOLLOWS]->(s2:TranscriptSegment)
            MATCH (s1)-[:MENTIONS]->(t1:Topic)
            MATCH (s2)-[:MENTIONS]->(t2:Topic)
            WHERE t1.id <> t2.id
            RETURN t1.name as from_topic,
                   t2.name as to_topic,
                   t1.id as from_topic_id,
                   t2.id as to_topic_id,
                   count(*) as transition_count,
                   avg(s2.start_time - s1.end_time) as avg_transition_duration
            ORDER BY transition_count DESC
            LIMIT $limit
            """

            result = await manager.execute_read_transaction(query, {"limit": limit})

            return result

        except Exception as e:
            logger.error(f"Failed to get global topic transitions: {e}")
            return []

    async def get_topic_cooccurrence(
        self, topic_id: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get topics that frequently occur together with the specified topic."""
        if not self.settings.graph.enabled:
            return []

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (t1:Topic {id: $topic_id})
            MATCH (s1:TranscriptSegment)-[:MENTIONS]->(t1)
            MATCH (c:Conversation)-[:CONTAINS]->(s1)
            MATCH (c)-[:CONTAINS]->(s2:TranscriptSegment)-[:MENTIONS]->(t2:Topic)
            WHERE t1.id <> t2.id
            AND abs(s1.start_time - s2.start_time) <= 60.0  // Within 60 seconds
            RETURN t2.id as cooccurring_topic_id,
                   t2.name as cooccurring_topic_name,
                   count(*) as cooccurrence_count,
                   avg(abs(s1.start_time - s2.start_time)) as avg_time_distance
            ORDER BY cooccurrence_count DESC
            LIMIT $limit
            """

            result = await manager.execute_read_transaction(
                query, {"topic_id": topic_id, "limit": limit}
            )

            return result

        except Exception as e:
            logger.error(f"Failed to get topic cooccurrence: {e}")
            return []

    async def get_trending_topics(
        self, time_window_hours: int = 24, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get trending topics based on recent activity."""
        if not self.settings.graph.enabled:
            return []

        try:
            manager = await get_graph_db_manager()
            # Note: This query assumes we have timestamps in ISO format
            query = """
            MATCH (t:Topic)
            MATCH (s:Speaker)-[r:DISCUSSES]->(t)
            WHERE datetime(t.updated_at) >= datetime() - duration({hours: $time_window_hours})
            RETURN t.id as topic_id,
                   t.name as topic_name,
                   t.keywords as keywords,
                   count(DISTINCT s) as unique_speakers,
                   sum(r.mention_count) as total_mentions,
                   avg(r.context_relevance) as avg_relevance
            ORDER BY total_mentions DESC, unique_speakers DESC
            LIMIT $limit
            """

            result = await manager.execute_read_transaction(
                query, {"time_window_hours": time_window_hours, "limit": limit}
            )

            return result

        except Exception as e:
            logger.error(f"Failed to get trending topics: {e}")
            return []

    async def analyze_topic_sentiment_by_speaker(
        self, topic_id: str
    ) -> List[Dict[str, Any]]:
        """Analyze how different speakers discuss a specific topic."""
        if not self.settings.graph.enabled:
            return []

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (t:Topic {id: $topic_id})
            MATCH (s:Speaker)-[r:DISCUSSES]->(t)
            MATCH (seg:TranscriptSegment {speaker_id: s.id})-[:MENTIONS]->(t)
            RETURN s.id as speaker_id,
                   s.name as speaker_name,
                   r.mention_count as mention_count,
                   r.context_relevance as context_relevance,
                   avg(seg.confidence_score) as avg_confidence,
                   collect(seg.text) as sample_mentions
            ORDER BY r.mention_count DESC
            """

            result = await manager.execute_read_transaction(
                query, {"topic_id": topic_id}
            )

            return result

        except Exception as e:
            logger.error(f"Failed to analyze topic sentiment by speaker: {e}")
            return []

    async def get_topic_evolution(self, topic_id: str) -> Dict[str, Any]:
        """Track how a topic evolves over time across conversations."""
        if not self.settings.graph.enabled:
            return {}

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (t:Topic {id: $topic_id})
            MATCH (seg:TranscriptSegment)-[:MENTIONS]->(t)
            MATCH (c:Conversation)-[:CONTAINS]->(seg)
            RETURN c.id as conversation_id,
                   c.created_at as conversation_date,
                   count(seg) as mention_count,
                   avg(seg.confidence_score) as avg_confidence,
                   collect(seg.text) as mentions
            ORDER BY c.created_at ASC
            """

            result = await manager.execute_read_transaction(
                query, {"topic_id": topic_id}
            )

            evolution_data = {
                "topic_id": topic_id,
                "timeline": result,
                "evolution_stats": {
                    "total_conversations": len(result),
                    "total_mentions": sum(r["mention_count"] for r in result),
                    "avg_mentions_per_conversation": (
                        sum(r["mention_count"] for r in result) / len(result)
                        if result
                        else 0
                    ),
                },
            }

            return evolution_data

        except Exception as e:
            logger.error(f"Failed to get topic evolution: {e}")
            return {}

    async def find_topic_clusters(
        self, min_cluster_size: int = 3
    ) -> List[Dict[str, Any]]:
        """Find clusters of related topics based on cooccurrence patterns."""
        if not self.settings.graph.enabled:
            return []

        try:
            manager = await get_graph_db_manager()
            query = """
            MATCH (t1:Topic), (t2:Topic)
            WHERE t1.id < t2.id
            MATCH (s1:TranscriptSegment)-[:MENTIONS]->(t1)
            MATCH (s2:TranscriptSegment)-[:MENTIONS]->(t2)
            WHERE abs(s1.start_time - s2.start_time) <= 30.0  // Within 30 seconds
            WITH t1, t2, count(*) as cooccurrence_strength
            WHERE cooccurrence_strength >= $min_cluster_size
            RETURN t1.id as topic1_id,
                   t1.name as topic1_name,
                   t2.id as topic2_id,
                   t2.name as topic2_name,
                   cooccurrence_strength
            ORDER BY cooccurrence_strength DESC
            """

            result = await manager.execute_read_transaction(
                query, {"min_cluster_size": min_cluster_size}
            )

            return result

        except Exception as e:
            logger.error(f"Failed to find topic clusters: {e}")
            return []


# Global service instance
topic_graph_service = TopicGraphService()


# Dependency injection
async def get_topic_graph_service() -> TopicGraphService:
    """Get topic graph service instance."""
    return topic_graph_service
