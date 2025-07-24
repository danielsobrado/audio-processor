"""Service for loading AutoSchemaKG output into Neo4j database."""

import csv
import json
import logging
import os
from typing import Any, Dict, List, Optional

from app.db.graph_session import get_graph_db_manager

logger = logging.getLogger(__name__)


class AutoSchemaNeo4jLoader:
    """Loads AutoSchemaKG output files into Neo4j database."""

    def __init__(self):
        pass

    async def load_csv_data(self, output_directory: str, job_id: str) -> Dict[str, Any]:
        """Load CSV data from AutoSchemaKG output into Neo4j."""
        try:
            manager = await get_graph_db_manager()
            if not manager.is_connected:
                await manager.initialize()

            result = {
                "nodes_loaded": 0,
                "relationships_loaded": 0,
                "concepts_loaded": 0,
                "errors": [],
            }

            # Load node data
            nodes_file = self._find_file(output_directory, ["nodes.csv", "entity.csv"])
            if nodes_file:
                nodes_loaded = await self._load_nodes(nodes_file, job_id, manager)
                result["nodes_loaded"] = nodes_loaded
                logger.info(f"Loaded {nodes_loaded} nodes from {nodes_file}")

            # Load relationship data
            relations_file = self._find_file(
                output_directory, ["relations.csv", "edges.csv", "triples.csv"]
            )
            if relations_file:
                relations_loaded = await self._load_relationships(relations_file, job_id, manager)
                result["relationships_loaded"] = relations_loaded
                logger.info(f"Loaded {relations_loaded} relationships from {relations_file}")

            # Load concept data
            concepts_file = self._find_file(output_directory, ["concepts.csv", "concept.csv"])
            if concepts_file:
                concepts_loaded = await self._load_concepts(concepts_file, job_id, manager)
                result["concepts_loaded"] = concepts_loaded
                logger.info(f"Loaded {concepts_loaded} concepts from {concepts_file}")

            return result

        except Exception as e:
            logger.error(f"Failed to load AutoSchemaKG data: {e}")
            raise

    def _find_file(self, directory: str, possible_names: List[str]) -> Optional[str]:
        """Find a file with one of the possible names in the directory."""
        for filename in os.listdir(directory):
            for possible_name in possible_names:
                if filename.endswith(possible_name):
                    return os.path.join(directory, filename)
        return None

    async def _load_nodes(self, nodes_file: str, job_id: str, manager) -> int:
        """Load node data into Neo4j."""
        nodes_loaded = 0

        try:
            with open(nodes_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                # Process nodes in batches
                batch_size = 1000
                batch = []

                for row in reader:
                    batch.append(row)

                    if len(batch) >= batch_size:
                        nodes_loaded += await self._insert_node_batch(batch, job_id, manager)
                        batch = []

                # Process remaining nodes
                if batch:
                    nodes_loaded += await self._insert_node_batch(batch, job_id, manager)

        except Exception as e:
            logger.error(f"Failed to load nodes from {nodes_file}: {e}")
            raise

        return nodes_loaded

    async def _insert_node_batch(self, batch: List[Dict[str, Any]], job_id: str, manager) -> int:
        """Insert a batch of nodes into Neo4j."""
        try:
            # Prepare data for Cypher query - MERGE on text and job_id to prevent duplicates
            query = """
            UNWIND $batch AS row
            MERGE (n:AutoSchemaNode {text: row.text, job_id: $job_id})
            SET n.type = COALESCE(row.type, 'Entity'),
                n.confidence = COALESCE(toFloat(row.confidence), 1.0),
                n.created_at = datetime(),
                n.source = 'autoschema_kg'
            """

            # Format batch data - use text as unique identifier
            formatted_batch = []
            seen_texts = set()
            for i, row in enumerate(batch):
                text = row.get("text", row.get("name", ""))
                # Skip duplicates within the batch
                if text in seen_texts:
                    continue
                seen_texts.add(text)

                formatted_row = {
                    "text": text,
                    "type": row.get("type", "Entity"),
                    "confidence": row.get("confidence", "1.0"),
                }
                formatted_batch.append(formatted_row)

            await manager.execute_write_transaction(
                query, {"batch": formatted_batch, "job_id": job_id}
            )

            return len(formatted_batch)

        except Exception as e:
            logger.error(f"Failed to insert node batch: {e}")
            return 0

    async def _load_relationships(self, relations_file: str, job_id: str, manager) -> int:
        """Load relationship data into Neo4j."""
        relationships_loaded = 0

        try:
            with open(relations_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                # Process relationships in batches
                batch_size = 1000
                batch = []

                for row in reader:
                    batch.append(row)

                    if len(batch) >= batch_size:
                        relationships_loaded += await self._insert_relationship_batch(
                            batch, job_id, manager
                        )
                        batch = []

                # Process remaining relationships
                if batch:
                    relationships_loaded += await self._insert_relationship_batch(
                        batch, job_id, manager
                    )

        except Exception as e:
            logger.error(f"Failed to load relationships from {relations_file}: {e}")
            raise

        return relationships_loaded

    async def _insert_relationship_batch(
        self, batch: List[Dict[str, Any]], job_id: str, manager
    ) -> int:
        """Insert a batch of relationships into Neo4j."""
        try:
            query = """
            UNWIND $batch AS row
            MATCH (source:AutoSchemaNode {text: row.source, job_id: $job_id})
            MATCH (target:AutoSchemaNode {text: row.target, job_id: $job_id})
            MERGE (source)-[r:AUTOSCHEMA_RELATION {
                type: row.relation,
                job_id: $job_id,
                source_text: row.source,
                target_text: row.target
            }]->(target)
            SET r.confidence = COALESCE(toFloat(row.confidence), 1.0),
                r.created_at = datetime(),
                r.source = 'autoschema_kg'
            """

            # Format batch data and remove duplicates
            formatted_batch = []
            seen_relations = set()

            for row in batch:
                source = row.get("source", row.get("head", row.get("subject", "")))
                target = row.get("target", row.get("tail", row.get("object", "")))
                relation = row.get("relation", row.get("predicate", "RELATED_TO"))

                # Create unique key for deduplication
                relation_key = (source, relation, target)
                if relation_key in seen_relations:
                    continue
                seen_relations.add(relation_key)

                formatted_row = {
                    "source": source,
                    "target": target,
                    "relation": relation,
                    "confidence": row.get("confidence", "1.0"),
                }
                formatted_batch.append(formatted_row)

            await manager.execute_write_transaction(
                query, {"batch": formatted_batch, "job_id": job_id}
            )

            return len(formatted_batch)

        except Exception as e:
            logger.error(f"Failed to insert relationship batch: {e}")
            return 0

    async def _load_concepts(self, concepts_file: str, job_id: str, manager) -> int:
        """Load concept data into Neo4j."""
        concepts_loaded = 0

        try:
            with open(concepts_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                # Process concepts in batches
                batch_size = 1000
                batch = []

                for row in reader:
                    batch.append(row)

                    if len(batch) >= batch_size:
                        concepts_loaded += await self._insert_concept_batch(batch, job_id, manager)
                        batch = []

                # Process remaining concepts
                if batch:
                    concepts_loaded += await self._insert_concept_batch(batch, job_id, manager)

        except Exception as e:
            logger.error(f"Failed to load concepts from {concepts_file}: {e}")
            raise

        return concepts_loaded

    async def _insert_concept_batch(self, batch: List[Dict[str, Any]], job_id: str, manager) -> int:
        """Insert a batch of concepts into Neo4j."""
        try:
            query = """
            UNWIND $batch AS row
            MERGE (c:AutoSchemaConcept {name: row.name, job_id: $job_id})
            SET c.description = row.description,
                c.category = COALESCE(row.category, 'General'),
                c.confidence = COALESCE(toFloat(row.confidence), 1.0),
                c.created_at = datetime(),
                c.source = 'autoschema_kg'
            """

            # Format batch data
            formatted_batch = []
            for row in batch:
                formatted_row = {
                    "name": row.get("name", row.get("concept", "")),
                    "description": row.get("description", ""),
                    "category": row.get("category", "General"),
                    "confidence": row.get("confidence", "1.0"),
                }
                formatted_batch.append(formatted_row)

            await manager.execute_write_transaction(
                query, {"batch": formatted_batch, "job_id": job_id}
            )

            return len(batch)

        except Exception as e:
            logger.error(f"Failed to insert concept batch: {e}")
            return 0

    async def get_job_statistics(self, job_id: str) -> Dict[str, Any]:
        """Get statistics for a specific AutoSchemaKG job."""
        try:
            manager = await get_graph_db_manager()
            if not manager.is_connected:
                await manager.initialize()

            # Count nodes
            nodes_query = """
            MATCH (n:AutoSchemaNode {job_id: $job_id})
            RETURN count(n) as node_count
            """
            nodes_result = await manager.execute_read_transaction(nodes_query, {"job_id": job_id})
            node_count = nodes_result[0]["node_count"] if nodes_result else 0

            # Count relationships
            rels_query = """
            MATCH ()-[r:AUTOSCHEMA_RELATION {job_id: $job_id}]->()
            RETURN count(r) as rel_count
            """
            rels_result = await manager.execute_read_transaction(rels_query, {"job_id": job_id})
            rel_count = rels_result[0]["rel_count"] if rels_result else 0

            # Count concepts
            concepts_query = """
            MATCH (c:AutoSchemaConcept {job_id: $job_id})
            RETURN count(c) as concept_count
            """
            concepts_result = await manager.execute_read_transaction(
                concepts_query, {"job_id": job_id}
            )
            concept_count = concepts_result[0]["concept_count"] if concepts_result else 0

            return {
                "job_id": job_id,
                "node_count": node_count,
                "relationship_count": rel_count,
                "concept_count": concept_count,
            }

        except Exception as e:
            logger.error(f"Failed to get job statistics: {e}")
            return {
                "job_id": job_id,
                "node_count": 0,
                "relationship_count": 0,
                "concept_count": 0,
                "error": str(e),
            }

    async def delete_job_data(self, job_id: str) -> Dict[str, Any]:
        """Delete all data for a specific AutoSchemaKG job."""
        try:
            manager = await get_graph_db_manager()
            if not manager.is_connected:
                await manager.initialize()

            # Delete relationships first
            rel_query = """
            MATCH ()-[r:AUTOSCHEMA_RELATION {job_id: $job_id}]->()
            DELETE r
            """
            await manager.execute_write_transaction(rel_query, {"job_id": job_id})

            # Delete nodes
            node_query = """
            MATCH (n:AutoSchemaNode {job_id: $job_id})
            DELETE n
            """
            await manager.execute_write_transaction(node_query, {"job_id": job_id})

            # Delete concepts
            concept_query = """
            MATCH (c:AutoSchemaConcept {job_id: $job_id})
            DELETE c
            """
            await manager.execute_write_transaction(concept_query, {"job_id": job_id})

            return {"success": True, "job_id": job_id, "message": "Job data deleted successfully"}

        except Exception as e:
            logger.error(f"Failed to delete job data: {e}")
            return {"success": False, "job_id": job_id, "error": str(e)}
