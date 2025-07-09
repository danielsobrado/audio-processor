"""Graph API endpoints for graph database queries."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.schemas.api import (
    SimilarSpeakerResponse,
    SpeakerProfileResponse,
    TopicCooccurrenceResponse,
    TopicProfileResponse,
    TopSpeakerResponse,
    TrendingTopicResponse,
)
from app.schemas.graph import RelationshipType
from app.services.graph_service import GraphService, get_graph_service
from app.services.speaker_graph import SpeakerGraphService, get_speaker_graph_service
from app.services.topic_graph import TopicGraphService, get_topic_graph_service

logger = logging.getLogger(__name__)

router = APIRouter()


class GraphStatsResponse(BaseModel):
    """Response model for graph statistics."""

    enabled: bool
    stats: Dict[str, Any]


class ConversationGraphResponse(BaseModel):
    """Response model for conversation graph data."""

    conversation_id: str
    graph_data: Dict[str, Any]


class SpeakerNetworkResponse(BaseModel):
    """Response model for speaker network analysis."""

    conversation_id: str
    speaker_interactions: List[Dict[str, Any]]


class TopicFlowResponse(BaseModel):
    """Response model for topic flow analysis."""

    conversation_id: str
    topic_transitions: List[Dict[str, Any]]


@router.get("/stats", response_model=GraphStatsResponse)
async def get_graph_stats(
    graph_service: GraphService = Depends(get_graph_service),
) -> GraphStatsResponse:
    """Get graph database statistics."""
    try:
        if not graph_service.settings.graph.enabled:
            return GraphStatsResponse(
                enabled=False, stats={"message": "Graph processing is disabled"}
            )

        stats = await graph_service.get_database_stats()
        return GraphStatsResponse(enabled=True, stats=stats)

    except Exception as e:
        logger.error(f"Failed to get graph stats: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve graph statistics: {str(e)}"
        )


@router.get(
    "/conversation/{conversation_id}/graph", response_model=ConversationGraphResponse
)
async def get_conversation_graph(
    conversation_id: str, graph_service: GraphService = Depends(get_graph_service)
) -> ConversationGraphResponse:
    """Get complete graph data for a conversation."""
    try:
        if not graph_service.settings.graph.enabled:
            raise HTTPException(status_code=503, detail="Graph processing is disabled")

        graph_data = await graph_service.get_conversation_graph(conversation_id)

        if not graph_data:
            raise HTTPException(
                status_code=404,
                detail=f"No graph data found for conversation {conversation_id}",
            )

        return ConversationGraphResponse(
            conversation_id=conversation_id, graph_data=graph_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation graph: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve conversation graph: {str(e)}"
        )


@router.get(
    "/conversation/{conversation_id}/speaker-network",
    response_model=SpeakerNetworkResponse,
)
async def get_speaker_network(
    conversation_id: str, graph_service: GraphService = Depends(get_graph_service)
) -> SpeakerNetworkResponse:
    """Get speaker interaction network for a conversation."""
    try:
        if not graph_service.settings.graph.enabled:
            raise HTTPException(status_code=503, detail="Graph processing is disabled")

        speaker_interactions = await graph_service.get_speaker_network(conversation_id)

        return SpeakerNetworkResponse(
            conversation_id=conversation_id, speaker_interactions=speaker_interactions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get speaker network: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve speaker network: {str(e)}"
        )


@router.get(
    "/conversation/{conversation_id}/topic-flow", response_model=TopicFlowResponse
)
async def get_topic_flow(
    conversation_id: str, graph_service: GraphService = Depends(get_graph_service)
) -> TopicFlowResponse:
    """Get topic transition flow for a conversation."""
    try:
        if not graph_service.settings.graph.enabled:
            raise HTTPException(status_code=503, detail="Graph processing is disabled")

        topic_transitions = await graph_service.get_topic_flow(conversation_id)

        return TopicFlowResponse(
            conversation_id=conversation_id, topic_transitions=topic_transitions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get topic flow: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve topic flow: {str(e)}"
        )


@router.get("/node/{node_id}/relationships")
async def get_node_relationships(
    node_id: str,
    node_type: Optional[str] = Query(None, description="Node type filter"),
    relationship_types: Optional[str] = Query(
        None, description="Comma-separated relationship types"
    ),
    direction: str = Query(
        "BOTH", description="Relationship direction: IN, OUT, or BOTH"
    ),
    graph_service: GraphService = Depends(get_graph_service),
) -> Dict[str, Any]:
    """Get relationships for a specific node."""
    try:
        if not graph_service.settings.graph.enabled:
            raise HTTPException(status_code=503, detail="Graph processing is disabled")

        # Parse relationship types
        rel_types: Optional[List[str]] = None
        if relationship_types:
            try:
                rel_types = [
                    RelationshipType(rt.strip()).value
                    for rt in relationship_types.split(",")
                ]
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid relationship type: {str(e)}"
                )

        # Validate direction
        if direction not in ["IN", "OUT", "BOTH"]:
            raise HTTPException(
                status_code=400, detail="Direction must be IN, OUT, or BOTH"
            )

        relationships = await graph_service.get_node_relationships(
            node_id=node_id, relationship_types=rel_types, direction=direction
        )

        return {
            "node_id": node_id,
            "relationships": relationships,
            "count": len(relationships),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get node relationships: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve node relationships: {str(e)}"
        )


@router.get("/path/{from_node_id}/{to_node_id}")
async def find_shortest_path(
    from_node_id: str,
    to_node_id: str,
    max_hops: int = Query(5, description="Maximum number of hops", ge=1, le=10),
    graph_service: GraphService = Depends(get_graph_service),
) -> Dict[str, Any]:
    """Find shortest path between two nodes."""
    try:
        if not graph_service.settings.graph.enabled:
            raise HTTPException(status_code=503, detail="Graph processing is disabled")

        path = await graph_service.find_shortest_path(
            from_node_id=from_node_id, to_node_id=to_node_id, max_hops=max_hops
        )

        if not path:
            raise HTTPException(
                status_code=404,
                detail=f"No path found between {from_node_id} and {to_node_id}",
            )

        return {
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "path": path,
            "max_hops": max_hops,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to find shortest path: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to find shortest path: {str(e)}"
        )


# New Speaker Endpoints
@router.get(
    "/speakers/top",
    response_model=List[TopSpeakerResponse],
    summary="Get Top Speakers",
    description="Get a list of top speakers based on a specified metric.",
)
async def get_top_speakers(
    limit: int = Query(10, ge=1, le=100),
    metric: str = Query(
        "speaking_time", enum=["speaking_time", "conversations", "turns"]
    ),
    service: SpeakerGraphService = Depends(get_speaker_graph_service),
):
    """Get top speakers based on speaking time, conversation count, or turn count."""
    if not service.settings.graph.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph processing is disabled",
        )
    return await service.get_top_speakers(limit=limit, metric=metric)


@router.get(
    "/speakers/{speaker_id}/profile",
    response_model=SpeakerProfileResponse,
    summary="Get Speaker Profile",
    description="Get a comprehensive profile for a specific speaker.",
)
async def get_speaker_profile(
    speaker_id: str,
    service: SpeakerGraphService = Depends(get_speaker_graph_service),
):
    """Get a detailed profile for a speaker, including statistics and topics discussed."""
    if not service.settings.graph.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph processing is disabled",
        )

    profile = await service.get_speaker_profile(speaker_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speaker profile for '{speaker_id}' not found",
        )
    return profile


@router.get(
    "/speakers/{speaker_id}/similar",
    response_model=List[SimilarSpeakerResponse],
    summary="Find Similar Speakers",
    description="Find speakers with similar communication patterns.",
)
async def find_similar_speakers(
    speaker_id: str,
    threshold: float = Query(0.7, ge=0.1, le=1.0),
    service: SpeakerGraphService = Depends(get_speaker_graph_service),
):
    """Find speakers with similar communication styles based on speaking patterns."""
    if not service.settings.graph.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph processing is disabled",
        )
    return await service.find_similar_speakers(
        speaker_id, similarity_threshold=threshold
    )


# New Topic Endpoints
@router.get(
    "/topics/trending",
    response_model=List[TrendingTopicResponse],
    summary="Get Trending Topics",
    description="Get a list of trending topics based on recent activity.",
)
async def get_trending_topics(
    limit: int = Query(10, ge=1, le=100),
    time_window_hours: int = Query(24, ge=1),
    service: TopicGraphService = Depends(get_topic_graph_service),
):
    """Get trending topics based on mentions and speaker engagement within a time window."""
    if not service.settings.graph.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph processing is disabled",
        )
    return await service.get_trending_topics(
        limit=limit, time_window_hours=time_window_hours
    )


@router.get(
    "/topics/{topic_id}/profile",
    response_model=TopicProfileResponse,
    summary="Get Topic Profile",
    description="Get a comprehensive profile for a specific topic.",
)
async def get_topic_profile(
    topic_id: str,
    service: TopicGraphService = Depends(get_topic_graph_service),
):
    """Get a detailed profile for a topic, including statistics and related speakers."""
    if not service.settings.graph.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph processing is disabled",
        )

    profile = await service.get_topic_profile(topic_id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Topic profile for '{topic_id}' not found",
        )
    return profile


@router.get(
    "/topics/{topic_id}/co-occurrence",
    response_model=List[TopicCooccurrenceResponse],
    summary="Get Topic Co-occurrence",
    description="Find topics that frequently occur with the specified topic.",
)
async def get_topic_cooccurrence(
    topic_id: str,
    limit: int = Query(20, ge=1, le=100),
    service: TopicGraphService = Depends(get_topic_graph_service),
):
    """Get topics that frequently appear in the same context as the given topic."""
    if not service.settings.graph.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph processing is disabled",
        )
    return await service.get_topic_cooccurrence(topic_id, limit=limit)
