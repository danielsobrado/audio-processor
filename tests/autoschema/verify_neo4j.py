#!/usr/bin/env python3
"""
Verify AutoSchemaKG data in Neo4j
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

async def verify_neo4j():
    try:
        print('🔍 Verifying AutoSchemaKG data in Neo4j...')
        manager = await get_graph_db_manager()
        if not manager.is_connected:
            await manager.initialize()

        # Check total AutoSchemaNode count
        result = await manager.execute_read_transaction('MATCH (n:AutoSchemaNode) RETURN count(n) as count')
        total_count = result[0]['count'] if result else 0
        print(f'📊 Total AutoSchemaNode count: {total_count}')

        # Check nodes from the test job
        result = await manager.execute_read_transaction(
            'MATCH (n:AutoSchemaNode {job_id: "test_job_001"}) RETURN n.text as text, n.type as type ORDER BY n.text LIMIT 10'
        )
        print(f'📋 Nodes from test job ({len(result)} found):')
        for row in result:
            print(f'   • {row["text"]} ({row["type"]})')

        # Check relationships from the test job
        result = await manager.execute_read_transaction(
            'MATCH (a:AutoSchemaNode)-[r:AUTOSCHEMA_RELATION]->(b:AutoSchemaNode) WHERE r.job_id = "test_job_001" RETURN a.text as source, r.type as relation, b.text as target ORDER BY a.text LIMIT 10'
        )
        print(f'🔗 Relationships from test job ({len(result)} found):')
        for row in result:
            print(f'   • {row["source"]} --{row["relation"]}--> {row["target"]}')

        print(f'✅ Neo4j verification complete!')

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_neo4j())
