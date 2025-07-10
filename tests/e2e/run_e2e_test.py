"""
Simple script to run the comprehensive end-to-end test with proper environment setup.
This ensures the .env.test file is loaded correctly.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load the test environment first
env_file = Path(".env.test")
if env_file.exists():
    load_dotenv(env_file, override=True)
    print(f"✅ Loaded environment from {env_file}")
    print(f"   WHISPERX_MODEL_SIZE: {os.getenv('WHISPERX_MODEL_SIZE')}")
    print(f"   DATABASE_URL: {os.getenv('DATABASE_URL')}")
    print(f"   GRAPH_DATABASE_PASSWORD: {os.getenv('GRAPH_DATABASE_PASSWORD')}")
else:
    print(f"❌ Environment file not found: {env_file}")
    sys.exit(1)

# Now import and run the test
from test_e2e_real_audio import main

if __name__ == "__main__":
    print("\n🚀 Starting comprehensive end-to-end test...")
    result = asyncio.run(main())
    
    if result:
        print("\n🎉 SUCCESS: End-to-end test completed successfully!")
    else:
        print("\n❌ FAILURE: End-to-end test failed!")
    
    sys.exit(0 if result else 1)
