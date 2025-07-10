"""
Quick validation script for end-to-end audio processing pipeline.
Use this before running the comprehensive test to check if all components are ready.
"""

import asyncio
import os
from pathlib import Path

try:
    import httpx
except ImportError:
    httpx = None
    
from dotenv import load_dotenv

# Load test environment
load_dotenv(".env.test")

async def quick_validation():
    """Run quick validation checks."""
    print("🔍 Quick Pipeline Validation")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 6
    
    # 1. Check API server
    print("\n1. API Server...")
    if not httpx:
        print("   ❌ httpx package not available")
        print("   💡 Run: uv sync")
    else:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get("http://localhost:8000/health")
                if response.status_code == 200:
                    print("   ✅ API server is running")
                    checks_passed += 1
                else:
                    print(f"   ❌ API server returned {response.status_code}")
        except Exception as e:
            print(f"   ❌ Cannot connect to API server: {e}")
            print("   💡 Make sure to run: uv run python app/main.py")
    
    # 2. Check OpenRouter API key
    print("\n2. OpenRouter Configuration...")
    api_key = os.getenv("OPENROUTER_API_KEY")
    if api_key and len(api_key) > 20 and api_key.startswith("sk-or-v1-"):
        print("   ✅ OpenRouter API key configured")
        checks_passed += 1
    else:
        print("   ❌ OpenRouter API key not properly configured")
        print("   💡 Set OPENROUTER_API_KEY in .env.test")
    
    # 3. Check Neo4j connection
    print("\n3. Neo4j Database...")
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
                print("   ✅ Neo4j connection successful")
                checks_passed += 1
            else:
                print("   ❌ Neo4j connection test failed")
        driver.close()
    except Exception as e:
        print(f"   ❌ Neo4j connection failed: {e}")
        print("   💡 Make sure Neo4j is running on bolt://localhost:7687")
    
    # 4. Check test audio files
    print("\n4. Test Audio Files...")
    audio_dir = Path("tests/data/audio")
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*"))
        valid_files = [f for f in audio_files if f.suffix.lower() in ['.wav', '.mp3', '.flac']]
        if valid_files:
            print(f"   ✅ Found {len(valid_files)} audio files:")
            for file in valid_files:
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"      - {file.name} ({size_mb:.2f} MB)")
            checks_passed += 1
        else:
            print("   ❌ No valid audio files found")
    else:
        print(f"   ❌ Audio directory not found: {audio_dir}")
    
    # 5. Check required Python packages
    print("\n5. Python Dependencies...")
    try:
        import neo4j, dotenv
        if httpx:
            print("   ✅ Required packages available")
            checks_passed += 1
        else:
            print("   ❌ httpx package missing")
            print("   💡 Run: uv sync")
    except ImportError as e:
        print(f"   ❌ Missing package: {e}")
        print("   💡 Run: uv sync")
    
    # 6. Check environment configuration
    print("\n6. Environment Configuration...")
    required_vars = [
        "GRAPH_LLM_PROVIDER",
        "GRAPH_LLM_MODEL",
        "GRAPH_ENTITY_EXTRACTION_METHOD",
        "GRAPH_TOPIC_EXTRACTION_METHOD"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if not missing_vars:
        print("   ✅ Environment variables configured")
        checks_passed += 1
    else:
        print(f"   ❌ Missing environment variables: {missing_vars}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Validation Summary: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("🎉 All checks passed! Ready to run comprehensive test.")
        print("\n🚀 Run the full test with:")
        print("   uv run python test_e2e_real_audio.py")
        return True
    else:
        print("⚠️  Some issues need to be resolved before testing.")
        print("\n🔧 Fix the issues above, then run:")
        print("   uv run python test_e2e_quick_check.py")
        return False

if __name__ == "__main__":
    import sys
    result = asyncio.run(quick_validation())
    sys.exit(0 if result else 1)
