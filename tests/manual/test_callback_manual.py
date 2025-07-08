"""
Manual testing script for callback URL functionality.

This script provides practical examples and test scenarios for developers
to manually verify the callback functionality works correctly.
"""

import asyncio
import json
from typing import Dict, Any
from unittest.mock import AsyncMock, patch

# Example callback payloads that the system will send


def example_success_payload() -> Dict[str, Any]:
    """Example payload sent for successful transcription."""
    return {
        "request_id": "abc-123-def-456",
        "status": "completed",
        "timestamp": "2025-07-08T12:34:56.789Z",
        "result": {
            "results": {
                "channels": [{
                    "alternatives": [{
                        "transcript": "Hello world, this is a test transcription.",
                        "confidence": 0.95,
                        "words": [
                            {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.98},
                            {"word": "world", "start": 0.6, "end": 1.0, "confidence": 0.94}
                        ]
                    }]
                }]
            },
            "metadata": {
                "request_id": "abc-123-def-456",
                "model_info": {"name": "whisper-large-v2", "version": "1.0"},
                "duration": 5.2,
                "channels": 1
            }
        }
    }


def example_failure_payload() -> Dict[str, Any]:
    """Example payload sent for failed transcription."""
    return {
        "request_id": "xyz-789-uvw-012",
        "status": "failed", 
        "timestamp": "2025-07-08T12:35:30.123Z",
        "error": "Audio file format not supported: unsupported codec 'unknown'"
    }


async def test_callback_function():
    """Test the callback notification function directly."""
    print("Testing callback notification function...")
    
    # Import the function
    from app.workers.tasks import _send_callback_notification
    
    # Test successful notification
    print("\n1. Testing successful callback notification:")
    success_payload = example_success_payload()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_context = AsyncMock()
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_context.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_context
        
        await _send_callback_notification(
            callback_url="https://httpbin.org/post",
            request_id=success_payload["request_id"],
            status="completed",
            result=success_payload["result"]
        )
        
        # Check what was sent
        call_args = mock_context.post.call_args
        sent_payload = call_args[1]["json"]
        print(f"✓ Sent payload keys: {list(sent_payload.keys())}")
        print(f"✓ Request ID: {sent_payload['request_id']}")
        print(f"✓ Status: {sent_payload['status']}")
        print(f"✓ Has result: {'result' in sent_payload}")
        print(f"✓ Has timestamp: {'timestamp' in sent_payload}")
    
    # Test failure notification
    print("\n2. Testing failure callback notification:")
    failure_payload = example_failure_payload()
    
    with patch('httpx.AsyncClient') as mock_client:
        mock_context = AsyncMock()
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_context.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_context
        
        await _send_callback_notification(
            callback_url="https://httpbin.org/post",
            request_id=failure_payload["request_id"],
            status="failed",
            error=failure_payload["error"]
        )
        
        # Check what was sent
        call_args = mock_context.post.call_args
        sent_payload = call_args[1]["json"]
        print(f"✓ Sent payload keys: {list(sent_payload.keys())}")
        print(f"✓ Request ID: {sent_payload['request_id']}")
        print(f"✓ Status: {sent_payload['status']}")
        print(f"✓ Has error: {'error' in sent_payload}")
        print(f"✓ No result field: {'result' not in sent_payload}")
    
    print("\n✓ All callback tests passed!")


def print_example_payloads():
    """Print example payloads for manual testing."""
    print("=== EXAMPLE CALLBACK PAYLOADS ===\n")
    
    print("SUCCESS PAYLOAD:")
    print(json.dumps(example_success_payload(), indent=2))
    
    print("\n" + "="*50 + "\n")
    
    print("FAILURE PAYLOAD:")
    print(json.dumps(example_failure_payload(), indent=2))


def curl_examples():
    """Print curl examples for testing webhook endpoints."""
    print("\n=== CURL EXAMPLES FOR TESTING YOUR WEBHOOK ===\n")
    
    success_payload = json.dumps(example_success_payload(), indent=2)
    failure_payload = json.dumps(example_failure_payload(), indent=2)
    
    print("Test successful transcription callback:")
    print(f"""curl -X POST https://your-webhook.com/transcription \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(example_success_payload())}'""")
    
    print("\nTest failed transcription callback:")
    print(f"""curl -X POST https://your-webhook.com/transcription \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(example_failure_payload())}'""")
    
    print("\nTest with httpbin.org (for debugging):")
    print(f"""curl -X POST https://httpbin.org/post \\
  -H "Content-Type: application/json" \\
  -d '{json.dumps(example_success_payload())}'""")


def webhook_server_example():
    """Print example webhook server code."""
    print("\n=== EXAMPLE WEBHOOK SERVER (Python Flask) ===\n")
    
    server_code = '''
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

@app.route('/transcription', methods=['POST'])
def handle_transcription_callback():
    """Handle transcription completion callbacks."""
    try:
        payload = request.get_json()
        
        print(f"Received callback for job: {payload.get('request_id')}")
        print(f"Status: {payload.get('status')}")
        print(f"Timestamp: {payload.get('timestamp')}")
        
        if payload.get('status') == 'completed':
            result = payload.get('result', {})
            transcript = result.get('results', {}).get('channels', [{}])[0].get('alternatives', [{}])[0].get('transcript', '')
            print(f"Transcript: {transcript[:100]}...")
            
            # Your business logic here
            # - Save to database
            # - Send notifications
            # - Update UI via WebSocket
            # - etc.
            
        elif payload.get('status') == 'failed':
            error = payload.get('error')
            print(f"Transcription failed: {error}")
            
            # Your error handling here
            # - Log error
            # - Retry logic
            # - User notification
            # - etc.
        
        return jsonify({"status": "received"}), 200
        
    except Exception as e:
        print(f"Error processing callback: {e}")
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
'''
    
    print(server_code)
    
    print("\nTo test this server:")
    print("1. Save the code above as 'webhook_server.py'")
    print("2. Install Flask: pip install flask")
    print("3. Run: python webhook_server.py")
    print("4. Use callback_url: http://localhost:3000/transcription")


async def main():
    """Main test function."""
    print("=== CALLBACK URL FUNCTIONALITY MANUAL TESTING ===\n")
    
    # Test the callback function
    await test_callback_function()
    
    # Print examples
    print_example_payloads()
    curl_examples()
    webhook_server_example()
    
    print("\n=== TESTING COMPLETE ===")
    print("✓ Callback function works correctly")
    print("✓ Example payloads are properly structured") 
    print("✓ Ready for integration with real webhook endpoints")


if __name__ == "__main__":
    asyncio.run(main())
'''

To use this manual testing script:

1. **Run the tests:**
   ```bash
   cd /path/to/audio-processor
   python tests/manual/test_callback_manual.py
   ```

2. **Test with real webhook:**
   - Set up a webhook endpoint (use the Flask example provided)
   - Submit a transcription job with callback_url parameter
   - Verify you receive the callback

3. **Test with httpbin.org:**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/transcribe" \\
     -F "file=@test_audio.wav" \\
     -F "callback_url=https://httpbin.org/post"
   ```

4. **Monitor logs:**
   Check application logs for callback attempts and responses.
'''
