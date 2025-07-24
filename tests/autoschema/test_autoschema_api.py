#!/usr/bin/env python3
"""
Simple test to check AutoSchemaKG API endpoints
"""
import requests
import json
import time

def test_autoschema_api():
    """Test AutoSchemaKG API endpoints manually"""

    print("🧪 AutoSchemaKG API Test")
    print("=" * 50)

    base_url = "http://localhost:8000"

    # Test sample data
    sample_text = """
    John Smith works as a senior software engineer at Microsoft Corporation in Seattle.
    He has been developing applications using Python and JavaScript for over 8 years.
    John graduated from Stanford University with a degree in Computer Science in 2015.
    He is passionate about artificial intelligence and machine learning technologies.
    Microsoft is a leading technology company founded by Bill Gates and Paul Allen in 1975.
    The company is headquartered in Redmond, Washington, and employs over 200,000 people worldwide.
    """

    try:
        # 1. Test stats endpoint
        print("📊 Testing /api/v1/autoschema-kg/stats endpoint...")
        response = requests.get(f"{base_url}/api/v1/autoschema-kg/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Stats: {stats}")
        else:
            print(f"❌ Stats failed: {response.status_code} - {response.text}")
            return

        # 2. Test extraction endpoint
        print("\n🔍 Testing /api/v1/autoschema-kg/extract endpoint...")
        extract_request = {
            "text": sample_text,
            "job_id": "test_job_001",
            "config": {
                "model_name": "meta-llama/llama-3.2-3b-instruct",
                "max_tokens": 1024,
                "batch_size": 2
            }
        }

        response = requests.post(
            f"{base_url}/api/v1/autoschema-kg/extract",
            json=extract_request,
            timeout=300  # 5 minutes timeout
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Extraction successful!")
            print(f"   Entities: {result.get('entities_count', 0)}")
            print(f"   Relationships: {result.get('relationships_count', 0)}")
            print(f"   Concepts: {result.get('concepts_count', 0)}")
            print(f"   Output directory: {result.get('output_directory', 'N/A')}")

            # If extraction was successful, test Neo4j loading
            if result.get('output_directory'):
                print("\n🗃️ Testing Neo4j loading...")
                load_response = requests.post(
                    f"{base_url}/api/v1/autoschema-kg/load-to-neo4j/{extract_request['job_id']}",
                    params={"output_directory": result['output_directory']},
                    timeout=60
                )

                if load_response.status_code == 200:
                    load_result = load_response.json()
                    print(f"✅ Neo4j loading successful!")
                    print(f"   Nodes loaded: {load_result.get('nodes_loaded', 0)}")
                    print(f"   Relationships loaded: {load_result.get('relationships_loaded', 0)}")
                else:
                    print(f"❌ Neo4j loading failed: {load_response.status_code} - {load_response.text}")

        else:
            print(f"❌ Extraction failed: {response.status_code} - {response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server")
        print("💡 Make sure to start the server first:")
        print("   uv run uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Test error: {e}")

    print("\n🎉 API test completed!")

if __name__ == "__main__":
    test_autoschema_api()
