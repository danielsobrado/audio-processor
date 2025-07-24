"""AutoSchemaKG API endpoints for autonomous knowledge graph construction."""

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.config.settings import get_settings
from app.db.graph_session import get_graph_db_manager
from app.services.graph_service import GraphService, get_graph_service

# Add the autoschema_kg library path to sys.path
current_dir = Path(__file__).parent.parent.parent.parent
autoschema_kg_path = current_dir / "lib" / "autoschema_kg"
if str(autoschema_kg_path) not in sys.path:
    sys.path.insert(0, str(autoschema_kg_path))

logger = logging.getLogger(__name__)

router = APIRouter()


class AutoSchemaKGRequest(BaseModel):
    """Request model for AutoSchemaKG processing."""

    text_data: str
    batch_size_triple: int = 3
    batch_size_concept: int = 16
    max_new_tokens: int = 2048
    max_workers: int = 3
    output_directory: Optional[str] = None


class AutoSchemaKGResponse(BaseModel):
    """Response model for AutoSchemaKG processing."""

    success: bool
    job_id: str
    output_directory: str
    node_count: int
    edge_count: int
    concept_count: int
    message: str


class AutoSchemaKGStatsResponse(BaseModel):
    """Response model for AutoSchemaKG statistics."""

    available: bool
    neo4j_connected: bool
    atlas_version: Optional[str] = None
    graph_stats: dict[str, Any]


@router.get("/stats", response_model=AutoSchemaKGStatsResponse)
async def get_autoschema_kg_stats(
    graph_service: GraphService = Depends(get_graph_service),
) -> AutoSchemaKGStatsResponse:
    """Get AutoSchemaKG system statistics and availability."""
    try:
        settings = get_settings()

        if not settings.graph.enabled:
            return AutoSchemaKGStatsResponse(
                available=False,
                neo4j_connected=False,
                atlas_version=None,
                graph_stats={"message": "Graph processing is disabled"},
            )

        # Check if AutoSchemaKG libraries are available
        try:
            from atlas_rag.kg_construction.triple_config import ProcessingConfig
            from atlas_rag.kg_construction.triple_extraction import KnowledgeGraphExtractor

            atlas_available = True
            atlas_version = "1.0.0"  # You might want to get this from the package
        except ImportError as e:
            atlas_available = False
            atlas_version = None
            logger.warning(f"AutoSchemaKG libraries not available: {e}")

        # Get graph database stats
        try:
            stats = await graph_service.get_database_stats()
            neo4j_connected = True
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            stats = {"error": str(e)}
            neo4j_connected = False

        return AutoSchemaKGStatsResponse(
            available=atlas_available,
            neo4j_connected=neo4j_connected,
            atlas_version=atlas_version,
            graph_stats=stats,
        )

    except Exception as e:
        logger.error(f"Failed to get AutoSchemaKG stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve AutoSchemaKG statistics: {str(e)}"
        )


@router.post("/extract", response_model=AutoSchemaKGResponse)
async def extract_knowledge_graph(
    request: AutoSchemaKGRequest,
    graph_service: GraphService = Depends(get_graph_service),
) -> AutoSchemaKGResponse:
    """Extract knowledge graph from text using AutoSchemaKG."""
    try:
        settings = get_settings()

        if not settings.graph.enabled:
            raise HTTPException(status_code=503, detail="Graph processing is disabled")

        # Check if AutoSchemaKG libraries are available
        try:
            from atlas_rag.kg_construction.triple_config import ProcessingConfig
            from atlas_rag.kg_construction.triple_extraction import KnowledgeGraphExtractor
            from atlas_rag.llm_generator import LLMGenerator
            from openai import OpenAI
        except ImportError as e:
            raise HTTPException(
                status_code=503, detail=f"AutoSchemaKG libraries not available: {e}"
            )

        # Generate unique job ID
        import uuid

        job_id = f"autoschema_{uuid.uuid4().hex[:8]}"

        # Set up output directory
        if request.output_directory:
            output_directory = request.output_directory
        else:
            output_directory = os.path.join(tempfile.gettempdir(), "autoschema_kg", job_id)

        os.makedirs(output_directory, exist_ok=True)

        # Write text data to a JSONL file (required format for AutoSchemaKG)
        data_directory = os.path.join(output_directory, "data")
        os.makedirs(data_directory, exist_ok=True)
        input_file = os.path.join(data_directory, f"{job_id}.jsonl")

        import json

        with open(input_file, "w", encoding="utf-8") as f:
            json_line = {
                "id": job_id,
                "text": request.text_data,
                "metadata": {"source": "api_request", "type": "text_extraction"},
            }
            f.write(json.dumps(json_line) + "\n")

        # Set up LLM client - using OpenRouter configuration from settings
        if settings.graph.llm_provider == "openrouter":
            if not settings.graph.llm_api_key:
                raise HTTPException(
                    status_code=400,
                    detail="LLM API key not configured. Please set GRAPH_LLM_API_KEY.",
                )

            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=settings.graph.llm_api_key,
            )
        elif settings.graph.llm_provider == "openai":
            client = OpenAI(
                api_key=settings.graph.llm_api_key,
                base_url=settings.graph.llm_api_base if settings.graph.llm_api_base else None,
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported LLM provider: {settings.graph.llm_provider}"
            )

        # Initialize LLM generator
        triple_generator = LLMGenerator(client=client, model_name=settings.graph.llm_model)

        # Configure processing
        kg_extraction_config = ProcessingConfig(
            model_path=settings.graph.llm_model,
            data_directory=data_directory,
            filename_pattern=job_id,
            batch_size_triple=request.batch_size_triple,
            batch_size_concept=request.batch_size_concept,
            output_directory=output_directory,
            max_new_tokens=request.max_new_tokens,
            max_workers=request.max_workers,
            remove_doc_spaces=True,
        )

        # Initialize knowledge graph extractor
        kg_extractor = KnowledgeGraphExtractor(model=triple_generator, config=kg_extraction_config)

        logger.info(f"Starting AutoSchemaKG extraction for job {job_id}")

        # Run the extraction pipeline
        try:
            # Extract triples
            kg_extractor.run_extraction()

            # Convert to CSV format
            kg_extractor.convert_json_to_csv()

            # Generate concepts
            kg_extractor.generate_concept_csv_temp(batch_size=request.batch_size_concept)

            # Create concept CSV
            kg_extractor.create_concept_csv()

            # Convert to GraphML for Neo4j import
            kg_extractor.convert_to_graphml()

            logger.info(f"AutoSchemaKG extraction completed for job {job_id}")

        except Exception as e:
            logger.error(f"AutoSchemaKG extraction failed for job {job_id}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Knowledge graph extraction failed: {str(e)}"
            )

        # Get statistics about the generated graph
        try:
            node_count = await _count_nodes_in_output(output_directory)
            edge_count = await _count_edges_in_output(output_directory)
            concept_count = await _count_concepts_in_output(output_directory)
        except Exception as e:
            logger.warning(f"Failed to get output statistics: {e}")
            node_count = edge_count = concept_count = -1

        return AutoSchemaKGResponse(
            success=True,
            job_id=job_id,
            output_directory=output_directory,
            node_count=node_count,
            edge_count=edge_count,
            concept_count=concept_count,
            message=f"Knowledge graph extraction completed successfully. Output saved to {output_directory}",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AutoSchemaKG extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Knowledge graph extraction failed: {str(e)}")


@router.post("/load-to-neo4j/{job_id}")
async def load_to_neo4j(
    job_id: str,
    output_directory: str = Query(..., description="Directory containing AutoSchemaKG output"),
    graph_service: GraphService = Depends(get_graph_service),
) -> dict[str, Any]:
    """Load AutoSchemaKG output into Neo4j database."""
    try:
        settings = get_settings()

        if not settings.graph.enabled:
            raise HTTPException(status_code=503, detail="Graph processing is disabled")

        # Check if output directory exists
        if not os.path.exists(output_directory):
            raise HTTPException(
                status_code=404, detail=f"Output directory not found: {output_directory}"
            )

        # Import CSV files into Neo4j
        try:
            from app.services.autoschema_neo4j_loader import AutoSchemaNeo4jLoader

            loader = AutoSchemaNeo4jLoader()
            result = await loader.load_csv_data(output_directory, job_id)

            return {
                "success": True,
                "job_id": job_id,
                "nodes_loaded": result.get("nodes_loaded", 0),
                "relationships_loaded": result.get("relationships_loaded", 0),
                "message": "Data successfully loaded into Neo4j",
            }

        except ImportError:
            # Fallback to basic CSV loading
            result = await _load_csv_to_neo4j_basic(output_directory, job_id, graph_service)
            return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load AutoSchemaKG output to Neo4j: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load data to Neo4j: {str(e)}")


async def _count_nodes_in_output(output_directory: str) -> int:
    """Count nodes in AutoSchemaKG output."""
    try:
        import json

        # Look for JSON files with node data
        for filename in os.listdir(output_directory):
            if filename.endswith("_nodes.json"):
                with open(os.path.join(output_directory, filename), "r") as f:
                    data = json.load(f)
                    return len(data) if isinstance(data, list) else len(data.get("nodes", []))

        # Fallback: try to count from CSV
        for filename in os.listdir(output_directory):
            if filename.endswith("_nodes.csv"):
                import csv

                with open(os.path.join(output_directory, filename), "r") as f:
                    return sum(1 for _ in csv.reader(f)) - 1  # Subtract header

        return 0
    except Exception:
        return -1


async def _count_edges_in_output(output_directory: str) -> int:
    """Count edges in AutoSchemaKG output."""
    try:
        import json

        # Look for JSON files with edge data
        for filename in os.listdir(output_directory):
            if filename.endswith("_edges.json") or filename.endswith("_relations.json"):
                with open(os.path.join(output_directory, filename), "r") as f:
                    data = json.load(f)
                    return len(data) if isinstance(data, list) else len(data.get("edges", []))

        # Fallback: try to count from CSV
        for filename in os.listdir(output_directory):
            if filename.endswith("_edges.csv") or filename.endswith("_relations.csv"):
                import csv

                with open(os.path.join(output_directory, filename), "r") as f:
                    return sum(1 for _ in csv.reader(f)) - 1  # Subtract header

        return 0
    except Exception:
        return -1


async def _count_concepts_in_output(output_directory: str) -> int:
    """Count concepts in AutoSchemaKG output."""
    try:
        import json

        # Look for JSON files with concept data
        for filename in os.listdir(output_directory):
            if filename.endswith("_concepts.json"):
                with open(os.path.join(output_directory, filename), "r") as f:
                    data = json.load(f)
                    return len(data) if isinstance(data, list) else len(data.get("concepts", []))

        # Fallback: try to count from CSV
        for filename in os.listdir(output_directory):
            if filename.endswith("_concepts.csv"):
                import csv

                with open(os.path.join(output_directory, filename), "r") as f:
                    return sum(1 for _ in csv.reader(f)) - 1  # Subtract header

        return 0
    except Exception:
        return -1


async def _load_csv_to_neo4j_basic(
    output_directory: str, job_id: str, graph_service: GraphService
) -> dict[str, Any]:
    """Basic CSV loading to Neo4j (fallback implementation)."""
    try:
        # This is a basic implementation - you might want to create a more sophisticated loader
        nodes_loaded = 0
        relationships_loaded = 0

        # Look for CSV files and load them
        for filename in os.listdir(output_directory):
            if filename.endswith(".csv"):
                csv_path = os.path.join(output_directory, filename)

                if "node" in filename.lower():
                    # Load nodes using the correct method
                    query = f"""
                    LOAD CSV WITH HEADERS FROM 'file:///{csv_path}' AS row
                    CREATE (n:AutoSchemaNode {{
                        job_id: '{job_id}',
                        text: row.text,
                        type: row.type
                    }})
                    """
                    # Get the graph manager and execute write transaction
                    manager = await get_graph_db_manager()
                    if not manager.is_connected:
                        await manager.initialize()
                    result = await manager.execute_write_transaction(query)
                    nodes_loaded += 1

                elif "edge" in filename.lower() or "relation" in filename.lower():
                    # Load relationships using the correct method
                    query = f"""
                    LOAD CSV WITH HEADERS FROM 'file:///{csv_path}' AS row
                    MATCH (a:AutoSchemaNode {{text: row.source, job_id: '{job_id}'}})
                    MATCH (b:AutoSchemaNode {{text: row.target, job_id: '{job_id}'}})
                    CREATE (a)-[r:AUTOSCHEMA_RELATION {{
                        type: row.relation,
                        job_id: '{job_id}'
                    }}]->(b)
                    """
                    # Get the graph manager and execute write transaction
                    manager = await get_graph_db_manager()
                    if not manager.is_connected:
                        await manager.initialize()
                    result = await manager.execute_write_transaction(query)
                    relationships_loaded += 1

        return {
            "nodes_loaded": nodes_loaded,
            "relationships_loaded": relationships_loaded,
            "files_processed": nodes_loaded + relationships_loaded,
        }

    except Exception as e:
        logger.error(f"Error loading CSV to Neo4j: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load data to Neo4j: {str(e)}")
