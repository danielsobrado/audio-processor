"""Graph API endpoints for graph database queries."""

import logging
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.services.conversation_graph import get_conversation_graph_service, ConversationGraphService
from app.services.speaker_graph import get_speaker_graph_service, SpeakerGraphService
from app.services.topic_graph import get_topic_graph_service, TopicGraphService
from app.models.graph import NodeType, RelationshipType

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
    graph_service: GraphService = Depends(get_graph_service)
) -> GraphStatsResponse:
    """Get graph database statistics."""
    try:
        if not graph_service.settings.graph.enabled:
            return GraphStatsResponse(
                enabled=False,
                stats={"message": "Graph processing is disabled"}
            )
        
        stats = await graph_service.get_database_stats()
        return GraphStatsResponse(enabled=True, stats=stats)
        
    except Exception as e:
        logger.error(f"Failed to get graph stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve graph statistics: {str(e)}"
        )


@router.get("/conversation/{conversation_id}/graph", response_model=ConversationGraphResponse)
async def get_conversation_graph(
    conversation_id: str,
    graph_service: GraphService = Depends(get_graph_service)
) -> ConversationGraphResponse:
    """Get complete graph data for a conversation."""
    try:
        if not graph_service.settings.graph.enabled:
            raise HTTPException(
                status_code=503,
                detail="Graph processing is disabled"
            )
        
        graph_data = await graph_service.get_conversation_graph(conversation_id)
        
        if not graph_data:
            raise HTTPException(
                status_code=404,
                detail=f"No graph data found for conversation {conversation_id}"
            )
        
        return ConversationGraphResponse(
            conversation_id=conversation_id,
            graph_data=graph_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation graph: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve conversation graph: {str(e)}"
        )


@router.get("/conversation/{conversation_id}/speaker-network", response_model=SpeakerNetworkResponse)
async def get_speaker_network(
    conversation_id: str,
    graph_service: GraphService = Depends(get_graph_service)
) -> SpeakerNetworkResponse:
    """Get speaker interaction network for a conversation."""
    try:
        if not graph_service.settings.graph.enabled:
            raise HTTPException(
                status_code=503,
                detail="Graph processing is disabled"
            )
        
        speaker_interactions = await graph_service.get_speaker_network(conversation_id)
        
        return SpeakerNetworkResponse(
            conversation_id=conversation_id,
            speaker_interactions=speaker_interactions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get speaker network: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve speaker network: {str(e)}"
        )


@router.get("/conversation/{conversation_id}/topic-flow", response_model=TopicFlowResponse)
async def get_topic_flow(
    conversation_id: str,
    graph_service: GraphService = Depends(get_graph_service)
) -> TopicFlowResponse:
    """Get topic transition flow for a conversation."""
    try:
        if not graph_service.settings.graph.enabled:
            raise HTTPException(
                status_code=503,
                detail="Graph processing is disabled"
            )
        
        topic_transitions = await graph_service.get_topic_flow(conversation_id)
        
        return TopicFlowResponse(
            conversation_id=conversation_id,
            topic_transitions=topic_transitions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get topic flow: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve topic flow: {str(e)}"
        )


@router.get("/node/{node_id}/relationships")
async def get_node_relationships(
    node_id: str,
    node_type: Optional[str] = Query(None, description="Node type filter"),
    relationship_types: Optional[str] = Query(None, description="Comma-separated relationship types"),
    direction: str = Query("BOTH", description="Relationship direction: IN, OUT, or BOTH"),
    graph_service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Get relationships for a specific node."""
    try:
        if not graph_service.settings.graph.enabled:
            raise HTTPException(
                status_code=503,
                detail="Graph processing is disabled"
            )
        
        # Parse relationship types
        rel_types = None
        if relationship_types:
            try:
                rel_types = [RelationshipType(rt.strip()) for rt in relationship_types.split(",")]
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid relationship type: {str(e)}"
                )
        
        # Validate direction
        if direction not in ["IN", "OUT", "BOTH"]:
            raise HTTPException(
                status_code=400,
                detail="Direction must be IN, OUT, or BOTH"
            )
        
        relationships = await graph_service.get_node_relationships(
            node_id=node_id,
            relationship_types=rel_types,
            direction=direction
        )
        
        return {
            "node_id": node_id,
            "relationships": relationships,
            "count": len(relationships)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get node relationships: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve node relationships: {str(e)}"
        )


@router.get("/path/{from_node_id}/{to_node_id}")
async def find_shortest_path(
    from_node_id: str,
    to_node_id: str,
    max_hops: int = Query(5, description="Maximum number of hops", ge=1, le=10),
    graph_service: GraphService = Depends(get_graph_service)
) -> Dict[str, Any]:
    """Find shortest path between two nodes."""
    try:
        if not graph_service.settings.graph.enabled:
            raise HTTPException(
                status_code=503,
                detail="Graph processing is disabled"
            )
        
        path = await graph_service.find_shortest_path(
            from_node_id=from_node_id,
            to_node_id=to_node_id,
            max_hops=max_hops
        )
        
        if not path:
            raise HTTPException(
                status_code=404,
                detail=f"No path found between {from_node_id} and {to_node_id}"
            )
        
        return {
            "from_node_id": from_node_id,
            "to_node_id": to_node_id,
            "path": path,
            "max_hops": max_hops
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to find shortest path: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to find shortest path: {str(e)}"
        )
