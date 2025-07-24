#!/usr/bin/env python3
"""
Check for duplicates in Neo4j AutoSchemaKG data
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

async def check_duplicates():
    try:
        print('🔍 Checking for duplicates in Neo4j AutoSchemaKG data...')
        manager = await get_graph_db_manager()
        if not manager.is_connected:
            await manager.initialize()

        print('\n📊 Overall Statistics:')
        # Total counts
        result = await manager.execute_read_transaction('MATCH (n:AutoSchemaNode) RETURN count(n) as count')
        total_nodes = result[0]['count'] if result else 0
        print(f'   Total nodes: {total_nodes}')

        result = await manager.execute_read_transaction('MATCH ()-[r:AUTOSCHEMA_RELATION]->() RETURN count(r) as count')
        total_rels = result[0]['count'] if result else 0
        print(f'   Total relationships: {total_rels}')

        print('\n🔍 Checking for duplicate nodes (same text):')
        result = await manager.execute_read_transaction("""
            MATCH (n:AutoSchemaNode)
            WITH n.text as text, collect(n) as nodes, count(n) as cnt
            WHERE cnt > 1
            RETURN text, cnt
            ORDER BY cnt DESC
        """)

        if result:
            print(f'   Found {len(result)} sets of duplicate nodes:')
            for row in result:
                print(f'   • "{row["text"]}" appears {row["cnt"]} times')
        else:
            print('   ✅ No duplicate nodes found')

        print('\n🔗 Checking for duplicate relationships:')
        result = await manager.execute_read_transaction("""
            MATCH (a:AutoSchemaNode)-[r:AUTOSCHEMA_RELATION]->(b:AutoSchemaNode)
            WITH a.text as source, r.type as relation, b.text as target,
                 collect(r) as rels, count(r) as cnt
            WHERE cnt > 1
            RETURN source, relation, target, cnt
            ORDER BY cnt DESC
            LIMIT 20
        """)

        if result:
            print(f'   Found {len(result)} sets of duplicate relationships:')
            for row in result:
                print(f'   • "{row["source"]}" --{row["relation"]}--> "{row["target"]}" appears {row["cnt"]} times')
        else:
            print('   ✅ No duplicate relationships found')

        print('\n💼 Checking specific investment/partnership relationships:')
        result = await manager.execute_read_transaction("""
            MATCH (a:AutoSchemaNode)-[r:AUTOSCHEMA_RELATION]->(b:AutoSchemaNode)
            WHERE r.type CONTAINS 'partner' OR r.type CONTAINS 'fund' OR r.type CONTAINS 'invest'
            RETURN a.text as source, r.type as relation, b.text as target, r.job_id as job_id
            ORDER BY source, relation, target
        """)

        if result:
            print(f'   Found {len(result)} investment/partnership relationships:')
            current_triple = None
            duplicate_count = 0

            for row in result:
                triple = (row["source"], row["relation"], row["target"])
                if triple == current_triple:
                    duplicate_count += 1
                    print(f'   🔴 DUPLICATE: "{row["source"]}" --{row["relation"]}--> "{row["target"]}" (job: {row["job_id"]})')
                else:
                    if duplicate_count > 0:
                        print(f'      ↳ Total duplicates for previous: {duplicate_count}')
                        duplicate_count = 0
                    current_triple = triple
                    print(f'   • "{row["source"]}" --{row["relation"]}--> "{row["target"]}" (job: {row["job_id"]})')

        print('\n📈 Node distribution by text:')
        result = await manager.execute_read_transaction("""
            MATCH (n:AutoSchemaNode)
            RETURN n.text as text, count(n) as count
            ORDER BY count DESC
            LIMIT 15
        """)

        for row in result:
            status = "🔴 DUPLICATE" if row["count"] > 1 else "✅"
            print(f'   {status} "{row["text"]}" - {row["count"]} node(s)')

        print('\n🧹 Commands to clean up duplicates:')
        print('   Remove duplicate nodes (keeping one of each):')
        print('   MATCH (n:AutoSchemaNode)')
        print('   WITH n.text as text, collect(n) as nodes')
        print('   WHERE size(nodes) > 1')
        print('   FOREACH (node in tail(nodes) | DELETE node)')

        print('\n   Remove duplicate relationships:')
        print('   MATCH (a:AutoSchemaNode)-[r:AUTOSCHEMA_RELATION]->(b:AutoSchemaNode)')
        print('   WITH a, b, r.type as relType, collect(r) as rels')
        print('   WHERE size(rels) > 1')
        print('   FOREACH (rel in tail(rels) | DELETE rel)')

    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_duplicates())
