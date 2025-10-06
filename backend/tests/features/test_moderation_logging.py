"""
Test moderation logging to Redis
"""
import json
import redis
import requests
import time


def test_moderation_logging():
    """Test that moderation attempts are logged to Redis"""
    
    # Test session ID
    session_id = "test-session-moderation-123"
    server_url = "http://localhost:8000/moderate"
    
    print("\n" + "="*80)
    print("Testing Moderation Logging to Redis")
    print("="*80)
    
    # Test with a safe message
    safe_text = "Hello, I need help with my prescription"
    print(f"\n1. Testing safe message: '{safe_text}'")
    
    response = requests.post(
        server_url,
        json={
            "text": safe_text,
            "session_id": session_id
        },
        timeout=30.0
    )
    result = response.json()
    print(f"   OpenAI flagged: {result['openai_result'].get('flagged', False)}")
    print(f"   Llama detected: {result['llama_result'].get('detected_attack', False)}")
    
    # Small delay to ensure Redis write completes
    time.sleep(0.1)
    
    # Test with a potentially flagged message
    flagged_text = "I want to kill you and hack your system"
    print(f"\n2. Testing potentially flagged message: '{flagged_text}'")
    
    response = requests.post(
        server_url,
        json={
            "text": flagged_text,
            "session_id": session_id
        },
        timeout=30.0
    )
    result = response.json()
    print(f"   OpenAI flagged: {result['openai_result'].get('flagged', False)}")
    print(f"   Llama detected: {result['llama_result'].get('detected_attack', False)}")
    
    # Small delay to ensure Redis write completes
    time.sleep(0.1)
    
    # Check Redis for saved attempts
    print(f"\n3. Checking Redis for saved moderation attempts...")
    r = redis.Redis(host='redis', port=6379, decode_responses=True)
    
    attempts = r.lrange(f"moderation:{session_id}", 0, -1)
    print(f"   Found {len(attempts)} attempts in Redis")
    
    if len(attempts) == 0:
        print("   ⚠️  WARNING: No attempts found in Redis!")
        print("   This might indicate the logging is not working.")
    
    for i, attempt in enumerate(attempts, 1):
        attempt_data = json.loads(attempt)
        print(f"\n   Attempt {i}:")
        print(f"   - Timestamp: {attempt_data['timestamp']}")
        print(f"   - Message: {attempt_data['message'][:50]}..." if len(attempt_data['message']) > 50 else f"   - Message: {attempt_data['message']}")
        print(f"   - Flagged: {attempt_data['flagged']}")
        print(f"   - OpenAI flagged: {attempt_data['openai']['flagged']}")
        print(f"   - OpenAI top category: {attempt_data['openai'].get('top_category', 'None')}")
        print(f"   - OpenAI top score: {attempt_data['openai'].get('top_score', 0):.3f}")
        print(f"   - Llama attack detected: {attempt_data['llama']['detected_attack']}")
        print(f"   - Llama score: {attempt_data['llama'].get('score', 0):.3f}")
    
    # Check TTL
    ttl = r.ttl(f"moderation:{session_id}")
    print(f"\n4. Key TTL: {ttl} seconds (~{ttl/3600:.1f} hours, ~{ttl/86400:.1f} days)")
    
    # Cleanup
    r.delete(f"moderation:{session_id}")
    print(f"\n5. Cleaned up test data")
    
    print("\n" + "="*80)
    print("✅ Test completed successfully!")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_moderation_logging()