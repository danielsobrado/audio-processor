# AutoSchemaKG Integration Guide

This guide explains how to use the AutoSchemaKG (Autonomous Knowledge Graph Construction) functionality integrated into the audio processor application.

## Overview

AutoSchemaKG is a powerful framework for automatically constructing knowledge graphs from unstructured text without requiring predefined schemas. Our integration allows you to:

1. **Extract knowledge graphs** from transcription results or any text data
2. **Load graphs into Neo4j** for visualization and querying
3. **Query and analyze** the generated knowledge structures
4. **Integrate with existing** audio processing workflows

## Prerequisites

### 1. Install AutoSchemaKG Dependencies

```bash
# Install the atlas-rag package (contains AutoSchemaKG)
pip install atlas-rag

# Or using uv
uv add atlas-rag
```

### 2. Set up Neo4j Database

Start a Neo4j instance using Docker:

```bash
docker run -d --name neo4j-autoschema \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  --rm neo4j:5-community
```

### 3. Configure Environment Variables

Set up your environment configuration:

```bash
# Enable graph processing
export GRAPH_ENABLED=true

# Neo4j connection
export GRAPH_DATABASE_URL=bolt://localhost:7687
export GRAPH_DATABASE_USERNAME=neo4j
export GRAPH_DATABASE_PASSWORD=password

# LLM configuration for AutoSchemaKG
export GRAPH_LLM_PROVIDER=openrouter  # or 'openai'
export GRAPH_LLM_MODEL=meta-llama/llama-3.2-3b-instruct
export GRAPH_LLM_API_KEY=your-api-key-here
```

## API Endpoints

### 1. Check AutoSchemaKG Status

Get information about AutoSchemaKG availability and configuration:

```bash
curl -X GET "http://localhost:8000/api/v1/autoschema-kg/stats"
```

Response:
```json
{
  "available": true,
  "neo4j_connected": true,
  "atlas_version": "1.0.0",
  "graph_stats": {
    "nodes": 1250,
    "relationships": 3840,
    "database_type": "neo4j",
    "enabled": true
  }
}
```

### 2. Extract Knowledge Graph from Text

Process text data to extract entities, relationships, and concepts:

```bash
curl -X POST "http://localhost:8000/api/v1/autoschema-kg/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "text_data": "Artificial Intelligence is transforming healthcare. Machine learning algorithms can analyze medical images to detect diseases early. Deep learning models are particularly effective in radiology and pathology.",
    "batch_size_triple": 3,
    "batch_size_concept": 16,
    "max_new_tokens": 2048,
    "max_workers": 3
  }'
```

Response:
```json
{
  "success": true,
  "job_id": "autoschema_a1b2c3d4",
  "output_directory": "/tmp/autoschema_kg/autoschema_a1b2c3d4",
  "node_count": 15,
  "edge_count": 23,
  "concept_count": 8,
  "message": "Knowledge graph extraction completed successfully."
}
```

### 3. Load Extracted Data into Neo4j

Load the extracted knowledge graph into Neo4j for querying:

```bash
curl -X POST "http://localhost:8000/api/v1/autoschema-kg/load-to-neo4j/autoschema_a1b2c3d4" \
  -G -d "output_directory=/tmp/autoschema_kg/autoschema_a1b2c3d4"
```

Response:
```json
{
  "success": true,
  "job_id": "autoschema_a1b2c3d4",
  "nodes_loaded": 15,
  "relationships_loaded": 23,
  "message": "Data successfully loaded into Neo4j"
}
```

## Python API Usage

### Direct Integration in Your Code

```python
import asyncio
from app.services.autoschema_neo4j_loader import AutoSchemaNeo4jLoader
from atlas_rag.kg_construction.triple_extraction import KnowledgeGraphExtractor
from atlas_rag.kg_construction.triple_config import ProcessingConfig
from atlas_rag.llm_generator import LLMGenerator
from openai import OpenAI

async def extract_and_load_knowledge_graph(text_data: str):
    """Extract knowledge graph from text and load into Neo4j."""

    # Set up LLM client
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="your-api-key"
    )

    # Create LLM generator
    llm_generator = LLMGenerator(
        client=client,
        model_name="meta-llama/llama-3.2-3b-instruct"
    )

    # Configure processing
    config = ProcessingConfig(
        model_path="meta-llama/llama-3.2-3b-instruct",
        data_directory="./data",
        filename_pattern="sample",
        batch_size_triple=3,
        batch_size_concept=16,
        output_directory="./output",
        max_new_tokens=2048,
        max_workers=3
    )

    # Extract knowledge graph
    kg_extractor = KnowledgeGraphExtractor(model=llm_generator, config=config)
    kg_extractor.run_extraction()
    kg_extractor.convert_json_to_csv()
    kg_extractor.generate_concept_csv()
    kg_extractor.create_concept_csv()

    # Load into Neo4j
    loader = AutoSchemaNeo4jLoader()
    result = await loader.load_csv_data("./output", "my_job_id")

    return result

# Run the extraction
asyncio.run(extract_and_load_knowledge_graph("Your text here..."))
```

## Querying the Knowledge Graph

### Neo4j Browser Queries

Access Neo4j Browser at `http://localhost:7474` and use these Cypher queries:

#### 1. View All AutoSchemaKG Nodes

```cypher
MATCH (n:AutoSchemaNode)
RETURN n.job_id, n.text, n.type, n.confidence
LIMIT 20
```

#### 2. View Relationships Between Entities

```cypher
MATCH (a:AutoSchemaNode)-[r:AUTOSCHEMA_RELATION]->(b:AutoSchemaNode)
RETURN a.text as source, r.type as relation, b.text as target, r.confidence
LIMIT 20
```

#### 3. Find Entities of Specific Types

```cypher
MATCH (n:AutoSchemaNode {type: 'PERSON'})
RETURN n.text, n.confidence
ORDER BY n.confidence DESC
```

#### 4. Explore Concept Hierarchies

```cypher
MATCH (c:AutoSchemaConcept)
RETURN c.name, c.category, c.description
ORDER BY c.category, c.name
```

#### 5. Find Connected Entity Clusters

```cypher
MATCH (n:AutoSchemaNode)-[*1..3]-(connected:AutoSchemaNode)
WHERE n.text CONTAINS 'AI'
RETURN n, connected
LIMIT 50
```

### Programmatic Queries

```python
from app.db.graph_session import get_graph_db_manager

async def query_knowledge_graph():
    """Query the knowledge graph programmatically."""

    manager = await get_graph_db_manager()
    if not manager.is_connected:
        await manager.initialize()

    # Find all entities related to a specific concept
    query = """
    MATCH (n:AutoSchemaNode)
    WHERE n.text CONTAINS $keyword
    OPTIONAL MATCH (n)-[r:AUTOSCHEMA_RELATION]-(connected)
    RETURN n.text as entity, collect(connected.text) as related_entities
    """

    result = await manager.execute_read_transaction(
        query,
        {"keyword": "artificial intelligence"}
    )

    return result
```

## Integration with Audio Processing

### Process Transcription Results

Integrate AutoSchemaKG with your transcription pipeline:

```python
from app.core.graph_processor import graph_processor

async def process_transcription_with_autoschema(transcription_result):
    """Process transcription and extract knowledge graph."""

    # Extract text from transcription segments
    full_text = " ".join([segment["text"] for segment in transcription_result["segments"]])

    # Use AutoSchemaKG API endpoint
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/v1/autoschema-kg/extract",
            json={
                "text_data": full_text,
                "batch_size_triple": 5,
                "batch_size_concept": 20
            }
        )

        if response.status_code == 200:
            result = response.json()
            job_id = result["job_id"]

            # Load into Neo4j
            load_response = await client.post(
                f"http://localhost:8000/api/v1/autoschema-kg/load-to-neo4j/{job_id}",
                params={"output_directory": result["output_directory"]}
            )

            return load_response.json()
```

## Testing

### Run the Test Suite

```bash
# Test AutoSchemaKG integration
python tests/test_autoschema_kg.py

# Test API endpoints (requires running server)
uv run uvicorn app.main:app --reload &
pytest tests/test_autoschema_kg_api.py -v
```

### Manual Testing Steps

1. **Start the application**:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

2. **Check status**:
   ```bash
   curl http://localhost:8000/api/v1/autoschema-kg/stats
   ```

3. **Extract knowledge graph**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/autoschema-kg/extract \
     -H "Content-Type: application/json" \
     -d '{"text_data": "Python is a programming language created by Guido van Rossum."}'
   ```

4. **View results in Neo4j Browser**:
   - Go to http://localhost:7474
   - Login with neo4j/password
   - Run: `MATCH (n:AutoSchemaNode) RETURN n LIMIT 10`

## Configuration Options

### Processing Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `batch_size_triple` | 3 | Batch size for triple extraction |
| `batch_size_concept` | 16 | Batch size for concept generation |
| `max_new_tokens` | 2048 | Maximum tokens for LLM generation |
| `max_workers` | 3 | Maximum concurrent workers |

### LLM Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `GRAPH_LLM_PROVIDER` | openrouter | LLM provider (openrouter, openai) |
| `GRAPH_LLM_MODEL` | llama-3.2-3b-instruct | Model name |
| `GRAPH_LLM_API_KEY` | - | API key for LLM service |
| `GRAPH_LLM_MAX_TOKENS` | 1000 | Max tokens per request |
| `GRAPH_LLM_TEMPERATURE` | 0.1 | Generation temperature |

## Troubleshooting

### Common Issues

1. **"AutoSchemaKG libraries not available"**
   ```bash
   pip install atlas-rag
   ```

2. **"Neo4j connection failed"**
   - Check if Neo4j is running: `docker ps`
   - Verify connection details in environment variables
   - Test connection: `curl http://localhost:7474`

3. **"LLM API key not configured"**
   - Set `GRAPH_LLM_API_KEY` environment variable
   - Verify API key is valid for your chosen provider

4. **"Extraction takes too long"**
   - Reduce `batch_size_triple` and `batch_size_concept`
   - Increase `max_workers` for parallel processing
   - Use a smaller, faster model

### Performance Optimization

1. **For large texts**: Split into smaller chunks
2. **For better quality**: Use larger, more capable models
3. **For speed**: Use smaller models with higher batch sizes
4. **For memory**: Reduce `max_workers` and batch sizes

## Advanced Usage

### Custom Entity Types

You can extend the knowledge graph with custom entity types by modifying the processing configuration or post-processing the results.

### Integration with Existing Graphs

AutoSchemaKG results can be integrated with existing Neo4j graphs using Cypher queries to create relationships between AutoSchemaKG nodes and your existing data.

### Batch Processing

For processing multiple documents, use the batch processing capabilities of AutoSchemaKG to efficiently extract knowledge graphs from large corpora.

## Support and Documentation

- **AutoSchemaKG Paper**: [arXiv:2505.23628](https://arxiv.org/abs/2505.23628)
- **Atlas RAG Documentation**: Check the `app/lib/autoschema_kg/README.md` file
- **Neo4j Documentation**: [neo4j.com/docs](https://neo4j.com/docs/)
- **Issues**: Report issues in the project repository
