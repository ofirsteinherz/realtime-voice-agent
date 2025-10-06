"""
Test script to retrieve and display conversation history for a specific customer
"""

import redis
import json
import sys
from datetime import datetime


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
        print("Make sure Redis is running: docker-compose up -d redis")
        sys.exit(1)


def get_customer_conversations(r, customer_id):
    """Get all conversation sessions for a specific customer"""
    print("="*80)
    print(f"CONVERSATION HISTORY FOR CUSTOMER ID: {customer_id}")
    print("="*80)
    
    # Get all conversation keys
    conversation_keys = r.keys('conversation:*')
    
    if not conversation_keys:
        print("\nNo conversations found in database.")
        return
    
    # Filter by customer_id
    customer_conversations = []
    for key in conversation_keys:
        conversation = r.hgetall(key)
        if conversation.get('customer_id') == str(customer_id):
            customer_conversations.append({
                'key': key,
                'data': conversation
            })
    
    if not customer_conversations:
        print(f"\nNo conversations found for customer ID {customer_id}.")
        return
    
    print(f"\nTotal sessions found: {len(customer_conversations)}\n")
    
    # Display each conversation session
    for i, conv in enumerate(customer_conversations, 1):
        session_id = conv['data'].get('session_id', 'Unknown')
        timestamp = conv['data'].get('timestamp', 'Unknown')
        message_count = conv['data'].get('message_count', '0')
        conversation_history = conv['data'].get('conversation_history', '[]')
        
        print(f"\n{'─'*80}")
        print(f"SESSION {i}: {session_id}")
        print(f"{'─'*80}")
        print(f"Customer ID: {conv['data'].get('customer_id')}")
        print(f"Timestamp: {timestamp}")
        print(f"Message Count: {message_count}")
        print(f"\nConversation Messages:")
        print(f"{'─'*80}")
        
        # Parse and display messages
        try:
            messages = json.loads(conversation_history)
            if not messages:
                print("  (No messages in this session)")
            else:
                for msg_idx, msg in enumerate(messages, 1):
                    role = msg.get('role', 'unknown')
                    msg_type = msg.get('type', 'unknown')
                    content = msg.get('content', '')
                    msg_timestamp = msg.get('timestamp', '')
                    
                    # Format role emoji
                    role_emoji = {
                        'user': '👤',
                        'assistant': '🤖',
                        'function': '🔧'
                    }.get(role, '❓')
                    
                    print(f"\n  [{msg_idx}] {role_emoji} {role.upper()} ({msg_type})")
                    if msg_timestamp:
                        print(f"      Time: {msg_timestamp}")
                    
                    # Display content based on type
                    if msg_type == 'function_call':
                        func_name = msg.get('function_name', 'unknown')
                        arguments = msg.get('arguments', {})
                        print(f"      Function: {func_name}")
                        print(f"      Arguments: {json.dumps(arguments, ensure_ascii=False)}")
                    elif msg_type == 'function_result':
                        func_name = msg.get('function_name', 'unknown')
                        result = msg.get('result', '')
                        print(f"      Function: {func_name}")
                        print(f"      Result: {result}")
                    else:
                        # Text or audio transcript
                        if len(content) > 100:
                            print(f"      Content: {content[:100]}...")
                        else:
                            print(f"      Content: {content}")
                    
        except json.JSONDecodeError:
            print("  (Error parsing conversation history)")
        
        print(f"\n{'─'*80}")
    
    print(f"\n{'='*80}\n")


def get_all_customer_conversations_summary(r):
    """Get a summary of all conversations grouped by customer"""
    print("\n" + "="*80)
    print("ALL CUSTOMERS CONVERSATION SUMMARY")
    print("="*80)
    
    # Get all conversation keys
    conversation_keys = r.keys('conversation:*')
    
    if not conversation_keys:
        print("\nNo conversations found in database.")
        return
    
    # Group by customer_id
    customer_sessions = {}
    for key in conversation_keys:
        conversation = r.hgetall(key)
        customer_id = conversation.get('customer_id', 'unknown')
        
        if customer_id not in customer_sessions:
            customer_sessions[customer_id] = []
        
        customer_sessions[customer_id].append({
            'session_id': conversation.get('session_id'),
            'timestamp': conversation.get('timestamp'),
            'message_count': conversation.get('message_count', '0')
        })
    
    # Display summary
    print(f"\nTotal unique customers: {len(customer_sessions)}")
    print(f"Total conversations: {len(conversation_keys)}\n")
    
    for customer_id, sessions in sorted(customer_sessions.items()):
        total_messages = sum(int(s['message_count']) for s in sessions)
        print(f"  Customer ID {customer_id}:")
        print(f"    - Sessions: {len(sessions)}")
        print(f"    - Total messages: {total_messages}")
    
    print(f"\n{'='*80}\n")


def main():
    """Main function"""
    print("\n" + "="*80)
    print("Conversation History Test Script")
    print("="*80 + "\n")
    
    # Connect to Redis
    r = connect_redis()
    
    # Show summary of all conversations
    get_all_customer_conversations_summary(r)
    
    # Get detailed history for customer ID 3
    get_customer_conversations(r, customer_id=3)
    
    print("✓ Test completed successfully!\n")


if __name__ == "__main__":
    main()