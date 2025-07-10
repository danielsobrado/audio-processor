"""
End-to-end test of the complete audio processing pipeline.
Tests the full flow: audio upload → transcription → diarization → graph processing → Neo4j storage.
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

import httpx
import pytest
from dotenv import load_dotenv

# Load test environment
load_dotenv(".env.test")

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test-user-123"
TIMEOUT = 60  # seconds


class AudioProcessingE2ETest:
    """End-to-end test for the audio processing pipeline."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.test_file_path = None
        self.request_id = None
        
    async def setup(self):
        """Set up test environment and generate test audio."""
        print("Setting up end-to-end test...")
        
        # Generate test audio file
        print("Generating test audio file...")
        from test_audio_sample import generate_test_audio
        
        self.test_file_path = Path("test_e2e_audio.wav")
        generate_test_audio(str(self.test_file_path), duration=10.0)
        
        if not self.test_file_path.exists():
            raise FileNotFoundError(f"Failed to create test audio file: {self.test_file_path}")
            
        print(f"Test audio file created: {self.test_file_path}")
        
    async def cleanup(self):
        """Clean up test resources."""
        print("\nCleaning up test resources...")
        
        await self.client.aclose()
        
        # Remove test audio file
        if self.test_file_path and self.test_file_path.exists():
            self.test_file_path.unlink()
            print(f"Removed test audio file: {self.test_file_path}")
            
    async def test_api_health(self):
        """Test that the API server is running and responsive."""
        print("\n1. Testing API health...")
        
        try:
            response = await self.client.get(f"{API_BASE_URL}/health")
            if response.status_code == 200:
                print("✓ API server is healthy")
                return True
            else:
                print(f"✗ API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ Failed to connect to API server: {e}")
            return False
            
    async def test_audio_upload_and_transcription(self):
        """Test audio file upload and transcription request."""
        print("\n2. Testing audio upload and transcription...")
        
        if not self.test_file_path:
            print("✗ Test file path not set")
            return False
            
        try:
            # Prepare the audio file for upload
            with open(self.test_file_path, "rb") as audio_file:
                files = {"file": ("test_audio.wav", audio_file, "audio/wav")}
                
                # Test parameters
                data = {
                    "language": "auto",
                    "model": "tiny",  # Use fastest model for testing
                    "diarize": True,
                    "punctuate": True,
                    "smart_format": True,
                    "utterances": True,
                    "summarize": False,
                    "translate": False,
                }
                
                # Add mock auth header
                headers = {"X-User-ID": TEST_USER_ID}
                
                # Submit transcription request
                response = await self.client.post(
                    f"{API_BASE_URL}/api/v1/transcribe",
                    files=files,
                    data=data,
                    headers=headers
                )
                
            if response.status_code == 201:
                result = response.json()
                self.request_id = result.get("request_id")
                print(f"✓ Transcription request submitted successfully")
                print(f"  Request ID: {self.request_id}")
                print(f"  Status: {result.get('status')}")
                return True
            else:
                print(f"✗ Transcription request failed: {response.status_code}")
                print(f"  Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Error during audio upload: {e}")
            return False
            
    async def test_job_status_polling(self):
        """Poll job status until completion or timeout."""
        print("\n3. Polling job status...")
        
        if not self.request_id:
            print("✗ No request ID available for status polling")
            return False
            
        max_wait = 300  # 5 minutes max wait
        poll_interval = 5  # Poll every 5 seconds
        start_time = time.time()
        
        headers = {"X-User-ID": TEST_USER_ID}
        
        while time.time() - start_time < max_wait:
            try:
                response = await self.client.get(
                    f"{API_BASE_URL}/api/v1/jobs/{self.request_id}",
                    headers=headers
                )
                
                if response.status_code == 200:
                    job_info = response.json()
                    status = job_info.get("status")
                    progress = job_info.get("progress", 0)
                    
                    print(f"  Job status: {status}, Progress: {progress:.1f}%")
                    
                    if status == "completed":
                        print("✓ Job completed successfully")
                        return job_info
                    elif status == "failed":
                        error = job_info.get("error", "Unknown error")
                        print(f"✗ Job failed: {error}")
                        return False
                    elif status in ["queued", "processing"]:
                        # Continue polling
                        await asyncio.sleep(poll_interval)
                        continue
                    else:
                        print(f"✗ Unexpected job status: {status}")
                        return False
                else:
                    print(f"✗ Failed to get job status: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"✗ Error polling job status: {e}")
                await asyncio.sleep(poll_interval)
                
        print(f"✗ Job did not complete within {max_wait} seconds")
        return False
        
    async def test_transcription_results(self, job_info: Dict[str, Any]):
        """Verify transcription results."""
        print("\n4. Verifying transcription results...")
        
        try:
            result = job_info.get("result", {})
            
            # Check for required fields in Deepgram-compatible format
            required_fields = ["metadata", "results"]
            for field in required_fields:
                if field not in result:
                    print(f"✗ Missing required field: {field}")
                    return False
                    
            # Check metadata
            metadata = result.get("metadata", {})
            print(f"  Model used: {metadata.get('model_info', {}).get('name', 'Unknown')}")
            print(f"  Duration: {metadata.get('duration', 'Unknown')} seconds")
            
            # Check results
            results = result.get("results", {})
            channels = results.get("channels", [])
            
            if not channels:
                print("✗ No transcription channels found")
                return False
                
            # Check first channel
            channel = channels[0]
            alternatives = channel.get("alternatives", [])
            
            if not alternatives:
                print("✗ No transcription alternatives found")
                return False
                
            # Get transcript
            transcript = alternatives[0].get("transcript", "")
            print(f"  Transcript preview: {transcript[:100]}...")
            
            # Check for utterances/segments
            utterances = results.get("utterances", [])
            print(f"  Number of utterances: {len(utterances)}")
            
            if utterances:
                print(f"  First utterance: {utterances[0].get('transcript', '')[:50]}...")
                
            print("✓ Transcription results look valid")
            return True
            
        except Exception as e:
            print(f"✗ Error verifying transcription results: {e}")
            return False
            
    async def test_neo4j_graph_results(self):
        """Check if graph processing results were stored in Neo4j."""
        print("\n5. Checking Neo4j graph results...")
        
        try:
            # Import Neo4j driver for direct database check
            from neo4j import GraphDatabase
            
            # Get Neo4j connection details from environment
            uri = os.getenv("GRAPH_DATABASE_URL", "bolt://localhost:7687")
            username = os.getenv("GRAPH_DATABASE_USERNAME", "neo4j")
            password = os.getenv("GRAPH_DATABASE_PASSWORD", "password")
            
            # Connect to Neo4j
            driver = GraphDatabase.driver(uri, auth=(username, password))
            
            with driver.session() as session:
                # Query for nodes created from our test
                query = """
                MATCH (n) 
                WHERE n.created_at > datetime() - duration('PT10M')
                RETURN labels(n) as labels, count(n) as count
                """
                
                result = session.run(query)
                records = list(result)
                
                if records:
                    print("✓ Found recent nodes in Neo4j:")
                    total_nodes = 0
                    for record in records:
                        labels = record["labels"]
                        count = record["count"]
                        total_nodes += count
                        print(f"  {labels}: {count} nodes")
                    
                    print(f"  Total recent nodes: {total_nodes}")
                    
                    # Query for relationships
                    rel_query = """
                    MATCH ()-[r]->() 
                    WHERE r.created_at > datetime() - duration('PT10M')
                    RETURN type(r) as relationship_type, count(r) as count
                    """
                    
                    rel_result = session.run(rel_query)
                    rel_records = list(rel_result)
                    
                    if rel_records:
                        print("✓ Found recent relationships in Neo4j:")
                        total_rels = 0
                        for record in rel_records:
                            rel_type = record["relationship_type"]
                            count = record["count"]
                            total_rels += count
                            print(f"  {rel_type}: {count} relationships")
                        
                        print(f"  Total recent relationships: {total_rels}")
                    
                    return True
                else:
                    print("⚠ No recent nodes found in Neo4j")
                    print("  This could mean graph processing is disabled or failed")
                    return False
                    
        except Exception as e:
            print(f"⚠ Could not check Neo4j results: {e}")
            print("  This might be expected if Neo4j is not available or graph processing is disabled")
            return False
            
    async def run_full_test(self):
        """Run the complete end-to-end test suite."""
        print("=" * 60)
        print("AUDIO PROCESSING END-TO-END TEST")
        print("=" * 60)
        
        try:
            await self.setup()
            
            # Test sequence
            tests = [
                ("API Health Check", self.test_api_health()),
                ("Audio Upload & Transcription", self.test_audio_upload_and_transcription()),
            ]
            
            # Run initial tests
            for test_name, test_coro in tests:
                result = await test_coro
                if not result:
                    print(f"\n❌ FAILED: {test_name}")
                    return False
                    
            # Job polling test
            job_info = await self.test_job_status_polling()
            if not job_info:
                print(f"\n❌ FAILED: Job Status Polling")
                return False
                
            # Results verification
            result_tests = [
                ("Transcription Results", self.test_transcription_results(job_info)),
                ("Neo4j Graph Results", self.test_neo4j_graph_results()),
            ]
            
            results = []
            for test_name, test_coro in result_tests:
                result = await test_coro
                results.append((test_name, result))
                
            # Final summary
            print("\n" + "=" * 60)
            print("TEST SUMMARY")
            print("=" * 60)
            
            all_passed = True
            for test_name, result in [("API Health Check", True), ("Audio Upload & Transcription", True), ("Job Status Polling", True)] + results:
                status = "✓ PASS" if result else "✗ FAIL"
                print(f"{test_name:<30} {status}")
                if not result:
                    all_passed = False
                    
            print("\n" + "=" * 60)
            if all_passed:
                print("🎉 ALL TESTS PASSED - End-to-end pipeline is working!")
            else:
                print("⚠️  SOME TESTS FAILED - Check the details above")
            print("=" * 60)
            
            return all_passed
            
        except Exception as e:
            print(f"\n❌ CRITICAL ERROR: {e}")
            return False
        finally:
            await self.cleanup()


async def main():
    """Run the end-to-end test."""
    test = AudioProcessingE2ETest()
    success = await test.run_full_test()
    
    if success:
        print("\n🚀 Ready for production! The complete audio processing pipeline is working.")
    else:
        print("\n🔧 Some issues need to be addressed before production deployment.")
        
    return success


if __name__ == "__main__":
    import sys
    
    # Check dependencies
    try:
        import numpy
        import wave
    except ImportError as e:
        print(f"Missing required dependency: {e}")
        print("Install with: pip install numpy")
        sys.exit(1)
        
    # Run the test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
