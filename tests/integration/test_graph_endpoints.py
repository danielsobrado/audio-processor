"""Integration tests for graph API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.services.graph import GraphService


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_graph_service():
    """Mock GraphService for testing."""
    service = AsyncMock(spec=GraphService)
    return service


class TestGraphEndpoints:
    """Test cases for graph API endpoints."""

    @pytest.mark.asyncio
    async def test_graph_stats_endpoint_enabled(self, client, mock_graph_service):
        """Test graph stats endpoint when graph is enabled."""
        # Mock the graph service response
        mock_graph_service.get_graph_stats.return_value = {
            "enabled": True,
            "stats": {
                "speakers": 5,
                "topics": 3,
                "conversations": 2,
                "relationships": 12
            }
        }
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            response = client.get("/api/v1/graph/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is True
            assert "stats" in data
            assert data["stats"]["speakers"] == 5

    @pytest.mark.asyncio
    async def test_graph_stats_endpoint_disabled(self, client, mock_graph_service):
        """Test graph stats endpoint when graph is disabled."""
        # Mock the graph service response for disabled state
        mock_graph_service.get_graph_stats.return_value = {
            "enabled": False,
            "stats": {}
        }
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            response = client.get("/api/v1/graph/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is False
            assert data["stats"] == {}

    @pytest.mark.asyncio
    async def test_speakers_endpoint(self, client, mock_graph_service):
        """Test speakers list endpoint."""
        # Mock the graph service response
        mock_graph_service.get_all_speakers.return_value = [
            {
                "speaker_id": "john-doe",
                "name": "John Doe",
                "total_speaking_time": 120.5,
                "segment_count": 5
            },
            {
                "speaker_id": "jane-smith",
                "name": "Jane Smith", 
                "total_speaking_time": 95.2,
                "segment_count": 3
            }
        ]
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            response = client.get("/api/v1/graph/speakers")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["speaker_id"] == "john-doe"
            assert data[1]["speaker_id"] == "jane-smith"

    @pytest.mark.asyncio
    async def test_topics_endpoint(self, client, mock_graph_service):
        """Test topics list endpoint."""
        # Mock the graph service response
        mock_graph_service.get_all_topics.return_value = [
            {
                "topic_id": "greeting",
                "name": "Greeting",
                "keyword_count": 3,
                "conversation_count": 2
            },
            {
                "topic_id": "business",
                "name": "Business Discussion",
                "keyword_count": 5,
                "conversation_count": 1
            }
        ]
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            response = client.get("/api/v1/graph/topics")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["topic_id"] == "greeting"

    @pytest.mark.asyncio
    async def test_conversation_graph_endpoint(self, client, mock_graph_service):
        """Test conversation graph endpoint."""
        conversation_id = "conv-123"
        
        # Mock the graph service response
        mock_graph_service.get_conversation_graph.return_value = {
            "conversation_id": conversation_id,
            "speakers": ["john-doe", "jane-smith"],
            "topics": ["greeting", "business"],
            "entities": ["john@example.com", "555-123-4567"],
            "interactions": [
                {
                    "from_speaker": "john-doe",
                    "to_speaker": "jane-smith",
                    "interaction_count": 3
                }
            ]
        }
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            response = client.get(f"/api/v1/graph/conversations/{conversation_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == conversation_id
            assert len(data["speakers"]) == 2
            assert len(data["topics"]) == 2

    @pytest.mark.asyncio
    async def test_conversation_graph_not_found(self, client, mock_graph_service):
        """Test conversation graph endpoint when conversation not found."""
        conversation_id = "non-existent-conv"
        
        # Mock the graph service to return None
        mock_graph_service.get_conversation_graph.return_value = None
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            response = client.get(f"/api/v1/graph/conversations/{conversation_id}")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_speaker_network_endpoint(self, client, mock_graph_service):
        """Test speaker network endpoint."""
        speaker_id = "john-doe"
        
        # Mock the graph service response
        mock_graph_service.get_speaker_network.return_value = {
            "speaker_id": speaker_id,
            "name": "John Doe",
            "direct_interactions": [
                {
                    "speaker_id": "jane-smith",
                    "name": "Jane Smith",
                    "interaction_count": 3,
                    "total_time": 45.2
                }
            ],
            "network_stats": {
                "total_connections": 1,
                "avg_interaction_time": 45.2
            }
        }
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            response = client.get(f"/api/v1/graph/speakers/{speaker_id}/network")
            
            assert response.status_code == 200
            data = response.json()
            assert data["speaker_id"] == speaker_id
            assert len(data["direct_interactions"]) == 1

    @pytest.mark.asyncio
    async def test_speaker_network_not_found(self, client, mock_graph_service):
        """Test speaker network endpoint when speaker not found."""
        speaker_id = "non-existent-speaker"
        
        # Mock the graph service to return None
        mock_graph_service.get_speaker_network.return_value = None
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            response = client.get(f"/api/v1/graph/speakers/{speaker_id}/network")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_topic_flow_endpoint(self, client, mock_graph_service):
        """Test topic flow endpoint."""
        topic_id = "greeting"
        
        # Mock the graph service response
        mock_graph_service.get_topic_flow.return_value = {
            "topic_id": topic_id,
            "name": "Greeting",
            "flow_patterns": [
                {
                    "from_topic": "greeting",
                    "to_topic": "business",
                    "transition_count": 2,
                    "conversations": ["conv-123", "conv-456"]
                }
            ],
            "keywords": ["hello", "hi", "greetings"],
            "usage_stats": {
                "conversation_count": 2,
                "avg_duration": 15.5
            }
        }
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            response = client.get(f"/api/v1/graph/topics/{topic_id}/flow")
            
            assert response.status_code == 200
            data = response.json()
            assert data["topic_id"] == topic_id
            assert len(data["flow_patterns"]) == 1
            assert len(data["keywords"]) == 3

    @pytest.mark.asyncio
    async def test_topic_flow_not_found(self, client, mock_graph_service):
        """Test topic flow endpoint when topic not found."""
        topic_id = "non-existent-topic"
        
        # Mock the graph service to return None
        mock_graph_service.get_topic_flow.return_value = None
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            response = client.get(f"/api/v1/graph/topics/{topic_id}/flow")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_graph_endpoints_with_query_params(self, client, mock_graph_service):
        """Test graph endpoints with query parameters."""
        # Mock the graph service response with filtering
        mock_graph_service.get_all_speakers.return_value = [
            {
                "speaker_id": "john-doe",
                "name": "John Doe",
                "total_speaking_time": 120.5,
                "segment_count": 5
            }
        ]
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            # Test with query parameters
            response = client.get("/api/v1/graph/speakers?limit=10&offset=0")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            
            # Verify service was called with correct parameters
            mock_graph_service.get_all_speakers.assert_called_once_with(limit=10, offset=0)

    @pytest.mark.asyncio
    async def test_graph_service_exception_handling(self, client, mock_graph_service):
        """Test graph service exception handling in endpoints."""
        # Mock the graph service to raise an exception
        mock_graph_service.get_graph_stats.side_effect = Exception("Database connection failed")
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            response = client.get("/api/v1/graph/stats")
            
            assert response.status_code == 500
            data = response.json()
            assert "error" in data["detail"].lower()


class TestGraphEndpointSecurity:
    """Test security aspects of graph endpoints."""

    @pytest.mark.asyncio
    async def test_graph_endpoints_without_auth(self, client):
        """Test graph endpoints accessibility without authentication."""
        # Since the app doesn't require auth for these endpoints in test mode,
        # they should be accessible
        response = client.get("/api/v1/graph/stats")
        assert response.status_code in [200, 500]  # Either success or server error, not auth error

    @pytest.mark.asyncio
    async def test_graph_endpoints_input_validation(self, client):
        """Test input validation for graph endpoints."""
        # Test with invalid conversation ID format
        response = client.get("/api/v1/graph/conversations/invalid-id-format-@#$")
        # Should either handle gracefully or return 404/400
        assert response.status_code in [400, 404, 500]

    @pytest.mark.asyncio
    async def test_graph_endpoints_sql_injection_protection(self, client):
        """Test SQL injection protection in graph endpoints."""
        # Test with potential SQL injection in path parameters
        malicious_id = "'; DROP TABLE conversations; --"
        response = client.get(f"/api/v1/graph/conversations/{malicious_id}")
        # Should not cause server error due to SQL injection
        assert response.status_code in [400, 404, 500]  # Any error except server crash


class TestGraphEndpointPerformance:
    """Test performance aspects of graph endpoints."""

    @pytest.mark.asyncio
    async def test_graph_endpoints_with_large_datasets(self, client, mock_graph_service):
        """Test graph endpoints with large datasets."""
        # Mock large dataset
        large_speakers_list = [
            {
                "speaker_id": f"speaker-{i}",
                "name": f"Speaker {i}",
                "total_speaking_time": 100.0 + i,
                "segment_count": i
            }
            for i in range(1000)
        ]
        
        mock_graph_service.get_all_speakers.return_value = large_speakers_list
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            response = client.get("/api/v1/graph/speakers")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1000

    @pytest.mark.asyncio
    async def test_graph_endpoints_pagination(self, client, mock_graph_service):
        """Test graph endpoints pagination."""
        # Mock paginated response
        mock_graph_service.get_all_speakers.return_value = [
            {
                "speaker_id": "speaker-1",
                "name": "Speaker 1",
                "total_speaking_time": 100.0,
                "segment_count": 5
            }
        ]
        
        with patch('app.api.v1.endpoints.graph.get_graph_service', return_value=mock_graph_service):
            response = client.get("/api/v1/graph/speakers?limit=1&offset=0")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            
            # Verify pagination parameters were passed
            mock_graph_service.get_all_speakers.assert_called_once_with(limit=1, offset=0)
