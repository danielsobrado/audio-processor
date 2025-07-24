#!/usr/bin/env python3
"""
Process AutoSchemaKG JSON output and convert to CSV, then load to Neo4j
"""
import sys
import os
import tempfile
import json
import csv
import pandas as pd
from datetime import datetime

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Go up 3 levels from tests/autoschema/
sys.path.insert(0, project_root)

# Load .env file from project root
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'))

# Add atlas_rag to path
atlas_rag_path = os.path.join(project_root, "app", "lib", "autoschema_kg")
if atlas_rag_path not in sys.path:
    sys.path.insert(0, atlas_rag_path)

print("🚀 AutoSchemaKG PoC/Demo - Rich Knowledge Graph Generation")
print("=" * 65)

# Get API key from environment
api_key = os.getenv("GRAPH_LLM_API_KEY")
if not api_key:
    print("❌ No GRAPH_LLM_API_KEY found")
    exit(1)

print(f"🔍 API Key: ***{api_key[-10:]}")

try:
    from atlas_rag.kg_construction.triple_extraction import KnowledgeGraphExtractor
    from atlas_rag.kg_construction.triple_config import ProcessingConfig
    from atlas_rag.llm_generator.llm_generator import LLMGenerator
    from openai import OpenAI

    # Rich text for PoC/demo - multiple entities, relationships, and domains
    sample_text = """
    TechCorp Inc. is a multinational technology company headquartered in San Francisco, California, founded by CEO Michael Chen in 2018.
    The company specializes in artificial intelligence, cloud computing, and enterprise software solutions.

    Dr. Sarah Johnson serves as the Chief Technology Officer and leads the AI Research Division based in Austin, Texas.
    She previously worked at Google for 8 years and holds a PhD in Computer Science from Stanford University.
    Under her leadership, the AI team has developed several breakthrough products including AutoML Platform and
    the Neural Processing Engine, which powers TechCorp's flagship product, IntelliCloud.

    The company's Chief Financial Officer, David Rodriguez, joined from Goldman Sachs where he managed tech investments
    for 12 years. He oversees TechCorp's recent $500 million Series C funding round led by Andreessen Horowitz,
    with participation from Sequoia Capital and Index Ventures. This brings the company's total valuation to $2.8 billion.

    TechCorp has strategic partnerships with Amazon Web Services, Microsoft Azure, and IBM Watson for cloud infrastructure.
    The company operates development centers in Seattle, Boston, and London, employing over 1,200 software engineers,
    data scientists, and product managers. Their largest client is Netflix, which uses TechCorp's IntelliCloud platform
    to optimize content recommendations for over 230 million subscribers worldwide.

    The Engineering team, led by VP of Engineering Lisa Park, recently launched the Quantum Analytics Suite,
    a machine learning platform that processes over 10 billion data points daily. This platform integrates with
    Salesforce, HubSpot, and Oracle databases to provide real-time business intelligence.

    In 2023, TechCorp acquired StartupAI, a promising computer vision company founded by former Tesla engineers,
    for $180 million. This acquisition brought 45 additional researchers and expanded TechCorp's capabilities
    in autonomous systems and robotics. The merged team is now working on Project Phoenix, an autonomous
    logistics system being piloted by FedEx and UPS.

    TechCorp went public in October 2023 on NASDAQ under ticker symbol TECH, with an IPO price of $42 per share.
    The stock is currently trading at $78 per share, making it one of the best-performing tech IPOs of the year.
    Major shareholders include Fidelity Investments, BlackRock, and Vanguard Group.
    """
    print(f"📄 Sample text length: {len(sample_text)} characters")

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

    # Create config for richer extraction
    config = ProcessingConfig(
        model_path=model_name,
        data_directory=data_dir,
        filename_pattern="test",
        batch_size_triple=2,  # Increased for better processing
        batch_size_concept=4,  # Increased for better processing
        output_directory=temp_dir,
        max_new_tokens=1024,  # Increased for longer text
        max_workers=1,
        remove_doc_spaces=True,
        debug_mode=True,
        record=True,
    )

    # Create proper JSONL input file
    input_file = os.path.join(data_dir, "test.jsonl")
    with open(input_file, 'w', encoding='utf-8') as f:
        json_line = {
            "id": "sample_1",
            "text": sample_text,
            "metadata": {"source": "test", "type": "business_text"}
        }
        f.write(json.dumps(json_line) + '\n')

    print(f"📁 Input file: {input_file}")

    # Create extractor and run
    kg_extractor = KnowledgeGraphExtractor(llm_generator, config)

    print("⚡ Starting extraction...")
    kg_extractor.run_extraction()

    # Find the JSON output file
    extraction_dir = os.path.join(temp_dir, "kg_extraction")
    json_files = []
    if os.path.exists(extraction_dir):
        for file in os.listdir(extraction_dir):
            if file.endswith('.json'):
                json_files.append(os.path.join(extraction_dir, file))

    print(f"\n📊 Found {len(json_files)} JSON output files")

    # Process each JSON file
    all_entities = []
    all_relationships = []
    all_events = []

    for json_file in json_files:
        print(f"📄 Processing: {os.path.basename(json_file)}")

        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        job_id = data.get('id', 'unknown')

        # Extract entity-relationships
        entity_relations = data.get('entity_relation_dict', [])
        for rel in entity_relations:
            all_relationships.append({
                'job_id': job_id,
                'source': rel.get('Head', ''),
                'relation': rel.get('Relation', ''),
                'target': rel.get('Tail', '')
            })

            # Add entities
            if rel.get('Head'):
                all_entities.append({
                    'id': f"{job_id}_entity_{len(all_entities)}",  # Add unique ID
                    'job_id': job_id,
                    'text': rel.get('Head'),
                    'type': 'Entity'
                })
            if rel.get('Tail'):
                all_entities.append({
                    'id': f"{job_id}_entity_{len(all_entities)}",  # Add unique ID
                    'job_id': job_id,
                    'text': rel.get('Tail'),
                    'type': 'Entity'
                })

        # Extract event-entities
        event_entities = data.get('event_entity_relation_dict', [])
        for event in event_entities:
            event_text = event.get('Event', '')
            entities = event.get('Entity', [])

            if event_text:
                all_events.append({
                    'id': f"{job_id}_event_{len(all_events)}",  # Add unique ID
                    'job_id': job_id,
                    'text': event_text,
                    'type': 'Event',
                    'entities': ', '.join(entities) if entities else ''
                })

    # Remove duplicates
    entities_df = pd.DataFrame(all_entities).drop_duplicates()
    relationships_df = pd.DataFrame(all_relationships).drop_duplicates()
    events_df = pd.DataFrame(all_events).drop_duplicates()

    print(f"\n🎯 Extraction Results:")
    print(f"   📊 Unique Entities: {len(entities_df)}")
    print(f"   🔗 Relationships: {len(relationships_df)}")
    print(f"   📅 Events: {len(events_df)}")

    # Show sample data
    if len(entities_df) > 0:
        print(f"\n📋 Sample Entities (showing first 10):")
        for _, entity in entities_df.head(10).iterrows():
            print(f"   • {entity['text']} ({entity['type']})")

    if len(relationships_df) > 0:
        print(f"\n🔗 Sample Relationships (showing first 10):")
        for _, rel in relationships_df.head(10).iterrows():
            print(f"   • {rel['source']} --{rel['relation']}--> {rel['target']}")

    if len(events_df) > 0:
        print(f"\n📅 Sample Events (showing first 5):")
        for _, event in events_df.head(5).iterrows():
            print(f"   • {event['text']} (entities: {event['entities']})")

    # Save to CSV files with correct naming for the loader
    csv_dir = os.path.join(temp_dir, "csv_output")
    os.makedirs(csv_dir, exist_ok=True)

    entities_csv = os.path.join(csv_dir, "nodes.csv")  # Changed from entities.csv
    relationships_csv = os.path.join(csv_dir, "relations.csv")  # Changed from relationships.csv
    events_csv = os.path.join(csv_dir, "concepts.csv")  # Changed from events.csv

    entities_df.to_csv(entities_csv, index=False)
    relationships_df.to_csv(relationships_csv, index=False)
    events_df.to_csv(events_csv, index=False)

    print(f"\n💾 CSV files saved:")
    print(f"   📄 Nodes: {entities_csv}")
    print(f"   📄 Relations: {relationships_csv}")
    print(f"   📄 Concepts: {events_csv}")

    # Now test Neo4j loading
    try:
        from app.services.autoschema_neo4j_loader import AutoSchemaNeo4jLoader
        from app.services.graph_service import GraphService

        print(f"\n🗃️ Testing Neo4j loading...")

        # Create graph service
        from app.config.settings import get_settings
        settings = get_settings()
        graph_service = GraphService()

        # Test connection
        async def test_neo4j():
            try:
                # Create loader
                loader = AutoSchemaNeo4jLoader()

                # Load data using the correct method
                result = await loader.load_csv_data(
                    output_directory=csv_dir,
                    job_id="demo_job_001"
                )

                print(f"✅ Neo4j loading result: {result}")
                return result

            except Exception as e:
                print(f"❌ Neo4j loading failed: {e}")
                return None

        # Run async test
        import asyncio
        result = asyncio.run(test_neo4j())

        if result:
            print(f"\n🎉 SUCCESS! AutoSchemaKG PoC/Demo data loaded into Neo4j!")
            print(f"   📊 Nodes loaded: {result.get('nodes_loaded', 0)}")
            print(f"   🔗 Relationships loaded: {result.get('relationships_loaded', 0)}")
            print(f"   📅 Concepts loaded: {result.get('concepts_loaded', 0)}")
            print(f"\n💡 View your rich knowledge graph in Neo4j Browser (http://localhost:7474):")
            print(f"   Username: neo4j")
            print(f"   Password: password")
            print(f"\n📋 Demo Queries:")
            print(f"   🌐 Full interactive graph visualization:")
            print(f"      MATCH (a:AutoSchemaNode)-[r:AUTOSCHEMA_RELATION]->(b:AutoSchemaNode)")
            print(f"      RETURN a, r, b LIMIT 50")
            print(f"\n   💼 Show company relationships:")
            print(f"      MATCH (a:AutoSchemaNode)-[r:AUTOSCHEMA_RELATION]->(b:AutoSchemaNode)")
            print(f"      WHERE a.text CONTAINS 'TechCorp' OR b.text CONTAINS 'TechCorp'")
            print(f"      RETURN a.text as Source, r.type as Relationship, b.text as Target")
            print(f"\n   👥 Show people and their roles:")
            print(f"      MATCH (a:AutoSchemaNode)-[r:AUTOSCHEMA_RELATION]->(b:AutoSchemaNode)")
            print(f"      WHERE r.type CONTAINS 'CEO' OR r.type CONTAINS 'CTO' OR r.type CONTAINS 'CFO'")
            print(f"      RETURN a.text, r.type, b.text")
            print(f"\n   � Show partnerships and investments:")
            print(f"      MATCH (a:AutoSchemaNode)-[r:AUTOSCHEMA_RELATION]->(b:AutoSchemaNode)")
            print(f"      WHERE r.type CONTAINS 'partner' OR r.type CONTAINS 'fund' OR r.type CONTAINS 'invest'")
            print(f"      RETURN a.text, r.type, b.text")
            print(f"\n   📈 View all data as network (for graph visualization):")
            print(f"      MATCH (n:AutoSchemaNode {{job_id: 'demo_job_001'}}) RETURN n")

    except Exception as e:
        print(f"❌ Neo4j test failed: {e}")

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

print("\n🎉 AutoSchemaKG processing completed!")
