#!/usr/bin/env python3
"""
Debug AutoSchemaKG extraction to see raw outputs
"""
import sys
import os
import tempfile
import json
from datetime import datetime

# Add atlas_rag to path
atlas_rag_path = os.path.join(os.path.dirname(__file__), "app", "lib", "autoschema_kg")
if atlas_rag_path not in sys.path:
    sys.path.insert(0, atlas_rag_path)

print("🧪 AutoSchemaKG Debug Test")
print("=" * 50)

# Get API key from environment - try loading .env if not found
api_key = os.getenv("GRAPH_LLM_API_KEY")
if not api_key:
    print("🔍 GRAPH_LLM_API_KEY not found in environment, loading .env file...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("GRAPH_LLM_API_KEY")
        if api_key:
            print("✅ Successfully loaded API key from .env file")
        else:
            print("❌ GRAPH_LLM_API_KEY not found in .env file either")
            print("💡 Please set GRAPH_LLM_API_KEY in your .env file")
            exit(1)
    except ImportError:
        print("❌ python-dotenv not available, please install it: pip install python-dotenv")
        print("💡 Or set the environment variable manually: $env:GRAPH_LLM_API_KEY='your-key'")
        exit(1)
else:
    print("✅ Found GRAPH_LLM_API_KEY in environment")

print(f"🔍 API Key: ***{api_key[-10:]}")

try:
    # No need to import atlas_rag directly since we're using the API
    print("🔄 Using API endpoints for extraction and loading")

    def run_extraction():
        """Run the knowledge graph extraction via API"""
        # Larger, more complex text for testing
        sample_text = """
        Dr. Sarah Johnson is the Chief Technology Officer at TechCorp, a leading artificial intelligence company based in San Francisco.
        She previously worked as a Senior Research Scientist at Google DeepMind from 2018 to 2023, where she led the development of
        large language models. Dr. Johnson earned her PhD in Computer Science from MIT in 2017, specializing in neural networks and
        machine learning. Her doctoral advisor was Professor Andrew Chen, who is now the Director of AI Research at Stanford University.

        TechCorp was founded in 2020 by Michael Zhang and Lisa Rodriguez. The company has raised $150 million in Series B funding
        led by Venture Capital Partners, with participation from Innovation Fund and TechStart Accelerator. TechCorp's headquarters
        are located in the SOMA district of San Francisco, and they have additional offices in New York, London, and Tokyo.

        The company's flagship product is an AI assistant called "IntelliBot" that helps businesses automate customer service.
        IntelliBot was launched in January 2023 and has already been adopted by over 500 companies including Netflix, Spotify,
        and Airbnb. The technology uses advanced natural language processing and was developed using TechCorp's proprietary
        "NeuralCore" framework.

        In 2024, TechCorp announced a strategic partnership with Amazon Web Services to integrate IntelliBot into AWS's cloud
        platform. This partnership allows TechCorp to scale their services globally and reach millions of potential customers.
        Dr. Johnson stated that this collaboration represents a major milestone for the company and will accelerate their mission
        to democratize AI technology.
        """
        print(f"📄 Sample text ({len(sample_text)} characters):")
        print(f"   Preview: {sample_text[:200]}...")

        try:
            import requests

            # Use our API endpoint to run extraction
            url = "http://localhost:8000/api/v1/autoschema-kg/extract"

            data = {
                "text_data": sample_text,
                "batch_size_triple": 1,
                "batch_size_concept": 1,
                "max_new_tokens": 512,
                "max_workers": 1
            }

            print(f"🚀 Starting extraction via API: {url}")

            response = requests.post(url, json=data)

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Extraction completed successfully!")
                print(f"   📊 Job ID: {result['job_id']}")
                print(f"   � {result['node_count']} nodes extracted")
                print(f"   📊 {result['edge_count']} edges extracted")
                print(f"   📊 {result['concept_count']} concepts extracted")
                print(f"   � Output directory: {result['output_directory']}")

                return result['job_id'], result['output_directory']
            else:
                print(f"❌ Extraction failed: {response.status_code}")
                print(f"   Error: {response.text}")
                return None, None

        except Exception as e:
            print(f"❌ Error during extraction: {e}")
            import traceback
            traceback.print_exc()
            return None, None

    def load_to_neo4j(job_id, extraction_dir):
        """Load extraction results to Neo4j using our API endpoint"""
        try:
            import requests

            # Use our existing endpoint with job_id from extraction
            url = f"http://localhost:8000/api/v1/autoschema-kg/load-to-neo4j/{job_id}"

            # Pass extraction directory as query parameter
            params = {
                "output_directory": extraction_dir
            }

            print(f"\n🚀 Loading to Neo4j via API: {url}")
            print(f"   📁 Directory: {extraction_dir}")
            print(f"   🆔 Job ID: {job_id}")

            response = requests.post(url, params=params)

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully loaded to Neo4j!")
                print(f"   📊 {result.get('nodes_created', 0)} nodes created")
                print(f"   📊 {result.get('relationships_created', 0)} relationships created")
                print(f"   📊 {result.get('files_processed', 0)} files processed")
                return True
            else:
                print(f"❌ Failed to load to Neo4j: {response.status_code}")
                print(f"   Error: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error loading to Neo4j: {e}")
            import traceback
            traceback.print_exc()
            return False

    # Main execution
    job_id, output_directory = None, None

    try:
        job_id, output_directory = run_extraction()

        if job_id and output_directory:
            # Try to load into Neo4j
            if load_to_neo4j(job_id, output_directory):
                print(f"\n🎯 You can now view the knowledge graph in Neo4j Browser!")
                print(f"   🌐 Open: http://localhost:7474")
                print(f"   🔍 Try query: MATCH (n) RETURN n LIMIT 50")
                print(f"   🔍 Or try: MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 25")
        else:
            print("⚠️ No extraction output to load into Neo4j")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

except ImportError as e:
    print(f"❌ Import failed: {e}")

print("\n🎉 Debug test completed!")
