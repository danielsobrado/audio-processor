"""
Graph service for abstracting graph database operations.
"""

import logging
from typing import Any, Dict, List, Optional

from app.config.settings import get_settings
from app.db.graph_session import get_graph_db_manager

logger = logging.getLogger(__name__)


class GraphService:
    """
    Service for interacting with the graph database.
    """

    def __init__(self):
        self.settings = get_settings()

    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the graph database.
        """
        if not self.settings.graph.enabled:
            return {"message": "Graph processing is disabled"}

        try:
            manager = await get_graph_db_manager()
            if not manager.is_connected:
                await manager.initialize()

            # Query actual database stats
            node_count_query = "MATCH (n) RETURN count(n) as nodes"
            rel_count_query = "MATCH ()-[r]->() RETURN count(r) as relationships"

            node_result = await manager.execute_read_transaction(node_count_query)
            rel_result = await manager.execute_read_transaction(rel_count_query)

            return {
                "nodes": node_result[0]["nodes"] if node_result else 0,
                "relationships": rel_result[0]["relationships"] if rel_result else 0,
                "database_type": self.settings.graph.database.type,
                "enabled": True,
            }
        except Exception as e:
            logger.error(f"Failed to get graph stats: {e}", exc_info=True)
            return {"error": str(e), "enabled": True}

    async def get_conversation_graph(
        self, conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the graph for a specific conversation.
        """
        if not self.settings.graph.enabled:
            return None

        try:
            manager = await get_graph_db_manager()
            if not manager.is_connected:
                await manager.initialize()

            # Query for conversation nodes and relationships
            query = """
            MATCH (conv:Conversation {id: $conversation_id})
            OPTIONAL MATCH (conv)-[:HAS_SPEAKER]->(s:Speaker)
            OPTIONAL MATCH (conv)-[:HAS_TOPIC]->(t:Topic)
            OPTIONAL MATCH (s)-[r:SPEAKS_TO]->(s2:Speaker)
            RETURN conv, collect(DISTINCT s) as speakers, 
                   collect(DISTINCT t) as topics,
                   collect(DISTINCT r) as relationships
            """

            result = await manager.execute_read_transaction(
                query, {"conversation_id": conversation_id}
            )

            if not result:
                return {
                    "conversation_id": conversation_id,
                    "nodes": [],
                    "edges": [],
                    "found": False,
                }

            data = result[0]
            nodes = []
            edges = []

            # Add speakers as nodes
            for speaker in data.get("speakers", []):
                if speaker:
                    nodes.append(
                        {
                            "id": speaker.get("id"),
                            "type": "speaker",
                            "label": speaker.get("name", "Unknown Speaker"),
                            "properties": dict(speaker),
                        }
                    )

            # Add topics as nodes
            for topic in data.get("topics", []):
                if topic:
                    nodes.append(
                        {
                            "id": topic.get("id"),
                            "type": "topic",
                            "label": topic.get("name", "Unknown Topic"),
                            "properties": dict(topic),
                        }
                    )

            # Add relationships as edges
            for rel in data.get("relationships", []):
                if rel:
                    edges.append(
                        {
                            "from": rel.start_node.get("id"),
                            "to": rel.end_node.get("id"),
                            "type": rel.type,
                            "properties": dict(rel),
                        }
                    )

            return {
                "conversation_id": conversation_id,
                "nodes": nodes,
                "edges": edges,
                "found": True,
            }

        except Exception as e:
            logger.error(f"Failed to get conversation graph: {e}", exc_info=True)
            return None

    async def get_speaker_network(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get the speaker network for a specific conversation.
        """
        if not self.settings.graph.enabled:
            return []

        try:
            manager = await get_graph_db_manager()
            if not manager.is_connected:
                await manager.initialize()

            # Query for speaker interactions
            query = """
            MATCH (conv:Conversation {id: $conversation_id})-[:HAS_SPEAKER]->(s1:Speaker)
            OPTIONAL MATCH (s1)-[r:SPEAKS_TO]->(s2:Speaker)<-[:HAS_SPEAKER]-(conv)
            RETURN s1.id as speaker_id, s1.name as speaker_name,
                   s1.speaking_time as speaking_time,
                   collect({
                       target_id: s2.id,
                       target_name: s2.name,
                       interaction_count: r.interaction_count,
                       total_duration: r.total_duration
                   }) as interactions
            ORDER BY s1.speaking_time DESC
            """

            results = await manager.execute_read_transaction(
                query, {"conversation_id": conversation_id}
            )

            network = []
            for result in results:
                # Filter out null interactions
                interactions = [
                    i for i in result.get("interactions", []) if i.get("target_id")
                ]

                network.append(
                    {
                        "speaker_id": result.get("speaker_id"),
                        "speaker_name": result.get("speaker_name", "Unknown"),
                        "speaking_time": result.get("speaking_time", 0),
                        "interactions": interactions,
                        "interaction_count": len(interactions),
                    }
                )

            return network

        except Exception as e:
            logger.error(f"Failed to get speaker network: {e}", exc_info=True)
            return []

    async def get_topic_flow(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get the topic flow for a specific conversation.
        """
        if not self.settings.graph.enabled:
            return []

        try:
            manager = await get_graph_db_manager()
            if not manager.is_connected:
                await manager.initialize()

            # Query for topic transitions and timeline
            query = """
            MATCH (conv:Conversation {id: $conversation_id})-[:HAS_TOPIC]->(t:Topic)
            OPTIONAL MATCH (t)-[r:TRANSITIONS_TO]->(t2:Topic)<-[:HAS_TOPIC]-(conv)
            RETURN t.id as topic_id, t.name as topic_name,
                   t.start_time as start_time, t.end_time as end_time,
                   t.duration as duration, t.keywords as keywords,
                   collect({
                       target_id: t2.id,
                       target_name: t2.name,
                       transition_time: r.transition_time,
                       transition_type: r.transition_type
                   }) as transitions
            ORDER BY t.start_time ASC
            """

            results = await manager.execute_read_transaction(
                query, {"conversation_id": conversation_id}
            )

            topic_flow = []
            for result in results:
                # Filter out null transitions
                transitions = [
                    t for t in result.get("transitions", []) if t.get("target_id")
                ]

                topic_flow.append(
                    {
                        "topic_id": result.get("topic_id"),
                        "topic_name": result.get("topic_name", "Unknown Topic"),
                        "start_time": result.get("start_time", 0),
                        "end_time": result.get("end_time", 0),
                        "duration": result.get("duration", 0),
                        "keywords": result.get("keywords", []),
                        "transitions": transitions,
                        "transition_count": len(transitions),
                    }
                )

            return topic_flow

        except Exception as e:
            logger.error(f"Failed to get topic flow: {e}", exc_info=True)
            return []

    async def get_node_relationships(
        self,
        node_id: str,
        relationship_types: Optional[List[str]] = None,
        direction: str = "BOTH",
    ) -> List[Dict[str, Any]]:
        """
        Get relationships for a specific node.
        """
        if not self.settings.graph.enabled:
            return []

        try:
            manager = await get_graph_db_manager()
            if not manager.is_connected:
                await manager.initialize()

            # Build query based on direction and relationship types
            direction_clause = ""
            if direction.upper() == "OUTGOING":
                direction_clause = "-[r]->"
            elif direction.upper() == "INCOMING":
                direction_clause = "<-[r]-"
            else:  # BOTH
                direction_clause = "-[r]-"

            type_filter = ""
            if relationship_types:
                type_list = "|".join(relationship_types)
                type_filter = f":{type_list}"

            query = f"""
            MATCH (n {{id: $node_id}}){direction_clause}(related)
            WHERE type(r) {f'IN {relationship_types}' if relationship_types else 'IS NOT NULL'}
            RETURN n, r, related, type(r) as rel_type
            """

            results = await manager.execute_read_transaction(
                query, {"node_id": node_id}
            )

            relationships = []
            for result in results:
                relationships.append(
                    {
                        "source_node": {
                            "id": result["n"].get("id"),
                            "type": (
                                list(result["n"].labels)[0]
                                if result["n"].labels
                                else "Unknown"
                            ),
                            "properties": dict(result["n"]),
                        },
                        "target_node": {
                            "id": result["related"].get("id"),
                            "type": (
                                list(result["related"].labels)[0]
                                if result["related"].labels
                                else "Unknown"
                            ),
                            "properties": dict(result["related"]),
                        },
                        "relationship": {
                            "type": result["rel_type"],
                            "properties": dict(result["r"]),
                        },
                    }
                )

            return relationships

        except Exception as e:
            logger.error(f"Failed to get node relationships: {e}", exc_info=True)
            return []

    async def find_shortest_path(
        self,
        from_node_id: str,
        to_node_id: str,
        max_hops: int = 5,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Find the shortest path between two nodes.
        """
        if not self.settings.graph.enabled:
            return None

        try:
            manager = await get_graph_db_manager()
            if not manager.is_connected:
                await manager.initialize()

            # Use Cypher shortestPath function with max hop limit
            query = """
            MATCH (start {id: $from_node_id}), (end {id: $to_node_id})
            MATCH p = shortestPath((start)-[*1..$max_hops]-(end))
            RETURN nodes(p) as path_nodes, relationships(p) as path_relationships,
                   length(p) as path_length
            """

            results = await manager.execute_read_transaction(
                query,
                {
                    "from_node_id": from_node_id,
                    "to_node_id": to_node_id,
                    "max_hops": max_hops,
                },
            )

            if not results:
                return None

            result = results[0]
            path = []

            nodes = result.get("path_nodes", [])
            relationships = result.get("path_relationships", [])

            # Build path with alternating nodes and relationships
            for i, node in enumerate(nodes):
                path.append(
                    {
                        "type": "node",
                        "id": node.get("id"),
                        "labels": list(node.labels) if hasattr(node, "labels") else [],
                        "properties": dict(node),
                    }
                )

                # Add relationship if not the last node
                if i < len(relationships):
                    rel = relationships[i]
                    path.append(
                        {
                            "type": "relationship",
                            "rel_type": rel.type if hasattr(rel, "type") else "UNKNOWN",
                            "properties": dict(rel),
                        }
                    )

            return path

        except Exception as e:
            logger.error(f"Failed to find shortest path: {e}", exc_info=True)
            return None

    async def create_nodes_batch(self, nodes: List[Any]) -> int:
        """
        Create multiple nodes in a batch.
        """
        if not self.settings.graph.enabled:
            return 0

        try:
            manager = await get_graph_db_manager()
            queries = []
            for node in nodes:
                query = f"MERGE (n:{node.node_type.value} {{id: $id}}) ON CREATE SET n = $props ON MATCH SET n += $props"
                queries.append((query, node.to_cypher_props()))
            results = await manager.execute_batch_transactions(queries)
            return len(results)
        except Exception as e:
            logger.error(f"Failed to create nodes in batch: {e}", exc_info=True)
            raise

    async def create_relationships_batch(self, relationships: List[Any]) -> int:
        """
        Create multiple relationships in a batch.
        """
        if not self.settings.graph.enabled:
            return 0

        try:
            manager = await get_graph_db_manager()
            queries = []
            for rel in relationships:
                query = (
                    f"MATCH (a), (b) WHERE a.id = $from_node_id AND b.id = $to_node_id "
                    f"MERGE (a)-[r:{rel.relationship_type.value}]->(b) ON CREATE SET r = $props ON MATCH SET r += $props"
                )
                queries.append(
                    (
                        query,
                        {
                            "from_node_id": rel.from_node_id,
                            "to_node_id": rel.to_node_id,
                            "props": rel.to_cypher_props(),
                        },
                    )
                )
            results = await manager.execute_batch_transactions(queries)
            return len(results)
        except Exception as e:
            logger.error(f"Failed to create relationships in batch: {e}", exc_info=True)
            raise


def get_graph_service() -> GraphService:
    """
    Get an instance of the GraphService.
    """
    return GraphService()
