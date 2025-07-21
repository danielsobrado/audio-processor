#!/usr/bin/env python3
"""
Simple verification script to check if graph data was created in Neo4j.
"""

import asyncio
import os

# Set up environment variables
os.environ.setdefault("GRAPH_DATABASE_URL", "bolt://localhost:7687")
os.environ.setdefault("GRAPH_DATABASE_USERNAME", "neo4j")
os.environ.setdefault("GRAPH_DATABASE_PASSWORD", "devpassword")
os.environ.setdefault("GRAPH_ENABLED", "true")


async def verify_graph_data():
    """Verify that graph data was created properly."""
    print("🔍 Verifying Graph Data in Neo4j")
    print("=" * 40)

    try:
        from app.db.graph_session import get_graph_db_manager

        manager = await get_graph_db_manager()
        if not manager.is_connected:
            await manager.initialize()

        # Check total node count
        node_count_query = "MATCH (n) RETURN count(n) as total_nodes"
        node_result = await manager.execute_read_transaction(node_count_query)
        total_nodes = node_result[0]["total_nodes"] if node_result else 0
        print(f"📊 Total nodes: {total_nodes}")

        # Check total relationship count
        rel_count_query = "MATCH ()-[r]->() RETURN count(r) as total_relationships"
        rel_result = await manager.execute_read_transaction(rel_count_query)
        total_relationships = rel_result[0]["total_relationships"] if rel_result else 0
        print(f"🔗 Total relationships: {total_relationships}")

        # Check nodes by type
        node_types_query = "MATCH (n) RETURN labels(n)[0] as node_type, count(n) as count ORDER BY count DESC"
        node_types_result = await manager.execute_read_transaction(node_types_query)
        print("\n📋 Node types:")
        for record in node_types_result:
            print(f"   {record['node_type']}: {record['count']}")

        # Check relationships by type
        rel_types_query = "MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as count ORDER BY count DESC"
        rel_types_result = await manager.execute_read_transaction(rel_types_query)
        print("\n🔗 Relationship types:")
        for record in rel_types_result:
            print(f"   {record['rel_type']}: {record['count']}")

        # Show some sample data
        sample_query = """
        MATCH (c:Conversation)-[:CONTAINS]->(s:TranscriptSegment)
        RETURN c.id as conversation_id, s.text as segment_text, s.start_time as start_time
        ORDER BY s.start_time
        LIMIT 3
        """
        sample_result = await manager.execute_read_transaction(sample_query)
        print("\n📝 Sample transcript segments:")
        for record in sample_result:
            print(f"   {record['start_time']}s: {record['segment_text'][:50]}...")

        print("\n✅ Graph verification complete!")

    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(verify_graph_data())
