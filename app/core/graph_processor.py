"""Graph data processor for extracting relationships from transcription results."""

import logging
import re
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from collections import defaultdict

from app.models.graph import (
    SpeakerNode, TopicNode, EntityNode, ConversationNode, TranscriptSegmentNode,
    SpeaksInRelationship, DiscussesRelationship, MentionsRelationship, 
    FollowsRelationship, GraphNode, GraphRelationship, RelationshipType
)
from app.services.conversation_graph import get_conversation_graph_service
from app.services.speaker_graph import get_speaker_graph_service
from app.services.topic_graph import get_topic_graph_service
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class GraphProcessor:
    """Extract and process graph data from transcription results."""
    
    def __init__(self):
        self.settings = get_settings()
        self.topic_keywords = self._load_topic_keywords()
        self.entity_patterns = self._load_entity_patterns()
    
    def _load_topic_keywords(self) -> Dict[str, List[str]]:
        """Load topic classification keywords from configuration."""
        if self.settings.graph.topic_keywords:
            return self.settings.graph.topic_keywords
        
        # Fallback defaults if not configured
        return {
            'technology': ['ai', 'software', 'computer', 'digital', 'tech', 'algorithm'],
            'business': ['revenue', 'profit', 'market', 'sales', 'budget', 'finance'],
            'meeting': ['agenda', 'action', 'decision', 'follow-up', 'deadline', 'task'],
            'project': ['milestone', 'deliverable', 'timeline', 'scope', 'requirement'],
            'personal': ['family', 'vacation', 'health', 'hobby', 'weekend', 'personal']
        }
    
    def _load_entity_patterns(self) -> Dict[str, str]:
        """Load entity extraction patterns from configuration."""
        if self.settings.graph.entity_extraction_patterns:
            return self.settings.graph.entity_extraction_patterns
        
        # Fallback defaults if not configured
        return {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s*\d{3}-\d{4}\b',
            'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            'time': r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b',
            'money': r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|USD)\b',
            'url': r'https?://[^\s<>"{}|\\^`\[\]]*',
            'mention': r'@[a-zA-Z0-9_]+'
        }
    
    async def process_transcription_result(self, transcription_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main processing function for transcription results."""
        if not self.settings.graph.enabled:
            logger.debug("Graph processing is disabled")
            return {'success': True, 'message': 'Graph processing is disabled'}
        
        try:
            # Extract basic info
            conversation_id = transcription_data.get('job_id', '')
            audio_file_id = transcription_data.get('audio_file_id', '')
            language = transcription_data.get('language', 'en')
            segments = transcription_data.get('segments', [])
            
            if not conversation_id or not segments:
                logger.warning("Invalid transcription data for graph processing")
                return {'success': False, 'error': 'Invalid data'}
            
            # Process graph data
            graph_data = await self._extract_graph_data(
                conversation_id, audio_file_id, language, segments
            )
            
            # Create graph structure
            result = await self._create_graph_structure(graph_data)
            
            logger.info(f"Processed graph for conversation {conversation_id}")
            return {
                'success': True,
                'conversation_id': conversation_id,
                'nodes_created': result['nodes_created'],
                'relationships_created': result['relationships_created'],
                'processing_time': result['processing_time']
            }
            
        except Exception as e:
            logger.error(f"Graph processing failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _extract_graph_data(self, conversation_id: str, audio_file_id: str, 
                                 language: str, segments: List[Dict]) -> Dict[str, Any]:
        """Extract nodes and relationships from segments."""
        
        # Initialize data structures
        speakers = {}
        topics = {}
        entities = {}
        transcript_segments = {}
        
        # Track statistics
        total_duration = 0
        speaker_stats = defaultdict(lambda: {'time': 0, 'turns': 0})
        topic_mentions = defaultdict(int)
        
        # Process each segment
        for i, segment in enumerate(segments):
            segment_id = f"{conversation_id}_seg_{i}"
            text = segment.get('text', '').strip()
            start_time = segment.get('start', 0.0)
            end_time = segment.get('end', 0.0)
            speaker_id = segment.get('speaker', f'speaker_{i % 2}')  # Fallback if no speaker
            confidence = segment.get('confidence', 0.0)
            
            duration = end_time - start_time
            total_duration = max(total_duration, end_time)
            
            # Create transcript segment node
            transcript_segments[segment_id] = TranscriptSegmentNode(
                segment_id=segment_id,
                conversation_id=conversation_id,
                text=text,
                start_time=start_time,
                end_time=end_time,
                speaker_id=speaker_id,
                confidence_score=confidence
            )
            
            # Process speaker
            if speaker_id not in speakers:
                speakers[speaker_id] = SpeakerNode(
                    speaker_id=speaker_id,
                    name=f"Speaker_{speaker_id}",
                    voice_characteristics={}
                )
            
            # Update speaker statistics
            speaker_stats[speaker_id]['time'] += duration
            speaker_stats[speaker_id]['turns'] += 1
            
            # Extract topics from text
            segment_topics = self._extract_topics(text)
            for topic_name, confidence_score in segment_topics:
                topic_id = self._generate_topic_id(topic_name)
                if topic_id not in topics:
                    topics[topic_id] = TopicNode(
                        topic_id=topic_id,
                        topic_name=topic_name,
                        confidence_score=confidence_score,
                        keywords=self.topic_keywords.get(topic_name.lower(), [])
                    )
                topic_mentions[topic_id] += 1
            
            # Extract entities from text
            segment_entities = self._extract_entities(text)
            for entity_text, entity_type, confidence_score in segment_entities:
                entity_id = self._generate_entity_id(entity_text, entity_type)
                if entity_id not in entities:
                    entities[entity_id] = EntityNode(
                        entity_id=entity_id,
                        entity_text=entity_text,
                        entity_type=entity_type,
                        confidence_score=confidence_score
                    )
        
        # Create conversation node
        conversation = ConversationNode(
            conversation_id=conversation_id,
            audio_file_id=audio_file_id,
            duration=total_duration,
            language=language
        )
        
        # Update node statistics
        conversation.properties.update({
            'speaker_count': len(speakers),
            'topic_count': len(topics),
            'entity_count': len(entities),
            'segment_count': len(transcript_segments),
            'processing_status': 'completed'
        })
        
        # Update speaker statistics
        for speaker_id, stats in speaker_stats.items():
            speakers[speaker_id].properties.update({
                'total_speaking_time': stats['time'],
                'turn_count': stats['turns'],
                'participation_ratio': stats['time'] / total_duration if total_duration > 0 else 0
            })
        
        # Update topic statistics
        for topic_id, mentions in topic_mentions.items():
            topics[topic_id].properties['mention_count'] = mentions
        
        return {
            'conversation': conversation,
            'speakers': speakers,
            'topics': topics,
            'entities': entities,
            'transcript_segments': transcript_segments,
            'segments_data': segments  # Keep original for relationship creation
        }
    
    def _extract_topics(self, text: str) -> List[Tuple[str, float]]:
        """Extract topics from text using keyword matching."""
        text_lower = text.lower()
        topics = []
        
        for topic_name, keywords in self.topic_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in text_lower)
            if matches > 0:
                confidence = min(matches / len(keywords), 1.0)
                topics.append((topic_name, confidence))
        
        return topics
    
    def _extract_entities(self, text: str) -> List[Tuple[str, str, float]]:
        """Extract entities from text using pattern matching."""
        entities = []
        
        for entity_type, pattern in self.entity_patterns.items():
            try:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    # Simple confidence based on pattern match
                    confidence = 0.8 if len(match) > 5 else 0.6
                    entities.append((match, entity_type.upper(), confidence))
            except re.error as e:
                logger.warning(f"Invalid regex pattern for {entity_type}: {e}")
                continue
        
        return entities
    
    def _generate_topic_id(self, topic_name: str) -> str:
        """Generate consistent topic ID."""
        return f"topic_{hashlib.md5(topic_name.lower().encode()).hexdigest()[:8]}"
    
    def _generate_entity_id(self, entity_text: str, entity_type: str) -> str:
        """Generate consistent entity ID."""
        combined = f"{entity_type}_{entity_text}".lower()
        return f"entity_{hashlib.md5(combined.encode()).hexdigest()[:8]}"
    
    async def _create_graph_structure(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create all nodes and relationships in the graph."""
        start_time = datetime.utcnow()
        
        # Collect all nodes
        all_nodes = []
        all_relationships = []
        
        # Add conversation node
        all_nodes.append(graph_data['conversation'])
        
        # Add all other nodes
        all_nodes.extend(graph_data['speakers'].values())
        all_nodes.extend(graph_data['topics'].values())
        all_nodes.extend(graph_data['entities'].values())
        all_nodes.extend(graph_data['transcript_segments'].values())
        
        # Create relationships
        relationships = self._create_relationships(graph_data)
        all_relationships.extend(relationships)
        
        # Batch create nodes and relationships
        try:
            nodes_created = await graph_service.create_nodes_batch(all_nodes)
            relationships_created = await graph_service.create_relationships_batch(all_relationships)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return {
                'nodes_created': nodes_created,
                'relationships_created': relationships_created,
                'processing_time': processing_time
            }
            
        except Exception as e:
            logger.error(f"Failed to create graph structure: {e}")
            raise
    
    def _create_relationships(self, graph_data: Dict[str, Any]) -> List[GraphRelationship]:
        """Create all relationships between nodes."""
        relationships = []
        
        conversation_id = graph_data['conversation'].id
        speakers = graph_data['speakers']
        topics = graph_data['topics']
        entities = graph_data['entities']
        transcript_segments = graph_data['transcript_segments']
        segments_data = graph_data['segments_data']
        
        # Speaker -> Conversation relationships
        for speaker_id, speaker_node in speakers.items():
            relationships.append(SpeaksInRelationship(
                speaker_id=speaker_id,
                conversation_id=conversation_id,
                speaking_time=speaker_node.properties['total_speaking_time'],
                turn_count=speaker_node.properties['turn_count']
            ))
        
        # Process each segment for detailed relationships
        segment_list = list(transcript_segments.values())
        for i, segment in enumerate(segment_list):
            segment_id = segment.id
            text = segment.properties['text']
            speaker_id = segment.properties['speaker_id']
            
            # Segment -> Conversation (CONTAINS relationship)
            relationships.append(GraphRelationship(
                from_node_id=conversation_id,
                to_node_id=segment_id,
                relationship_type=RelationshipType.CONTAINS,
                properties={},
                created_at=datetime.utcnow()
            ))
            
            # Sequential relationships between segments
            if i > 0:
                prev_segment = segment_list[i-1]
                time_gap = segment.properties['start_time'] - prev_segment.properties['end_time']
                speaker_change = segment.properties['speaker_id'] != prev_segment.properties['speaker_id']
                
                relationships.append(FollowsRelationship(
                    from_segment_id=prev_segment.id,
                    to_segment_id=segment_id,
                    time_gap=time_gap,
                    speaker_change=speaker_change
                ))
            
            # Topic relationships
            segment_topics = self._extract_topics(text)
            for topic_name, confidence in segment_topics:
                topic_id = self._generate_topic_id(topic_name)
                if topic_id in topics:
                    # Speaker discusses topic
                    relationships.append(DiscussesRelationship(
                        speaker_id=speaker_id,
                        topic_id=topic_id,
                        mention_count=1,
                        context_relevance=confidence
                    ))
            
            # Entity relationships
            segment_entities = self._extract_entities(text)
            for entity_text, entity_type, confidence in segment_entities:
                entity_id = self._generate_entity_id(entity_text, entity_type)
                if entity_id in entities:
                    # Segment mentions entity
                    mention_position = text.lower().find(entity_text.lower())
                    relationships.append(MentionsRelationship(
                        segment_id=segment_id,
                        entity_id=entity_id,
                        mention_position=mention_position,
                        confidence_score=confidence
                    ))
        
        return relationships


# Global processor instance
graph_processor = GraphProcessor()


# Dependency injection
async def get_graph_processor() -> GraphProcessor:
    """Get graph processor instance."""
    return graph_processor
