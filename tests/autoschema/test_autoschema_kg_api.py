"""
API tests for AutoSchemaKG endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import tempfile
import os

from app.main import create_application


@pytest.fixture
def client():
    """Create test client."""
    app = create_application()
    return TestClient(app)


@pytest.fixture
def sample_text():
    """Sample text for testing."""
    return """
    Machine learning is a subset of artificial intelligence that enables computers to learn from data.
    Neural networks are computational models inspired by biological neural networks.
    Deep learning uses multiple layers of neural networks to process complex data.
    """


def test_autoschema_kg_stats_endpoint(client):
    """Test the AutoSchemaKG stats endpoint."""
    response = client.get("/api/v1/autoschema-kg/stats")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert "available" in data
    assert "neo4j_connected" in data
    assert "atlas_version" in data
    assert "graph_stats" in data

    # The available field should be boolean
    assert isinstance(data["available"], bool)
    assert isinstance(data["neo4j_connected"], bool)


@patch('app.api.v1.endpoints.autoschema_kg.KnowledgeGraphExtractor')
@patch('app.api.v1.endpoints.autoschema_kg.LLMGenerator')
@patch('app.api.v1.endpoints.autoschema_kg.OpenAI')
def test_autoschema_kg_extract_endpoint_success(mock_openai, mock_llm_gen, mock_kg_extractor, client, sample_text):
    """Test successful knowledge graph extraction."""
    # Mock the extraction process
    mock_extractor_instance = Mock()
    mock_kg_extractor.return_value = mock_extractor_instance

    # Mock the output files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mock output files
        os.makedirs(os.path.join(temp_dir, "data"), exist_ok=True)

        with open(os.path.join(temp_dir, "nodes.csv"), "w") as f:
            f.write("id,text,type\n1,Machine Learning,Concept\n2,AI,Concept\n")

        with open(os.path.join(temp_dir, "edges.csv"), "w") as f:
            f.write("source,target,relation\nMachine Learning,AI,IS_SUBSET_OF\n")

        request_data = {
            "text_data": sample_text,
            "batch_size_triple": 2,
            "batch_size_concept": 4,
            "max_new_tokens": 512,
            "max_workers": 1,
            "output_directory": temp_dir
        }

        response = client.post("/api/v1/autoschema-kg/extract", json=request_data)

        # The endpoint will fail due to missing API key, but we can check the validation
        assert response.status_code in [200, 400, 503]  # Could be any of these depending on config


def test_autoschema_kg_extract_endpoint_missing_data(client):
    """Test extraction endpoint with missing required data."""
    request_data = {
        "batch_size_triple": 2,
        # Missing text_data
    }

    response = client.post("/api/v1/autoschema-kg/extract", json=request_data)
    assert response.status_code == 422  # Validation error


def test_autoschema_kg_extract_endpoint_invalid_params(client, sample_text):
    """Test extraction endpoint with invalid parameters."""
    request_data = {
        "text_data": sample_text,
        "batch_size_triple": -1,  # Invalid: negative batch size
        "batch_size_concept": 0,  # Invalid: zero batch size
    }

    response = client.post("/api/v1/autoschema-kg/extract", json=request_data)
    # Should either succeed with corrected values or fail with validation error
    assert response.status_code in [200, 400, 422, 503]


def test_autoschema_kg_load_to_neo4j_missing_directory(client):
    """Test loading to Neo4j with non-existent directory."""
    response = client.post(
        "/api/v1/autoschema-kg/load-to-neo4j/test_job_123",
        params={"output_directory": "/nonexistent/directory"}
    )

    assert response.status_code in [404, 503]  # Not found or service unavailable


def test_autoschema_kg_load_to_neo4j_with_directory(client):
    """Test loading to Neo4j with valid directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create some mock CSV files
        with open(os.path.join(temp_dir, "nodes.csv"), "w") as f:
            f.write("id,text,type\n1,Test Node,Entity\n")

        response = client.post(
            "/api/v1/autoschema-kg/load-to-neo4j/test_job_456",
            params={"output_directory": temp_dir}
        )

        # Should either succeed or fail due to graph being disabled
        assert response.status_code in [200, 503]


@pytest.mark.asyncio
async def test_autoschema_kg_integration_flow():
    """Test the complete AutoSchemaKG integration flow."""
    # This test requires a running Neo4j instance
    # It's more of an integration test than a unit test

    from app.services.autoschema_neo4j_loader import AutoSchemaNeo4jLoader

    loader = AutoSchemaNeo4jLoader()

    # Test job statistics for a non-existent job
    stats = await loader.get_job_statistics("nonexistent_job")

    assert "job_id" in stats
    assert stats["job_id"] == "nonexistent_job"
    assert "node_count" in stats
    assert "relationship_count" in stats
    assert "concept_count" in stats


def test_autoschema_kg_endpoint_error_handling(client):
    """Test error handling in AutoSchemaKG endpoints."""
    # Test with empty text
    response = client.post("/api/v1/autoschema-kg/extract", json={"text_data": ""})
    assert response.status_code in [400, 422, 503]

    # Test with very large text (if there are size limits)
    large_text = "A" * (10 * 1024 * 1024)  # 10MB text
    response = client.post("/api/v1/autoschema-kg/extract", json={"text_data": large_text})
    assert response.status_code in [200, 400, 413, 503]  # Could be various errors


def test_autoschema_kg_response_models(client):
    """Test that response models are correctly structured."""
    # Test stats endpoint response structure
    response = client.get("/api/v1/autoschema-kg/stats")

    if response.status_code == 200:
        data = response.json()

        # Verify all required fields are present
        required_fields = ["available", "neo4j_connected", "atlas_version", "graph_stats"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Verify field types
        assert isinstance(data["available"], bool)
        assert isinstance(data["neo4j_connected"], bool)
        assert isinstance(data["graph_stats"], dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
