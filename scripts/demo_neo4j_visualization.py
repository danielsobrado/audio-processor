#!/usr/bin/env python3
"""
Demo script to load text, analyze it, and create Neo4j visualization.
Run this to see your graph in action.

Usage:
    uv run python scripts/demo_neo4j_visualization.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.graph_processor import GraphProcessor
from app.db.graph_session import get_graph_db_manager
from app.config.settings import get_settings

# Sample conversation data
DEMO_TRANSCRIPT = {
    "job_id": "demo-visualization-001",
    "audio_file_id": "demo-audio-001",
    "language": "en",
    "segments": [
        {
            "start": 0.0, "end": 4.8, "text": "Good morning team, this is John Smith, project manager. Let's review our AI budget.",
            "speaker": "john-smith", "confidence": 0.95
        },
        {
            "start": 4.8, "end": 11.2, "text": "Hi John, Sarah here from finance. Our Q1 budget is $500,000. Email me at sarah@company.com for details.",
            "speaker": "sarah-jones", "confidence": 0.92
        },
        {
            "start": 11.2, "end": 17.9, "text": "Thanks Sarah! Mike, can you update us on the machine learning algorithms? Deadline is March 15th.",
            "speaker": "john-smith", "confidence": 0.88
        },
        {
            "start": 17.9, "end": 25.3, "text": "Sure John. The neural networks need GPU clusters. Technical specs at mike.wilson@company.com",
            "speaker": "mike-wilson", "confidence": 0.91
        },
        {
            "start": 25.3, "end": 30.5, "text": "Perfect! Next meeting Friday 2:00 PM. Call me at 555-123-4567 for urgent issues.",
            "speaker": "john-smith", "confidence": 0.93
        }
    ]
}

async def cleanup_previous_demo(manager, conversation_id: str):
    """Deletes nodes and relationships from a previous run of this demo."""
    print(f"🧹 Cleaning up previous demo data for conversation ID: {conversation_id}...")
    query = """
    MATCH (c:Conversation {id: $conv_id})
    OPTIONAL MATCH (c)-[:CONTAINS]->(s:TranscriptSegment)
    DETACH DELETE c, s
    """
    try:
        await manager.execute_write_transaction(query, {'conv_id': conversation_id})
        print("✅ Cleanup complete.")
    except Exception as e:
        print(f"⚠️ Cleanup failed or was not needed: {e}")

async def main():
    """Main demo function."""
    print("="*60)
    print("AUDIO PROCESSOR - NEO4J VISUALIZATION DEMO")
    print("="*60)

    settings = get_settings()
    if not settings.graph.enabled:
        print("❌ ERROR: Graph processing is DISABLED in your configuration.")
        print("Please set GRAPH_ENABLED=true in your .env file or enable it in your YAML config and restart.")
        return

    print(f"✅ Graph enabled. Connecting to: {settings.graph.database.url}")

    try:
        manager = await get_graph_db_manager()
        if not manager.is_connected:
            await manager.initialize()

        conversation_id = DEMO_TRANSCRIPT["job_id"]
        await cleanup_previous_demo(manager, conversation_id)

        processor = GraphProcessor()
        print("\n📝 Processing transcript and populating graph...")
        result = await processor.process_transcription_result(DEMO_TRANSCRIPT)

        if not result.get('success'):
            print(f"❌ Processing failed: {result.get('error')}")
            return

        print(f"✅ Graph populated successfully!")
        print(f"   - Nodes created: {result.get('nodes_created', 'N/A')}")
        print(f"   - Relationships created: {result.get('relationships_created', 'N/A')}")

        print("\n" + "="*60)
        print("🎨 NEO4J VISUALIZATION INSTRUCTIONS")
        print("="*60)
        print(f"1. Open Neo4j Browser. If using Docker, go to: http://localhost:7474")
        print(f"2. Login with user '{settings.graph.database.username}' and the configured password.")
        print(f"3. Run these Cypher queries for different views:")
        print()

        print("📈 1. View the Full Conversation Graph:")
        print(f"   MATCH (c:Conversation {{id: '{conversation_id}'}})-[r]-(n) RETURN c, r, n")
        print()

        print("👥 2. View Speakers and their Segments:")
        print(f"   MATCH (sp:Speaker)-[:SPEAKS_IN]->(c:Conversation {{id: '{conversation_id}'}})<-[:CONTAINS]-(c)<-[:CONTAINS]-(seg:TranscriptSegment {{speaker_id: sp.id}}) RETURN sp, seg")
        print()

        print("🏷️  3. View Topics Discussed by Speakers:")
        print(f"   MATCH (sp:Speaker)-[d:DISCUSSES]->(t:Topic) WHERE (sp)-[:SPEAKS_IN]->(:Conversation {{id: '{conversation_id}'}}) RETURN sp, d, t")
        print()

        print("📧 4. View Entities Mentioned in Segments:")
        print(f"   MATCH (e:Entity)<-[m:MENTIONS]-(seg:TranscriptSegment)-[:CONTAINS]-(:Conversation {{id: '{conversation_id}'}}) RETURN e, m, seg")
        print()

        print("➡️ 5. View the Sequential Flow of the Conversation:")
        print(f"   MATCH p=(:Conversation {{id: '{conversation_id}'}})-[:CONTAINS]->(seg1:TranscriptSegment)-[:FOLLOWS*]->(seg2:TranscriptSegment) RETURN p")
        print()

        print("="*60)
        print("🎯 In the Neo4j Browser, results will appear as a table. Click the 'Graph' icon on the left to visualize.")
        print("="*60)

    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())