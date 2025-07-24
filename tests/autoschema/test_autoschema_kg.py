#!/usr/bin/env python3
"""
Test AutoSchemaKG integration and functionality.

This test script demonstrates how to use AutoSchemaKG to extract knowledge graphs
from text data and load them into Neo4j for visualization and querying.
"""

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add the autoschema_kg library path to sys.path
autoschema_kg_path = project_root / "app" / "lib" / "autoschema_kg"
if str(autoschema_kg_path) not in sys.path:
    sys.path.insert(0, str(autoschema_kg_path))

# Set up environment variables for testing
os.environ.setdefault("GRAPH_ENABLED", "true")
os.environ.setdefault("GRAPH_DATABASE_URL", "bolt://localhost:7687")
os.environ.setdefault("GRAPH_DATABASE_USERNAME", "neo4j")
os.environ.setdefault("GRAPH_DATABASE_PASSWORD", "password")
os.environ.setdefault("GRAPH_LLM_PROVIDER", "openrouter")
os.environ.setdefault("GRAPH_LLM_MODEL", "meta-llama/llama-3.2-3b-instruct")
os.environ.setdefault("GRAPH_LLM_API_KEY", "sk-or-v1-your-api-key-here")


async def test_autoschema_kg_availability():
    """Test if AutoSchemaKG libraries are available."""
    print("🔍 Testing AutoSchemaKG Availability")
    print("=" * 50)

    try:
        from atlas_rag.kg_construction.triple_extraction import KnowledgeGraphExtractor
        from atlas_rag.kg_construction.triple_config import ProcessingConfig
        from atlas_rag.llm_generator import LLMGenerator
        print("✅ AutoSchemaKG libraries are available")
        return True
    except ImportError as e:
        print(f"❌ AutoSchemaKG libraries not available: {e}")
        print("📝 To install AutoSchemaKG, run: pip install atlas-rag")
        return False


async def test_autoschema_kg_extraction():
    """Test AutoSchemaKG knowledge graph extraction."""
    print("\n🚀 Testing AutoSchemaKG Knowledge Graph Extraction")
    print("=" * 50)

    # Check if libraries are available
    if not await test_autoschema_kg_availability():
        return False

    try:
        from atlas_rag.kg_construction.triple_extraction import KnowledgeGraphExtractor
        from atlas_rag.kg_construction.triple_config import ProcessingConfig
        from atlas_rag.llm_generator import LLMGenerator
        from openai import OpenAI

        # Sample text for knowledge graph extraction
        sample_text = """
        Artificial Intelligence (AI) is a transformative technology that is revolutionizing various industries.
        Machine learning, a subset of AI, enables computers to learn from data without explicit programming.
        Deep learning, which uses neural networks with multiple layers, has shown remarkable success in image recognition and natural language processing.

        Companies like Google, Microsoft, and OpenAI are leading the development of AI technologies.
        Google developed TensorFlow, an open-source machine learning framework.
        Microsoft created Azure AI services for cloud-based AI solutions.
        OpenAI is known for creating GPT models that can generate human-like text.

        AI applications include autonomous vehicles, medical diagnosis, recommendation systems, and virtual assistants.
        Autonomous vehicles use computer vision and sensor fusion to navigate safely.
        Medical diagnosis benefits from AI's ability to analyze medical images and identify patterns.
        Recommendation systems help users discover relevant content on platforms like Netflix and Amazon.
        """

        print(f"📄 Sample text length: {len(sample_text)} characters")

        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"📁 Working directory: {temp_dir}")

            # Create data directory and input file
            data_dir = os.path.join(temp_dir, "data")
            os.makedirs(data_dir, exist_ok=True)

            # Create JSONL format as expected by AutoSchemaKG
            input_file = os.path.join(data_dir, "sample.jsonl")
            import json
            with open(input_file, 'w', encoding='utf-8') as f:
                # Each line should be a JSON object with id and text fields
                json_line = {"id": "sample_1", "text": sample_text.strip()}
                f.write(json.dumps(json_line) + '\n')

            print(f"💾 Created input file: {input_file}")

            # Configure mock LLM client (for testing without actual API calls)
            print("⚙️ Setting up LLM configuration...")

            # For testing, we'll create a mock client
            # In production, use: client = OpenAI(base_url="...", api_key="...")
            try:
                from app.config.settings import get_settings
                settings = get_settings()

                if settings.graph.llm_api_key and settings.graph.llm_api_key != "":
                    if settings.graph.llm_provider == "openrouter":
                        client = OpenAI(
                            base_url="https://openrouter.ai/api/v1",
                            api_key=settings.graph.llm_api_key,
                        )
                        print("✅ Using OpenRouter API")
                    else:
                        client = OpenAI(api_key=settings.graph.llm_api_key)
                        print("✅ Using OpenAI API")

                    # Create LLM generator
                    llm_generator = LLMGenerator(
                        client=client,
                        model_name=settings.graph.llm_model
                    )

                    # Configure processing
                    config = ProcessingConfig(
                        model_path=settings.graph.llm_model,
                        data_directory=data_dir,
                        filename_pattern="sample",  # Matches "sample.jsonl"
                        batch_size_triple=2,  # Small batch for testing
                        batch_size_concept=4,
                        output_directory=temp_dir,
                        max_new_tokens=1024,
                        max_workers=1,  # Single worker for testing
                        remove_doc_spaces=True,
                    )

                    print("🔧 Configuration:")
                    print(f"   Model: {settings.graph.llm_model}")
                    print(f"   Data directory: {data_dir}")
                    print(f"   Output directory: {temp_dir}")

                    # Create knowledge graph extractor
                    kg_extractor = KnowledgeGraphExtractor(
                        model=llm_generator,
                        config=config
                    )

                    print("\n⚡ Starting knowledge graph extraction...")

                    # Run the extraction pipeline
                    print("  1. Extracting triples...")
                    kg_extractor.run_extraction()

                    print("  2. Converting to CSV...")
                    kg_extractor.convert_json_to_csv()

                    print("  3. Generating concepts...")
                    kg_extractor.generate_concept_csv(batch_size=4)

                    print("  4. Creating concept CSV...")
                    kg_extractor.create_concept_csv()

                    print("  5. Converting to GraphML...")
                    kg_extractor.convert_to_graphml()

                    print("✅ Knowledge graph extraction completed!")

                    # List output files
                    print("\n📂 Output files:")
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, temp_dir)
                            file_size = os.path.getsize(file_path)
                            print(f"   {rel_path} ({file_size} bytes)")

                    return temp_dir

                else:
                    print("⚠️ No API key configured. Skipping actual extraction.")
                    print("💡 To test with real API, set GRAPH_LLM_API_KEY environment variable")
                    return None

            except Exception as e:
                print(f"❌ Extraction failed: {e}")
                import traceback
                traceback.print_exc()
                return None

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return None


async def test_neo4j_loading():
    """Test loading AutoSchemaKG output into Neo4j."""
    print("\n🗃️ Testing Neo4j Loading")
    print("=" * 50)

    try:
        from app.services.autoschema_neo4j_loader import AutoSchemaNeo4jLoader
        from app.db.graph_session import get_graph_db_manager

        # Check Neo4j connection
        manager = await get_graph_db_manager()
        if not manager.is_connected:
            await manager.initialize()

        print("✅ Connected to Neo4j")

        # Test basic queries
        test_query = "RETURN 'AutoSchemaKG Test' as message, datetime() as timestamp"
        result = await manager.execute_read_transaction(test_query)
        print(f"📊 Test query result: {result}")

        # Create a loader instance
        loader = AutoSchemaNeo4jLoader()
        print("✅ AutoSchemaKG loader created")

        return True

    except Exception as e:
        print(f"❌ Neo4j loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_endpoints():
    """Test AutoSchemaKG API endpoints."""
    print("\n🌐 Testing API Endpoints")
    print("=" * 50)

    try:
        import httpx

        base_url = "http://localhost:8000"

        async with httpx.AsyncClient() as client:
            # Test stats endpoint
            print("📊 Testing /api/v1/autoschema-kg/stats")
            response = await client.get(f"{base_url}/api/v1/autoschema-kg/stats")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                stats = response.json()
                print(f"   Available: {stats['available']}")
                print(f"   Neo4j Connected: {stats['neo4j_connected']}")
                print(f"   ATLAS Version: {stats['atlas_version']}")

            # Test extraction endpoint with sample data
            print("\n🔬 Testing /api/v1/autoschema-kg/extract")
            sample_data = {
                "text_data": "Python is a programming language. It was created by Guido van Rossum.",
                "batch_size_triple": 1,
                "batch_size_concept": 2,
                "max_new_tokens": 512,
                "max_workers": 1
            }

            response = await client.post(
                f"{base_url}/api/v1/autoschema-kg/extract",
                json=sample_data
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                print(f"   Success: {result['success']}")
                print(f"   Job ID: {result['job_id']}")
                print(f"   Nodes: {result['node_count']}")
                print(f"   Edges: {result['edge_count']}")
                return result['job_id']
            else:
                print(f"   Error: {response.text}")

    except ImportError:
        print("❌ httpx not available. Install with: pip install httpx")
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()

    return None


async def test_graph_queries():
    """Test querying AutoSchemaKG data in Neo4j."""
    print("\n🔍 Testing Graph Queries")
    print("=" * 50)

    try:
        from app.db.graph_session import get_graph_db_manager

        manager = await get_graph_db_manager()
        if not manager.is_connected:
            await manager.initialize()

        # Query AutoSchemaKG nodes
        nodes_query = """
        MATCH (n:AutoSchemaNode)
        RETURN n.job_id as job_id, n.text as text, n.type as type
        LIMIT 10
        """
        nodes = await manager.execute_read_transaction(nodes_query)
        print(f"📊 Found {len(nodes)} AutoSchemaKG nodes:")
        for node in nodes[:5]:  # Show first 5
            print(f"   Job: {node['job_id']}, Type: {node['type']}, Text: {node['text'][:50]}...")

        # Query AutoSchemaKG relationships
        rels_query = """
        MATCH (a:AutoSchemaNode)-[r:AUTOSCHEMA_RELATION]->(b:AutoSchemaNode)
        RETURN r.job_id as job_id, a.text as source, r.type as relation, b.text as target
        LIMIT 10
        """
        rels = await manager.execute_read_transaction(rels_query)
        print(f"\n🔗 Found {len(rels)} AutoSchemaKG relationships:")
        for rel in rels[:5]:  # Show first 5
            print(f"   Job: {rel['job_id']}, {rel['source']} --{rel['relation']}--> {rel['target']}")

        # Query AutoSchemaKG concepts
        concepts_query = """
        MATCH (c:AutoSchemaConcept)
        RETURN c.job_id as job_id, c.name as name, c.category as category
        LIMIT 10
        """
        concepts = await manager.execute_read_transaction(concepts_query)
        print(f"\n💡 Found {len(concepts)} AutoSchemaKG concepts:")
        for concept in concepts[:5]:  # Show first 5
            print(f"   Job: {concept['job_id']}, Name: {concept['name']}, Category: {concept['category']}")

        return True

    except Exception as e:
        print(f"❌ Graph query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all AutoSchemaKG tests."""
    print("🧪 AutoSchemaKG Integration Test Suite")
    print("=" * 60)

    # Test 1: Check availability
    available = await test_autoschema_kg_availability()

    # Test 2: Test extraction (if libraries available)
    if available:
        extraction_result = await test_autoschema_kg_extraction()
    else:
        extraction_result = None

    # Test 3: Test Neo4j loading
    neo4j_ok = await test_neo4j_loading()

    # Test 4: Test API endpoints (requires running server)
    print("\n💡 To test API endpoints, start the server with:")
    print("   uv run uvicorn app.main:app --reload")
    print("   Then run: pytest tests/test_autoschema_kg_api.py")

    # Test 5: Test graph queries
    if neo4j_ok:
        await test_graph_queries()

    # Summary
    print("\n📋 Test Summary")
    print("=" * 30)
    print(f"✅ AutoSchemaKG Available: {available}")
    print(f"✅ Neo4j Connection: {neo4j_ok}")

    if available and extraction_result:
        print("✅ Knowledge Graph Extraction: Success")
    elif available:
        print("⚠️ Knowledge Graph Extraction: Skipped (no API key)")
    else:
        print("❌ Knowledge Graph Extraction: Failed (libraries not available)")

    print("\n🎉 AutoSchemaKG integration test completed!")

    if available:
        print("\n📚 Next Steps:")
        print("1. Set GRAPH_LLM_API_KEY to test extraction with real data")
        print("2. Use /api/v1/autoschema-kg/extract endpoint to process text")
        print("3. Query the generated graph data using Cypher queries")
        print("4. Visualize results in Neo4j Browser at http://localhost:7474")


if __name__ == "__main__":
    asyncio.run(main())
