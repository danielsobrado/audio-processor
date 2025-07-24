#!/usr/bin/env python3
"""
Clean up duplicates in Neo4j AutoSchemaKG data
"""
import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

# Load .env
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'))

from app.db.graph_session import get_graph_db_manager

async def clean_duplicates():
    try:
        print('🧹 Cleaning duplicates in Neo4j AutoSchemaKG data...')
        manager = await get_graph_db_manager()
        if not manager.is_connected:
            await manager.initialize()

        # Check counts before cleanup
        result = await manager.execute_read_transaction('MATCH (n:AutoSchemaNode) RETURN count(n) as count')
        nodes_before = result[0]['count'] if result else 0

        result = await manager.execute_read_transaction('MATCH ()-[r:AUTOSCHEMA_RELATION]->() RETURN count(r) as count')
        rels_before = result[0]['count'] if result else 0

        print(f'📊 Before cleanup: {nodes_before} nodes, {rels_before} relationships')

        print('�️ Removing all data for fresh start...')
        # Clear all data
        result = await manager.execute_write_transaction("""
            MATCH ()-[r:AUTOSCHEMA_RELATION]->()
            DELETE r
            RETURN count(r) as deleted_relationships
        """)
        rels_deleted = result[0]['deleted_relationships'] if result else 0
        print(f'✅ Deleted {rels_deleted} relationships')

        result = await manager.execute_write_transaction("""
            MATCH (n:AutoSchemaNode)
            DELETE n
            RETURN count(n) as deleted_nodes
        """)
        nodes_deleted = result[0]['deleted_nodes'] if result else 0
        print(f'✅ Deleted {nodes_deleted} nodes')

        # Check counts after cleanup
        result = await manager.execute_read_transaction('MATCH (n:AutoSchemaNode) RETURN count(n) as count')
        nodes_after = result[0]['count'] if result else 0

        result = await manager.execute_read_transaction('MATCH ()-[r:AUTOSCHEMA_RELATION]->() RETURN count(r) as count')
        rels_after = result[0]['count'] if result else 0

        print(f'\n📊 After cleanup: {nodes_after} nodes, {rels_after} relationships')
        print(f'📉 Removed: {nodes_before - nodes_after} nodes, {rels_before - rels_after} relationships')

        print('\n✅ Cleanup completed! Your graph should now have no duplicates.')
        print('\n💡 View clean data in Neo4j Browser:')
        print('   MATCH (a:AutoSchemaNode)-[r:AUTOSCHEMA_RELATION]->(b:AutoSchemaNode)')
        print('   RETURN a, r, b LIMIT 50')

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(clean_duplicates())
