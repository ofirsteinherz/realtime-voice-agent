"""
Redis Data Inspector - Debug tool to see actual data structure
"""

import redis
import json
from typing import Dict, Any


def connect_redis():
    """Connect to Redis server"""
    try:
        r = redis.Redis(
            host='redis',
            port=6379,
            decode_responses=True
        )
        r.ping()
        print("✓ Successfully connected to Redis\n")
        return r
    except redis.ConnectionError:
        print("✗ Failed to connect to Redis")
        return None


def inspect_conversations(r):
    """Inspect conversation data structure"""
    print("="*70)
    print("🔍 INSPECTING CONVERSATIONS")
    print("="*70)
    
    conv_keys = r.keys('conversation:*')
    print(f"Found {len(conv_keys)} conversation keys\n")
    
    for i, key in enumerate(conv_keys[:3], 1):
        print(f"\n--- Conversation {i}: {key} ---")
        conv_data = r.hgetall(key)
        
        print(f"Fields: {list(conv_data.keys())}")
        print(f"Session ID: {conv_data.get('session_id', 'N/A')}")
        print(f"Customer ID: {conv_data.get('customer_id', 'N/A')}")
        print(f"Timestamp: {conv_data.get('timestamp', 'N/A')}")
        
        if 'conversation_history' in conv_data:
            history = json.loads(conv_data['conversation_history'])
            print(f"Message count: {len(history)}")
            print(f"\nMessages:")
            for j, msg in enumerate(history, 1):
                print(f"  {j}. Role: {msg.get('role')}")
                if 'content' in msg:
                    content_preview = str(msg['content'])[:60]
                    print(f"     Content: {content_preview}...")
                if 'tool_calls' in msg:
                    print(f"     Tool calls: {msg['tool_calls']}")
                if 'name' in msg:  # Tool response
                    print(f"     Tool name: {msg['name']}")


def inspect_moderation(r):
    """Inspect moderation data structure"""
    print("\n" + "="*70)
    print("🔍 INSPECTING MODERATION DATA")
    print("="*70)
    
    # Check counter
    mod_count = r.get('moderation:count')
    print(f"Moderation count key: {mod_count}")
    
    mod_keys = r.keys('moderation:*')
    session_keys = [k for k in mod_keys if k != 'moderation:count']
    print(f"Found {len(session_keys)} moderation session keys\n")
    
    for i, key in enumerate(session_keys[:2], 1):
        print(f"\n--- Moderation Session {i}: {key} ---")
        # Get list items
        items = r.lrange(key, 0, -1)
        print(f"Number of moderation attempts: {len(items)}")
        
        for j, item in enumerate(items[:2], 1):
            try:
                data = json.loads(item)
                print(f"\n  Attempt {j}:")
                print(f"    Timestamp: {data.get('timestamp')}")
                print(f"    Flagged: {data.get('flagged')}")
                print(f"    Message: {data.get('message', '')[:50]}...")
                if 'openai' in data:
                    print(f"    OpenAI flagged: {data['openai'].get('flagged')}")
                if 'llama' in data:
                    print(f"    Llama detected: {data['llama'].get('detected_attack')}")
            except json.JSONDecodeError as e:
                print(f"  Error parsing item: {e}")


def inspect_test_results(r):
    """Inspect test results data structure"""
    print("\n" + "="*70)
    print("🔍 INSPECTING TEST RESULTS")
    print("="*70)
    
    test_count = r.get('test_results:count')
    print(f"Test results count: {test_count}")
    
    test_keys = r.keys('test_result:*')
    print(f"Found {len(test_keys)} test result keys\n")
    
    for i, key in enumerate(test_keys[:3], 1):
        print(f"\n--- Test Result {i}: {key} ---")
        test_data = r.hgetall(key)
        
        print(f"Fields: {list(test_data.keys())}")
        for field, value in test_data.items():
            print(f"  {field}: {value}")


def inspect_reviews(r):
    """Inspect review data structure"""
    print("\n" + "="*70)
    print("🔍 INSPECTING REVIEWS")
    print("="*70)
    
    review_keys = r.keys('review:*')
    print(f"Found {len(review_keys)} review keys\n")
    
    for i, key in enumerate(review_keys[:2], 1):
        print(f"\n--- Review {i}: {key} ---")
        review_data = r.hgetall(key)
        
        print(f"Fields: {list(review_data.keys())}")
        for field, value in review_data.items():
            if field == 'review_text':
                print(f"  {field}: {value[:100]}...")
            else:
                print(f"  {field}: {value}")


def inspect_all_keys(r):
    """Show all keys by pattern"""
    print("\n" + "="*70)
    print("🔍 ALL REDIS KEYS BY PATTERN")
    print("="*70)
    
    patterns = [
        'customer:*',
        'medicine:*',
        'inventory:*',
        'prescription:*',
        'conversation:*',
        'review:*',
        'moderation:*',
        'test_result:*'
    ]
    
    for pattern in patterns:
        keys = r.keys(pattern)
        print(f"\n{pattern}: {len(keys)} keys")
        if keys:
            print(f"  Examples: {keys[:3]}")


def main():
    """Main function"""
    print("\n" + "🔍"*35)
    print("REDIS DATA STRUCTURE INSPECTOR")
    print("🔍"*35 + "\n")
    
    r = connect_redis()
    if not r:
        return
    
    # Inspect all data structures
    inspect_all_keys(r)
    inspect_conversations(r)
    inspect_moderation(r)
    inspect_test_results(r)
    inspect_reviews(r)
    
    print("\n" + "="*70)
    print("✅ Inspection completed!")
    print("="*70)


if __name__ == "__main__":
    main()