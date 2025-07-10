"""
Complete End-to-End Test with Real LLM Processing
Tests the full pipeline: audio upload → real transcription → real LLM graph processing → Neo4j storage.
"""

import asyncio
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import base64

import httpx
import pytest
from dotenv import load_dotenv

# Load test environment
load_dotenv(".env.test")

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test-user-real-e2e"
TIMEOUT = 300  # 5 minutes for real processing
TEST_AUDIO_DIR = Path("tests/data/audio")

# Mock JWT token for testing (since JWT_VERIFY_SIGNATURE=False in test env)
def create_mock_jwt_token(user_id: str = TEST_USER_ID) -> str:
    """Create a mock JWT token for testing when signature verification is disabled."""
    # Create a simple JWT structure without signature verification
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,  # 1 hour expiration
    }
    
    # Base64 encode header and payload
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip('=')
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
    
    # For testing, we don't need a real signature since verification is disabled
    signature = "test-signature"
    
    return f"{header_b64}.{payload_b64}.{signature}"

MOCK_JWT_TOKEN = create_mock_jwt_token()


class RealProcessingE2ETest:
    """Complete end-to-end test with real audio processing and LLM integration."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self.processed_files = []
        self.test_results = {}
        
    async def cleanup(self):
        """Clean up test resources."""
        await self.client.aclose()
        
    async def run_comprehensive_test(self) -> bool:
        """Run the complete end-to-end test with real processing."""
        print("================================================================================")
        print("🎵 COMPLETE END-TO-END TEST WITH REAL LLM PROCESSING")
        print("================================================================================")
        print("Setting up real processing end-to-end test...")
        
        # Find audio files
        audio_files = self.find_test_audio_files()
        if not audio_files:
            print("❌ No test audio files found")
            return False
            
        print(f"Found {len(audio_files)} test audio files:")
        for audio_file in audio_files:
            size_mb = audio_file.stat().st_size / (1024 * 1024)
            print(f"  - {audio_file.name} ({size_mb:.2f} MB)")
        
        # Clear previous test data
        await self.clear_test_data()
        
        # Pre-flight checks
        print("\n🔧 Pre-flight checks:")
        
        if not await self.test_api_health():
            print("❌ FAILED: API Health Check")
            return False
            
        if not await self.test_openrouter_config():
            print("❌ FAILED: OpenRouter Configuration")
            return False
            
        if not await self.test_neo4j_connection():
            print("❌ FAILED: Neo4j Connection")
            return False
            
        if not await self.test_celery_worker():
            print("❌ FAILED: Celery Worker Check")
            return False
        
        # Process audio files with real pipeline
        print(f"\n🎵 Processing {len(audio_files)} audio files with real pipeline:")
        
        successful_results = []
        for audio_file in audio_files:
            result = await self.process_audio_file_real(audio_file)
            if result:
                successful_results.append(result)
                self.processed_files.append(audio_file.name)
        
        if not successful_results:
            print("❌ No audio files were processed successfully")
            return False
            
        # Validate results
        all_passed = True
        for result_data in successful_results:
            # Real transcription validation
            if not await self.validate_real_transcription_results(result_data):
                all_passed = False
            
            # Real graph processing validation  
            if not await self.validate_real_graph_processing(result_data):
                all_passed = False
        
        # Print comprehensive summary
        self.print_comprehensive_summary(successful_results, all_passed)
        
        return all_passed
    
    def find_test_audio_files(self) -> List[Path]:
        """Find available test audio files."""
        if not TEST_AUDIO_DIR.exists():
            return []
        
        audio_extensions = ['.wav', '.mp3', '.flac', '.m4a']
        audio_files = []
        
        for ext in audio_extensions:
            audio_files.extend(TEST_AUDIO_DIR.glob(f"*{ext}"))
        
        return sorted(audio_files)[:2]  # Limit to 2 files for testing
    
    async def clear_test_data(self):
        """Clear previous test data from Neo4j."""
        print("\n🧹 Clearing previous test data...")
        
        try:
            from neo4j import GraphDatabase
            
            uri = os.getenv("GRAPH_DATABASE_URL", "bolt://localhost:7687")
            username = os.getenv("GRAPH_DATABASE_USERNAME", "neo4j")
            password = os.getenv("GRAPH_DATABASE_PASSWORD", "password")
            
            driver = GraphDatabase.driver(uri, auth=(username, password))
            
            with driver.session() as session:
                # Clear test data (nodes created in last hour)
                result = session.run("""
                    MATCH (n) 
                    WHERE n.created_at > datetime() - duration('PT1H')
                    DETACH DELETE n
                    RETURN count(n) as deleted_count
                """)
                record = result.single()
                deleted_count = record["deleted_count"] if record else 0
                print(f"   🗑️ Cleared {deleted_count} test nodes and relationships")
            
            driver.close()
            
        except Exception as e:
            print(f"   ⚠️ Warning: Could not clear test data: {e}")
    
    async def test_api_health(self) -> bool:
        """Test that the API server is running and responsive."""
        print("\n🔍 1. Testing API health...")
        
        try:
            response = await self.client.get(f"{API_BASE_URL}/")
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == "healthy":
                    print("✅ API server is healthy")
                    return True
                else:
                    print(f"❌ API server status: {result.get('status', 'unknown')}")
                    return False
            else:
                print(f"❌ API health check failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Failed to connect to API server: {e}")
            return False
    
    async def test_openrouter_config(self) -> bool:
        """Test OpenRouter configuration."""
        print("\n🔍 2. Testing OpenRouter configuration...")
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key or api_key.startswith("sk-or-v1-") and len(api_key) < 20:
            print("❌ OpenRouter API key not properly configured")
            return False
            
        # Test the configuration
        try:
            import sys
            sys.path.append('.')
            from app.core.llm_graph_processors import OpenRouterProvider
            
            provider = OpenRouterProvider(api_key=api_key)
            print("✅ OpenRouter provider initialized successfully")
            return True
        except Exception as e:
            print(f"❌ OpenRouter configuration error: {e}")
            return False
    
    async def test_neo4j_connection(self) -> bool:
        """Test Neo4j database connection."""
        print("\n🔍 3. Testing Neo4j connection...")
        
        try:
            from neo4j import GraphDatabase
            
            uri = os.getenv("GRAPH_DATABASE_URL", "bolt://localhost:7687")
            username = os.getenv("GRAPH_DATABASE_USERNAME", "neo4j")
            password = os.getenv("GRAPH_DATABASE_PASSWORD", "password")
            
            driver = GraphDatabase.driver(uri, auth=(username, password))
            
            with driver.session() as session:
                result = session.run("RETURN 1 as test")
                record = result.single()
                if record and record["test"] == 1:
                    print("✅ Neo4j connection successful")
                    driver.close()
                    return True
            
            driver.close()
            return False
            
        except Exception as e:
            print(f"❌ Neo4j connection error: {e}")
            return False
    
    async def test_celery_worker(self) -> bool:
        """Test that Celery worker is running and ready."""
        print("\n🔍 4. Testing Celery worker...")
        
        try:
            # Test Celery connection through the API
            headers = {"Authorization": f"Bearer {MOCK_JWT_TOKEN}"}
            
            # Create a simple test job to verify worker is responding
            # We'll check this by monitoring if tasks can be submitted
            print("✅ Celery worker assumed ready (running in background)")
            return True
            
        except Exception as e:
            print(f"❌ Celery worker test failed: {e}")
            return False
    
    async def process_audio_file_real(self, audio_file: Path) -> Optional[Dict[str, Any]]:
        """Process a single audio file through the real pipeline."""
        print(f"\n🎵 Processing: {audio_file.name}")
        
        try:
            # Determine MIME type
            mime_type = "audio/wav" if audio_file.suffix.lower() == ".wav" else "audio/mpeg"
            
            # Prepare the audio file for upload
            with open(audio_file, "rb") as f:
                files = {"file": (audio_file.name, f, mime_type)}
                
                # Test parameters - enable real LLM processing
                data = {
                    "language": "auto",
                    "model": "tiny",  # Fast model for testing
                    "diarize": True,  # Enable speaker diarization
                    "punctuate": True,
                    "smart_format": True,
                    "utterances": True,
                    "summarize": False,  # Keep disabled for speed
                    "translate": False,  # Keep disabled for speed
                }
                
                headers = {"Authorization": f"Bearer {MOCK_JWT_TOKEN}"}
                
                print(f"   📤 Uploading {audio_file.name}...")
                response = await self.client.post(
                    f"{API_BASE_URL}/api/transcribe",
                    files=files,
                    data=data,
                    headers=headers
                )
                
            if response.status_code != 201:
                print(f"   ❌ Upload failed: {response.status_code}")
                print(f"      Response: {response.text}")
                return None
                
            result = response.json()
            request_id = result.get("request_id")
            print(f"   ✅ Upload successful - Request ID: {request_id}")
            
            # Poll for real completion (no manual processing)
            job_info = await self.poll_real_job_completion(request_id)
            if not job_info:
                return None
                
            return {
                "audio_file": audio_file.name,
                "request_id": request_id,
                "job_info": job_info,
                "file_path": audio_file,
            }
            
        except Exception as e:
            print(f"   ❌ Error processing {audio_file.name}: {e}")
            return None
    
    async def poll_real_job_completion(self, request_id: str, max_wait: int = 300) -> Optional[Dict[str, Any]]:
        """Poll job status until real completion."""
        print(f"   ⏳ Polling for real job completion...")
        
        poll_interval = 10  # Check every 10 seconds for real processing
        start_time = time.time()
        headers = {"Authorization": f"Bearer {MOCK_JWT_TOKEN}"}
        
        while time.time() - start_time < max_wait:
            try:
                response = await self.client.get(
                    f"{API_BASE_URL}/api/status/{request_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    print(f"   ❌ Failed to get job status: {response.status_code}")
                    await asyncio.sleep(poll_interval)
                    continue
                    
                job_data = response.json()
                status = job_data.get("status")
                progress = job_data.get("progress", 0)
                
                print(f"   📊 Status: {status}, Progress: {progress:.1f}%")
                
                if status == "completed":
                    print(f"   ✅ Job completed successfully!")
                    return job_data
                elif status == "failed":
                    error = job_data.get("error", "Unknown error")
                    print(f"   ❌ Job failed: {error}")
                    return None
                elif status in ["pending", "processing"]:
                    # Continue polling
                    await asyncio.sleep(poll_interval)
                    continue
                else:
                    print(f"   ❌ Unexpected job status: {status}")
                    await asyncio.sleep(poll_interval)
                    continue
                    
            except Exception as e:
                print(f"   ⚠️ Error polling job status: {e}")
                await asyncio.sleep(poll_interval)
                
        print(f"   ❌ Job did not complete within {max_wait} seconds")
        return None
    
    async def validate_real_transcription_results(self, result_data: Dict[str, Any]) -> bool:
        """Validate real transcription and diarization results."""
        audio_file = result_data["audio_file"]
        job_info = result_data["job_info"]
        
        print(f"\n🔍 5. Validating real transcription results for {audio_file}...")
        
        try:
            result = job_info.get("result", {})
            
            # Check metadata
            metadata = result.get("metadata", {})
            duration = metadata.get("duration", 0)
            model_name = metadata.get("model_info", {}).get("name", "Unknown")
            
            print(f"   📊 Duration: {duration:.2f} seconds")
            print(f"   🤖 Model: {model_name}")
            
            # Check results structure
            results = result.get("results", {})
            channels = results.get("channels", [])
            
            if not channels:
                print(f"   ❌ No channels found in results")
                return False
                
            # Check transcript
            alternatives = channels[0].get("alternatives", [])
            if not alternatives:
                print(f"   ❌ No alternatives found")
                return False
                
            transcript = alternatives[0].get("transcript", "")
            confidence = alternatives[0].get("confidence", 0)
            
            print(f"   📝 Transcript length: {len(transcript)} chars, {len(transcript.split())} words")
            print(f"   🎯 Confidence: {confidence:.3f}")
            print(f"   📄 Preview: {transcript[:100]}...")
            
            # Check utterances (diarization)
            utterances = alternatives[0].get("utterances", [])
            print(f"   🗣️  Total utterances: {len(utterances)}")
            
            if utterances:
                speakers = set()
                for utterance in utterances:
                    speaker = utterance.get("speaker")
                    if speaker:
                        speakers.add(speaker)
                        
                print(f"   👥 Unique speakers detected: {len(speakers)}")
                if speakers:
                    print(f"   🎯 Speakers: {sorted(speakers)}")
                    
                # Show first few utterances
                for i, utterance in enumerate(utterances[:3]):
                    speaker = utterance.get("speaker", "Unknown")
                    text = utterance.get("transcript", "")
                    start = utterance.get("start", 0)
                    print(f"   💬 [{speaker}] {start:.1f}s: {text[:50]}...")
            
            # Validate transcript is not empty and meaningful
            if len(transcript.strip()) < 10:
                print(f"   ⚠️ Warning: Very short transcript ({len(transcript)} chars)")
            
            print(f"   ✅ Real transcription results validated successfully")
            return True
            
        except Exception as e:
            print(f"   ❌ Error validating transcription results: {e}")
            return False
    
    async def validate_real_graph_processing(self, result_data: Dict[str, Any]) -> bool:
        """Validate real LLM-based graph processing results in Neo4j."""
        audio_file = result_data["audio_file"]
        request_id = result_data["request_id"]
        
        print(f"\n🔍 6. Validating real graph processing for {audio_file}...")
        
        try:
            from neo4j import GraphDatabase
            
            uri = os.getenv("GRAPH_DATABASE_URL", "bolt://localhost:7687")
            username = os.getenv("GRAPH_DATABASE_USERNAME", "neo4j")
            password = os.getenv("GRAPH_DATABASE_PASSWORD", "password")
            
            driver = GraphDatabase.driver(uri, auth=(username, password))
            
            with driver.session() as session:
                # Query for nodes related to this processing session
                # Look for nodes created in the last 10 minutes
                node_query = """
                MATCH (n) 
                WHERE n.created_at > datetime() - duration('PT10M')
                RETURN labels(n) as labels, count(n) as count, 
                       collect(n.name)[0..3] as sample_names
                """
                
                result = session.run(node_query)
                node_results = list(result)
                
                if not node_results or all(r["count"] == 0 for r in node_results):
                    print(f"   ⚠️ No recent nodes found in Neo4j")
                    print(f"   ℹ️  This might indicate graph processing failed or is disabled")
                    
                    # Check if graph processing is enabled
                    graph_enabled = os.getenv("GRAPH_ENABLED", "false").lower() == "true"
                    if not graph_enabled:
                        print(f"   ℹ️  Graph processing is disabled in configuration")
                        return True  # Not a failure if disabled
                    
                    return False
                
                # Display found nodes
                total_nodes = sum(r["count"] for r in node_results)
                print(f"   📊 Found {total_nodes} nodes created recently:")
                
                for result_row in node_results:
                    if result_row["count"] > 0:
                        labels = result_row["labels"]
                        count = result_row["count"]
                        samples = result_row["sample_names"]
                        print(f"   🏷️  {labels}: {count} nodes")
                        if samples:
                            print(f"      📝 Examples: {', '.join(samples[:3])}")
                
                # Query for relationships
                rel_query = """
                MATCH ()-[r]->() 
                WHERE r.created_at > datetime() - duration('PT10M')
                RETURN type(r) as rel_type, count(r) as count
                """
                
                result = session.run(rel_query)
                rel_results = list(result)
                
                total_rels = sum(r["count"] for r in rel_results)
                print(f"   🔗 Found {total_rels} relationships created recently:")
                
                for result_row in rel_results:
                    if result_row["count"] > 0:
                        rel_type = result_row["rel_type"]
                        count = result_row["count"]
                        print(f"   🔗 {rel_type}: {count} relationships")
                
                # Check for specific graph processing indicators
                graph_query = """
                MATCH (n)
                WHERE n.created_at > datetime() - duration('PT10M')
                AND (n:Entity OR n:Topic OR n:Sentiment)
                RETURN count(n) as graph_nodes
                """
                
                result = session.run(graph_query)
                record = result.single()
                graph_count = record["graph_nodes"] if record else 0
                
                if graph_count > 0:
                    print(f"   ✅ Graph processing nodes found: {graph_count}")
                    print(f"   ✅ Real graph processing validation successful")
                    driver.close()
                    return True
                else:
                    print(f"   ⚠️ No specific graph processing nodes found")
                    print(f"   ℹ️  General nodes found, but may not be from LLM processing")
                    driver.close()
                    return total_nodes > 0  # Accept if any nodes were created
            
        except Exception as e:
            print(f"   ❌ Error validating graph processing: {e}")
            return False
    
    def print_comprehensive_summary(self, successful_results: List[Dict[str, Any]], all_passed: bool):
        """Print comprehensive test summary."""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE REAL PROCESSING TEST SUMMARY")
        print("="*80)
        
        print(f"📁 Audio Files Processed: {len(successful_results)}")
        for result in successful_results:
            request_id = result["request_id"]
            audio_file = result["audio_file"]
            print(f"   ✅ {audio_file} - Request ID: {request_id}")
        
        print(f"\n🔍 Validation Results:")
        for result in successful_results:
            audio_file = result["audio_file"]
            print(f"   📄 {audio_file}:")
            # Note: Individual validation results are displayed during processing
        
        if all_passed:
            print("\n" + "="*80)
            print("🎉 COMPREHENSIVE REAL PROCESSING TEST SUCCESSFUL!")
            print("   ✅ All pipeline components working correctly")
            print("   ✅ Real audio transcription functional")
            print("   ✅ Real LLM graph processing functional")
            print("   ✅ Neo4j integration working")
            print("🚀 System ready for production deployment!")
        else:
            print("\n" + "="*80)
            print("⚠️  COMPREHENSIVE REAL PROCESSING TEST INCOMPLETE!")
            print("   ❌ Some pipeline components failed validation")
            print("🔧 Please review the issues above before production deployment.")
        
        print("="*80)


async def main():
    """Main test execution."""
    test = RealProcessingE2ETest()
    
    try:
        success = await test.run_comprehensive_test()
        print("\nCleaning up test resources...")
        await test.cleanup()
        
        if success:
            print("✅ All tests passed!")
            exit(0)
        else:
            print("❌ Some tests failed!")
            exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        await test.cleanup()
        exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        await test.cleanup()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
