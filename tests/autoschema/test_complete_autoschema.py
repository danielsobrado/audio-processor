#!/usr/bin/env python3
"""
Test AutoSchemaKG extraction and Neo4j loading
"""
import sys
import os
import tempfile
import json
import asyncio
from datetime import datetime

# Add atlas_rag to path
atlas_rag_path = os.path.join(os.path.dirname(__file__), "app", "lib", "autoschema_kg")
if atlas_rag_path not in sys.path:
    sys.path.insert(0, atlas_rag_path)

print("🧪 AutoSchemaKG Complete Test - Extraction + Neo4j")
print("=" * 60)

# Get API key from environment
api_key = os.getenv("GRAPH_LLM_API_KEY")
if not api_key:
    print("❌ No GRAPH_LLM_API_KEY found")
    exit(1)

print(f"🔍 API Key: ***{api_key[-10:]}")

async def main():
    try:
        from atlas_rag.kg_construction.triple_extraction import KnowledgeGraphExtractor
        from atlas_rag.kg_construction.triple_config import ProcessingConfig
        from atlas_rag.llm_generator.llm_generator import LLMGenerator
        from openai import OpenAI
        from app.services.graph_service import GraphService
        from app.services.autoschema_neo4j_loader import AutoSchemaNeo4jLoader
        from app.db.graph_session import get_graph_db_manager

        # Simple text for testing
        sample_text = """
        John Smith works as a senior software engineer at Microsoft Corporation in Seattle.
        He graduated from Stanford University with a degree in Computer Science in 2015.
        Sarah Chen joined Google as a data scientist in Mountain View, California.
        She previously worked at Amazon Web Services for 3 years.
        """

        print(f"📄 Sample text: {sample_text.strip()}")

        # Create OpenRouter client
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        model_name = "meta-llama/llama-3.2-3b-instruct"
        print(f"🤖 Using model: {model_name}")

        # Create LLM Generator
        llm_generator = LLMGenerator(
            client=client,
            model_name=model_name
        )

        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        data_dir = os.path.join(temp_dir, "data")
        os.makedirs(data_dir, exist_ok=True)

        # Create config
        config = ProcessingConfig(
            model_path=model_name,
            data_directory=data_dir,
            filename_pattern="test",
            batch_size_triple=1,
            batch_size_concept=1,
            output_directory=temp_dir,
            max_new_tokens=512,
            max_workers=1,
            remove_doc_spaces=True,
            debug_mode=False,
            record=True,
        )

        # Create input file
        input_file = os.path.join(data_dir, "test.jsonl")
        with open(input_file, 'w', encoding='utf-8') as f:
            json_line = {
                "id": "test_001",
                "text": sample_text.strip(),
                "metadata": {"source": "test", "type": "business_text"}
            }
            f.write(json.dumps(json_line) + '\n')

        print(f"📁 Input file created: {os.path.getsize(input_file)} bytes")

        # Create extractor
        kg_extractor = KnowledgeGraphExtractor(llm_generator, config)

        print("⚡ Starting AutoSchemaKG extraction...")
        print("   🤖 Calling OpenRouter API...")

        try:
            # Run extraction
            kg_extractor.run_extraction()
            print("✅ Extraction completed!")

            # Look for the JSON output file
            extraction_dir = os.path.join(temp_dir, "kg_extraction")
            output_files = []

            if os.path.exists(extraction_dir):
                for file in os.listdir(extraction_dir):
                    if file.endswith('.json'):
                        output_files.append(os.path.join(extraction_dir, file))

            if not output_files:
                print("❌ No JSON output files found")
                return

            print(f"📄 Found {len(output_files)} output file(s)")

            # Process the JSON file and extract entities/relationships
            entities = []
            relationships = []

            for json_file in output_files:
                print(f"🔍 Processing: {os.path.basename(json_file)}")

                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Extract entity-relation pairs
                if 'entity_relation_dict' in data:
                    for rel in data['entity_relation_dict']:
                        if 'Head' in rel and 'Tail' in rel and 'Relation' in rel:
                            # Add entities
                            if rel['Head'] not in [e['text'] for e in entities]:
                                entities.append({
                                    'text': rel['Head'],
                                    'type': 'Entity',
                                    'job_id': 'test_001'
                                })
                            if rel['Tail'] not in [e['text'] for e in entities]:
                                entities.append({
                                    'text': rel['Tail'],
                                    'type': 'Entity',
                                    'job_id': 'test_001'
                                })

                            # Add relationship
                            relationships.append({
                                'source': rel['Head'],
                                'target': rel['Tail'],
                                'relation': rel['Relation'],
                                'job_id': 'test_001'
                            })

                # Extract event entities
                if 'event_entity_relation_dict' in data:
                    for event in data['event_entity_relation_dict']:
                        if 'Entity' in event and isinstance(event['Entity'], list):
                            for entity in event['Entity']:
                                if entity not in [e['text'] for e in entities]:
                                    entities.append({
                                        'text': entity,
                                        'type': 'Entity',
                                        'job_id': 'test_001'
                                    })

            print(f"\n📊 Extracted Results:")
            print(f"   📋 Entities: {len(entities)}")
            print(f"   🔗 Relationships: {len(relationships)}")

            # Show sample results
            if entities:
                print(f"\n📋 Sample Entities:")
                for entity in entities[:5]:
                    print(f"   • {entity['text']} ({entity['type']})")

            if relationships:
                print(f"\n🔗 Sample Relationships:")
                for rel in relationships[:5]:
                    print(f"   • {rel['source']} --{rel['relation']}--> {rel['target']}")

            if entities or relationships:
                # Now test Neo4j loading
                print(f"\n🗃️ Testing Neo4j loading...")

                try:
                    # Get the graph database manager
                    manager = await get_graph_db_manager()
                    if not manager.is_connected:
                        await manager.initialize()

                    # Test connection using GraphService for stats
                    graph_service = GraphService()
                    stats = await graph_service.get_database_stats()
                    print(f"✅ Neo4j connected - Nodes: {stats.get('nodes', 0)}, Relationships: {stats.get('relationships', 0)}")

                    # Load entities and relationships directly
                    nodes_loaded = 0
                    relationships_loaded = 0

                    # Load entities as nodes
                    for entity in entities:
                        query = """
                        CREATE (n:AutoSchemaNode {
                            job_id: $job_id,
                            text: $text,
                            type: $type
                        })
                        """
                        await manager.execute_write_transaction(
                            query, {
                                'job_id': entity['job_id'],
                                'text': entity['text'],
                                'type': entity['type']
                            }
                        )
                        nodes_loaded += 1

                    # Load relationships
                    for rel in relationships:
                        query = """
                        MATCH (a:AutoSchemaNode {text: $source, job_id: $job_id})
                        MATCH (b:AutoSchemaNode {text: $target, job_id: $job_id})
                        CREATE (a)-[r:AUTOSCHEMA_RELATION {
                            type: $relation,
                            job_id: $job_id
                        }]->(b)
                        """
                        await manager.execute_write_transaction(
                            query, {
                                'source': rel['source'],
                                'target': rel['target'],
                                'relation': rel['relation'],
                                'job_id': rel['job_id']
                            }
                        )
                        relationships_loaded += 1

                    print(f"✅ Neo4j loading completed!")
                    print(f"   📊 Nodes loaded: {nodes_loaded}")
                    print(f"   🔗 Relationships loaded: {relationships_loaded}")

                    # Verify the data in Neo4j
                    verify_query = """
                    MATCH (n:AutoSchemaNode {job_id: 'test_001'})
                    RETURN n.text as text, n.type as type
                    LIMIT 5
                    """
                    results = await manager.execute_read_transaction(verify_query)

                    print(f"\n🔍 Verification - Nodes in Neo4j:")
                    for result in results:
                        print(f"   • {result['text']} ({result['type']})")

                    # Check relationships
                    rel_query = """
                    MATCH (a:AutoSchemaNode)-[r:AUTOSCHEMA_RELATION]->(b:AutoSchemaNode)
                    WHERE r.job_id = 'test_001'
                    RETURN a.text as source, r.type as relation, b.text as target
                    LIMIT 5
                    """
                    rel_results = await manager.execute_read_transaction(rel_query)

                    print(f"\n🔗 Verification - Relationships in Neo4j:")
                    for result in rel_results:
                        print(f"   • {result['source']} --{result['relation']}--> {result['target']}")

                    print(f"\n🎉 SUCCESS! AutoSchemaKG + Neo4j integration working!")
                    print(f"💡 View results in Neo4j Browser: http://localhost:7474")
                    print(f"   Query: MATCH (n:AutoSchemaNode {{job_id: 'test_001'}}) RETURN n")

                except Exception as neo4j_error:
                    print(f"❌ Neo4j test failed: {neo4j_error}")
                    import traceback
                    traceback.print_exc()
            else:
                print("⚠️ No entities or relationships extracted to load into Neo4j")

        except Exception as extraction_error:
            print(f"❌ Extraction failed: {extraction_error}")
            import traceback
            traceback.print_exc()

        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print(f"\n🧹 Cleaned up {temp_dir}")

    except ImportError as e:
        print(f"❌ Import failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

print("\n🎉 Complete test finished!")
