"""Unit tests for graph service functionality."""

from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.graph_processor import GraphProcessor
from app.schemas.graph import (
    ConversationNode,
    EntityNode,
    NodeType,
    RelationshipType,
    SpeakerNode,
    TopicNode,
    TranscriptSegmentNode,
)
from app.services.graph_service import GraphService


@pytest.fixture
def mock_neo4j_session():
    """Mock Neo4j session."""
    session = AsyncMock()
    session.run = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_graph_enabled():
    """Mock graph enabled configuration."""
    with patch("app.config.settings.get_settings") as mock_settings:
        mock_settings.return_value.graph.enabled = True
        mock_settings.return_value.graph.neo4j.url = "bolt://localhost:7687"
        mock_settings.return_value.graph.neo4j.username = "neo4j"
        mock_settings.return_value.graph.neo4j.password = "password"
        yield mock_settings


@pytest.fixture
def mock_graph_disabled():
    """Mock graph disabled configuration."""
    with patch("app.config.settings.get_settings") as mock_settings:
        mock_settings.return_value.graph.enabled = False
        yield mock_settings


@pytest.fixture
def sample_transcription_result():
    """Sample transcription result for testing."""
    return {
        "request_id": "test-request-123",
        "conversation_id": "conv-456",
        "segments": [
            {
                "start": 0.0,
                "end": 3.5,
                "text": "Hello, this is John speaking.",
                "speaker": "Speaker_1",
                "speaker_id": "john-doe",
            },
            {
                "start": 3.5,
                "end": 8.2,
                "text": "Hi John, this is Jane. How are you?",
                "speaker": "Speaker_2",
                "speaker_id": "jane-smith",
            },
        ],
        "metadata": {"duration": 10.0, "language": "en"},
    }


class TestGraphService:
    """Test cases for GraphService."""

    @pytest.mark.asyncio
    async def test_graph_service_initialization_enabled(
        self, mock_graph_enabled, mock_neo4j_session
    ):
        """Test GraphService initialization when graph is enabled."""
        with patch(
            "app.db.neo4j_session.get_neo4j_session", return_value=mock_neo4j_session
        ):
            service = GraphService()
            assert service._enabled is True
            assert service._neo4j_session == mock_neo4j_session

    @pytest.mark.asyncio
    async def test_graph_service_initialization_disabled(self, mock_graph_disabled):
        """Test GraphService initialization when graph is disabled."""
        service = GraphService()
        assert service._enabled is False
        assert service._neo4j_session is None

    @pytest.mark.asyncio
    async def test_create_speaker_node(self, mock_graph_enabled, mock_neo4j_session):
        """Test creating a speaker node."""
        with patch(
            "app.db.neo4j_session.get_neo4j_session", return_value=mock_neo4j_session
        ):
            service = GraphService()

            speaker_data = {
                "speaker_id": "john-doe",
                "name": "John Doe",
                "total_speaking_time": 120.5,
                "segment_count": 5,
            }

            await service.create_speaker_node(speaker_data)

            mock_neo4j_session.run.assert_called_once()
            call_args = mock_neo4j_session.run.call_args
            assert "CREATE" in call_args[0][0]
            assert "Speaker" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_create_speaker_node_disabled(self, mock_graph_disabled):
        """Test creating a speaker node when graph is disabled."""
        service = GraphService()

        speaker_data = {"speaker_id": "john-doe", "name": "John Doe"}
        result = await service.create_speaker_node(speaker_data)

        assert result is None  # Should return None when disabled

    @pytest.mark.asyncio
    async def test_get_speaker_network(self, mock_graph_enabled, mock_neo4j_session):
        """Test getting speaker network."""
        # Mock query result
        mock_record = MagicMock()
        mock_record.get.return_value = {
            "speaker_id": "john-doe",
            "name": "John Doe",
            "interactions": 3,
        }
        mock_neo4j_session.run.return_value.data.return_value = [mock_record]

        with patch(
            "app.db.neo4j_session.get_neo4j_session", return_value=mock_neo4j_session
        ):
            service = GraphService()
            result = await service.get_speaker_network("john-doe")

            assert result is not None
            mock_neo4j_session.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_conversation_graph(self, mock_graph_enabled, mock_neo4j_session):
        """Test getting conversation graph."""
        # Mock query result
        mock_record = MagicMock()
        mock_record.get.return_value = {
            "conversation_id": "conv-123",
            "speakers": ["john-doe", "jane-smith"],
            "topics": ["greeting", "business"],
        }
        mock_neo4j_session.run.return_value.data.return_value = [mock_record]

        with patch(
            "app.db.neo4j_session.get_neo4j_session", return_value=mock_neo4j_session
        ):
            service = GraphService()
            result = await service.get_conversation_graph("conv-123")

            assert result is not None
            mock_neo4j_session.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_graph_stats(self, mock_graph_enabled, mock_neo4j_session):
        """Test getting graph statistics."""
        # Mock query results
        mock_neo4j_session.run.return_value.single.return_value = {"count": 10}

        with patch(
            "app.db.neo4j_session.get_neo4j_session", return_value=mock_neo4j_session
        ):
            service = GraphService()
            stats = await service.get_graph_stats()

            assert stats is not None
            assert "enabled" in stats
            assert stats["enabled"] is True

    @pytest.mark.asyncio
    async def test_get_graph_stats_disabled(self, mock_graph_disabled):
        """Test getting graph statistics when disabled."""
        service = GraphService()
        stats = await service.get_graph_stats()

        assert stats["enabled"] is False
        assert "stats" not in stats or stats["stats"] == {}


class TestGraphProcessor:
    """Test cases for GraphProcessor."""

    @pytest.fixture
    def graph_processor(self):
        """Create GraphProcessor instance."""
        return GraphProcessor()

    def test_extract_speaker_data(self, graph_processor, sample_transcription_result):
        """Test extracting speaker data from transcription result."""
        speakers = graph_processor.extract_speaker_data(sample_transcription_result)

        assert len(speakers) == 2
        assert speakers[0]["speaker_id"] == "john-doe"
        assert speakers[1]["speaker_id"] == "jane-smith"
        assert speakers[0]["total_speaking_time"] == 3.5
        assert speakers[1]["total_speaking_time"] == 4.7

    def test_extract_topics(self, graph_processor, sample_transcription_result):
        """Test extracting topics from transcription result."""
        topics = graph_processor.extract_topics(sample_transcription_result)

        assert len(topics) > 0
        # Should extract topics based on keywords in the text
        topic_names = [topic["name"] for topic in topics]
        assert any("greeting" in topic_name.lower() for topic_name in topic_names)

    def test_extract_entities(self, graph_processor):
        """Test extracting entities from text."""
        text = "Contact me at john@example.com or call 555-123-4567"
        entities = graph_processor.extract_entities(text)

        assert len(entities) >= 2
        entity_values = [entity["value"] for entity in entities]
        assert "john@example.com" in entity_values
        assert "555-123-4567" in entity_values

    def test_extract_speaker_interactions(
        self, graph_processor, sample_transcription_result
    ):
        """Test extracting speaker interactions."""
        interactions = graph_processor.extract_speaker_interactions(
            sample_transcription_result
        )

        assert len(interactions) >= 1
        # Should have interaction between john-doe and jane-smith
        interaction = interactions[0]
        assert set([interaction["from_speaker"], interaction["to_speaker"]]) == {
            "john-doe",
            "jane-smith",
        }

    def test_process_transcription_result(
        self, graph_processor, sample_transcription_result
    ):
        """Test processing complete transcription result."""
        graph_data = graph_processor.process_transcription_result(
            sample_transcription_result
        )

        assert "speakers" in graph_data
        assert "topics" in graph_data
        assert "entities" in graph_data
        assert "interactions" in graph_data
        assert "conversation" in graph_data

        assert len(graph_data["speakers"]) == 2
        assert graph_data["conversation"]["conversation_id"] == "conv-456"


class TestGraphServiceIntegration:
    """Integration tests for graph service with mock Neo4j."""

    @pytest.mark.asyncio
    async def test_process_and_store_transcription_result(
        self, mock_graph_enabled, mock_neo4j_session, sample_transcription_result
    ):
        """Test processing and storing a complete transcription result."""
        with patch(
            "app.db.neo4j_session.get_neo4j_session", return_value=mock_neo4j_session
        ):
            service = GraphService()
            processor = GraphProcessor()

            # Process transcription result
            graph_data = processor.process_transcription_result(
                sample_transcription_result
            )

            # Store in graph database
            await service.store_conversation_graph(graph_data)

            # Verify multiple Neo4j operations were called
            assert (
                mock_neo4j_session.run.call_count >= 4
            )  # speakers, topics, entities, conversation

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_neo4j_error(
        self, mock_graph_enabled, mock_neo4j_session
    ):
        """Test graceful degradation when Neo4j operations fail."""
        # Mock Neo4j to raise an exception
        mock_neo4j_session.run.side_effect = Exception("Neo4j connection failed")

        with patch(
            "app.db.neo4j_session.get_neo4j_session", return_value=mock_neo4j_session
        ):
            service = GraphService()

            # Should not raise exception, but handle gracefully
            result = await service.create_speaker_node(
                {"speaker_id": "test", "name": "Test"}
            )
            assert result is None  # Should return None on error

    @pytest.mark.asyncio
    async def test_batch_operations(self, mock_graph_enabled, mock_neo4j_session):
        """Test batch operations for performance."""
        with patch(
            "app.db.neo4j_session.get_neo4j_session", return_value=mock_neo4j_session
        ):
            service = GraphService()

            speakers = [
                {"speaker_id": "speaker1", "name": "Speaker 1"},
                {"speaker_id": "speaker2", "name": "Speaker 2"},
                {"speaker_id": "speaker3", "name": "Speaker 3"},
            ]

            await service.create_multiple_speakers(speakers)

            # Should use batch operation instead of individual calls
            assert mock_neo4j_session.run.call_count == 1  # Single batch operation
