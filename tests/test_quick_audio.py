"""
Quick audio processing test to verify the end-to-end workflow.
"""
import asyncio
import base64
import json
import time
from pathlib import Path

import httpx

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_USER_ID = "test-user-quick"
TIMEOUT = 60
TEST_AUDIO_FILE = Path("tests/data/audio/arabic_sample.wav.mp3")


def create_mock_jwt_token(user_id: str = TEST_USER_ID) -> str:
    """Create a mock JWT token for testing when signature verification is disabled."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "preferred_username": "test-user",
        "email": "test@example.com",
        "realm_access": {"roles": ["user"]},
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "iss": "http://mock-keycloak:8080/realms/test",
    }

    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

    return f"{header_b64}.{payload_b64}.fake_signature"


async def test_quick_audio_processing():
    """Quick test of audio processing with a smaller file."""
    if not TEST_AUDIO_FILE.exists():
        print(f"❌ Test audio file not found: {TEST_AUDIO_FILE}")
        return False

    print(f"🎵 Testing with: {TEST_AUDIO_FILE.name} ({TEST_AUDIO_FILE.stat().st_size / 1024:.1f} KB)")

    mock_token = create_mock_jwt_token()
    headers = {"Authorization": f"Bearer {mock_token}"}

    try:
        async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=1800.0) as client:
            # Test upload
            with open(TEST_AUDIO_FILE, "rb") as f:
                files = {"file": (TEST_AUDIO_FILE.name, f, "audio/mpeg")}
                data = {
                    "language": "auto",
                    "model": "base",
                    "include_diarization": "false",
                    "include_summarization": "false",
                    "include_translation": "false",
                    "include_graph": "false",
                }

                print("🚀 Uploading audio file...")
                response = await client.post(
                    f"{API_BASE_URL}/api/v1/transcribe",
                    files=files,
                    data=data,
                    headers=headers,
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    print("✅ Upload successful!")
                    print(f"📄 Job ID: {result.get('job_id', 'N/A')}")
                    print(f"🔄 Status: {result.get('status', 'N/A')}")
                    if 'transcription' in result:
                        transcript = result['transcription']
                        print(f"📝 Transcription: {transcript[:100]}..." if len(transcript) > 100 else f"📝 Transcription: {transcript}")
                    return True
                else:
                    print(f"❌ Upload failed: {response.status_code}")
                    print(f"Response: {response.text}")
                    return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_quick_audio_processing())
    exit(0 if success else 1)
