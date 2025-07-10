#!/usr/bin/env python3
"""
Test script to generate graph nodes from text data and visualize them.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List

# Set up environment variables for testing
import os
os.environ.setdefault("GRAPH_DATABASE_URL", "bolt://localhost:7687")
os.environ.setdefault("GRAPH_DATABASE_USERNAME", "neo4j")
os.environ.setdefault("GRAPH_DATABASE_PASSWORD", "devpassword")
os.environ.setdefault("GRAPH_ENABLED", "true")

async def test_graph_from_text():
    """Test creating graph nodes from text data."""
    print("🚀 Testing Graph Generation from Text Data")
    print("=" * 50)
    
    # Sample text data that simulates transcription segments
    sample_segments = [
        {
            "start": 0.0,
            "end": 5.0,
            "text": "Hello everyone, my name is John and I'm excited to talk about artificial intelligence today.",
            "speaker": "SPEAKER_00"
        },
        {
            "start": 5.0,
            "end": 10.0,
            "text": "AI has been transforming various industries including healthcare and finance.",
            "speaker": "SPEAKER_00"
        },
        {
            "start": 10.0,
            "end": 15.0,
            "text": "I completely agree with John. Machine learning algorithms are particularly effective in medical diagnosis.",
            "speaker": "SPEAKER_01"
        },
        {
            "start": 15.0,
            "end": 20.0,
            "text": "That's fascinating! Can you tell us more about the applications in healthcare?",
            "speaker": "SPEAKER_00"
        },
        {
            "start": 20.0,
            "end": 30.0,
            "text": "Sure! Deep learning models can analyze medical images like X-rays and MRIs to detect diseases early.",
            "speaker": "SPEAKER_01"
        }
    ]
    
    # Create graph data structure
    graph_data = {
        "job_id": "test-text-001",
        "audio_file_id": "text-sample-001",
        "language": "en",
        "segments": sample_segments
    }
    
    try:
        # Import the graph processor
        from app.core.graph_processor import graph_processor
        
        print("📊 Processing text data into graph structure...")
        print(f"📋 Graph data: {json.dumps(graph_data, indent=2)}")
        
        # Check if graph is enabled
        from app.config.settings import get_settings
        settings = get_settings()
        print(f"🔧 Graph enabled: {settings.graph.enabled}")
        
        # Process the text data
        result = await graph_processor.process_transcription_result(graph_data)
        
        print("✅ Graph processing completed successfully!")
        print(f"📈 Result summary: {json.dumps(result, indent=2)}")
        
        # Test querying the graph
        print("\n🔍 Testing graph queries...")
        await test_graph_queries()
        
    except Exception as e:
        print(f"❌ Error during graph processing: {e}")
        import traceback
        traceback.print_exc()

async def test_graph_queries():
    """Test querying the generated graph data."""
    try:
        from app.db.graph_session import get_graph_db_manager
        
        manager = await get_graph_db_manager()
        if not manager.is_connected:
            await manager.initialize()
        
        # Test query 1: Get all speakers
        print("\n1. Getting all speakers...")
        speakers_query = """
        MATCH (s:Speaker)
        RETURN s.speaker_id as speaker_id, s.name as name
        """
        speakers = await manager.execute_read_transaction(speakers_query)
        print(f"   Found {len(speakers)} speakers: {speakers}")
        
        # Test query 2: Get all topics
        print("\n2. Getting all topics...")
        topics_query = """
        MATCH (t:Topic)
        RETURN t.name as topic, t.keywords as keywords
        """
        topics = await manager.execute_read_transaction(topics_query)
        print(f"   Found {len(topics)} topics: {topics}")
        
        # Test query 3: Get all entities
        print("\n3. Getting all entities...")
        entities_query = """
        MATCH (e:Entity)
        RETURN e.name as entity, e.type as type, e.confidence as confidence
        """
        entities = await manager.execute_read_transaction(entities_query)
        print(f"   Found {len(entities)} entities: {entities}")
        
        # Test query 4: Get conversation flow
        print("\n4. Getting conversation flow...")
        flow_query = """
        MATCH (s1:TranscriptSegment)-[:FOLLOWS]->(s2:TranscriptSegment)
        RETURN s1.text as segment1, s2.text as segment2, s1.start_time as time1, s2.start_time as time2
        ORDER BY s1.start_time
        """
        flow = await manager.execute_read_transaction(flow_query)
        print(f"   Found {len(flow)} conversation flows")
        for f in flow:
            print(f"     {f['time1']}s -> {f['time2']}s: '{f['segment1'][:50]}...' -> '{f['segment2'][:50]}...'")
        
        # Test query 5: Get speaker relationships
        print("\n5. Getting speaker relationships...")
        speaker_rel_query = """
        MATCH (sp:Speaker)-[:SPEAKS_IN]->(s:TranscriptSegment)
        RETURN sp.speaker_id as speaker, s.text as text, s.start_time as time
        ORDER BY s.start_time
        """
        speaker_rels = await manager.execute_read_transaction(speaker_rel_query)
        print(f"   Found {len(speaker_rels)} speaker relationships")
        for rel in speaker_rels:
            print(f"     {rel['speaker']} ({rel['time']}s): '{rel['text'][:50]}...'")
            
    except Exception as e:
        print(f"❌ Error during graph queries: {e}")
        import traceback
        traceback.print_exc()

async def visualize_graph():
    """Generate a simple text-based visualization of the graph."""
    print("\n📊 Graph Visualization")
    print("=" * 30)
    
    try:
        from app.db.graph_session import get_graph_db_manager
        
        manager = await get_graph_db_manager()
        if not manager.is_connected:
            await manager.initialize()
        
        # Get a comprehensive view of the graph
        viz_query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN labels(n) as node_labels, n as node_properties, 
               type(r) as relationship_type, labels(m) as target_labels, m as target_properties
        """
        results = await manager.execute_read_transaction(viz_query)
        
        print("🔗 Graph Structure:")
        node_counts = {}
        relationship_counts = {}
        
        for result in results:
            node_label = result['node_labels'][0] if result['node_labels'] else 'Unknown'
            node_counts[node_label] = node_counts.get(node_label, 0) + 1
            
            if result['relationship_type']:
                rel_type = result['relationship_type']
                relationship_counts[rel_type] = relationship_counts.get(rel_type, 0) + 1
        
        print("\n📈 Node Types:")
        for node_type, count in node_counts.items():
            print(f"   {node_type}: {count} nodes")
        
        print("\n🔗 Relationship Types:")
        for rel_type, count in relationship_counts.items():
            print(f"   {rel_type}: {count} relationships")
            
    except Exception as e:
        print(f"❌ Error during visualization: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main test function."""
    print("🌟 Audio Processor Graph Testing Suite")
    print("=" * 50)
    
    # Test the graph generation from text
    await test_graph_from_text()
    
    # Visualize the graph
    await visualize_graph()
    
    print("\n🎉 Graph testing completed!")
    print("💡 You can now:")
    print("   - View the Neo4j browser at http://localhost:7474")
    print("   - Login with: neo4j / devpassword")
    print("   - Run Cypher queries to explore the graph")

if __name__ == "__main__":
    asyncio.run(main())
