#!/usr/bin/env python3
"""
Clear AutoSchemaKG data from Neo4j
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

async def clear_autoschema_data():
    try:
        print('🧹 Clearing AutoSchemaKG data from Neo4j...')
        manager = await get_graph_db_manager()
        if not manager.is_connected:
            await manager.initialize()

        # Check current count before deletion
        result = await manager.execute_read_transaction('MATCH (n:AutoSchemaNode) RETURN count(n) as count')
        before_count = result[0]['count'] if result else 0
        print(f'📊 AutoSchemaNode count before deletion: {before_count}')

        # Check relationships count before deletion
        result = await manager.execute_read_transaction('MATCH ()-[r:AUTOSCHEMA_RELATION]->() RETURN count(r) as count')
        rel_before_count = result[0]['count'] if result else 0
        print(f'🔗 AUTOSCHEMA_RELATION count before deletion: {rel_before_count}')

        if before_count == 0 and rel_before_count == 0:
            print('✅ No AutoSchemaKG data found to delete.')
            return

        # Delete all AutoSchemaKG relationships first
        print('🗑️ Deleting AutoSchemaKG relationships...')
        result = await manager.execute_write_transaction(
            'MATCH ()-[r:AUTOSCHEMA_RELATION]->() DELETE r RETURN count(r) as deleted'
        )
        rel_deleted = result[0]['deleted'] if result else 0
        print(f'✅ Deleted {rel_deleted} relationships')

        # Delete all AutoSchemaKG nodes
        print('🗑️ Deleting AutoSchemaKG nodes...')
        result = await manager.execute_write_transaction(
            'MATCH (n:AutoSchemaNode) DELETE n RETURN count(n) as deleted'
        )
        nodes_deleted = result[0]['deleted'] if result else 0
        print(f'✅ Deleted {nodes_deleted} nodes')

        # Verify deletion
        result = await manager.execute_read_transaction('MATCH (n:AutoSchemaNode) RETURN count(n) as count')
        after_count = result[0]['count'] if result else 0
        print(f'📊 AutoSchemaNode count after deletion: {after_count}')

        result = await manager.execute_read_transaction('MATCH ()-[r:AUTOSCHEMA_RELATION]->() RETURN count(r) as count')
        rel_after_count = result[0]['count'] if result else 0
        print(f'🔗 AUTOSCHEMA_RELATION count after deletion: {rel_after_count}')

        print(f'🎉 Successfully cleared all AutoSchemaKG data from Neo4j!')

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

async def clear_specific_job(job_id: str):
    try:
        print(f'🧹 Clearing AutoSchemaKG data for job: {job_id}...')
        manager = await get_graph_db_manager()
        if not manager.is_connected:
            await manager.initialize()

        # Check current count for this job
        result = await manager.execute_read_transaction(
            'MATCH (n:AutoSchemaNode {job_id: $job_id}) RETURN count(n) as count',
            {'job_id': job_id}
        )
        before_count = result[0]['count'] if result else 0
        print(f'📊 Nodes for job {job_id} before deletion: {before_count}')

        if before_count == 0:
            print(f'✅ No data found for job {job_id}.')
            return

        # Delete relationships for this job
        result = await manager.execute_write_transaction(
            'MATCH ()-[r:AUTOSCHEMA_RELATION {job_id: $job_id}]->() DELETE r RETURN count(r) as deleted',
            {'job_id': job_id}
        )
        rel_deleted = result[0]['deleted'] if result else 0
        print(f'✅ Deleted {rel_deleted} relationships for job {job_id}')

        # Delete nodes for this job
        result = await manager.execute_write_transaction(
            'MATCH (n:AutoSchemaNode {job_id: $job_id}) DELETE n RETURN count(n) as deleted',
            {'job_id': job_id}
        )
        nodes_deleted = result[0]['deleted'] if result else 0
        print(f'✅ Deleted {nodes_deleted} nodes for job {job_id}')

        print(f'🎉 Successfully cleared data for job {job_id}!')

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Clear AutoSchemaKG data from Neo4j')
    parser.add_argument('--job-id', help='Clear data for a specific job ID only')
    parser.add_argument('--all', action='store_true', help='Clear all AutoSchemaKG data')

    args = parser.parse_args()

    if args.job_id:
        asyncio.run(clear_specific_job(args.job_id))
    elif args.all:
        asyncio.run(clear_autoschema_data())
    else:
        print("Usage:")
        print("  Clear all AutoSchemaKG data:")
        print("    python clear_autoschema_data.py --all")
        print("  Clear specific job data:")
        print("    python clear_autoschema_data.py --job-id test_job_001")
