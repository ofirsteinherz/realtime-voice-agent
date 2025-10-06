"""
Test script to analyze conversation history and count tool usage
"""

import redis
import json
import sys
from collections import Counter


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


def extract_tool_calls_from_conversation(conversation_history):
    """
    Extract tool calls from conversation history.
    
    Args:
        conversation_history: List of message dicts or JSON string
        
    Returns:
        List of tool names used in the conversation
    """
    tool_calls = []
    
    # Parse JSON if needed
    if isinstance(conversation_history, str):
        try:
            conversation_history = json.loads(conversation_history)
        except json.JSONDecodeError:
            return tool_calls
    
    # Iterate through messages
    for message in conversation_history:
        # Check if this is a function_call type message
        if message.get('type') == 'function_call':
            # Extract function_name directly from the message
            function_name = message.get('function_name')
            if function_name:
                tool_calls.append(function_name)
        
        # Also check for old format with function_call object
        if 'function_call' in message:
            tool_name = message['function_call'].get('name')
            if tool_name:
                tool_calls.append(tool_name)
        
        # Check for tool_calls array format
        if 'tool_calls' in message:
            for tool_call in message['tool_calls']:
                if 'function' in tool_call:
                    tool_name = tool_call['function'].get('name')
                    if tool_name:
                        tool_calls.append(tool_name)
    
    return tool_calls


def analyze_all_conversations(r):
    """
    Analyze all conversation history and count tool usage.
    
    Returns:
        Counter object with tool usage counts
    """
    conversation_keys = r.keys('conversation:*')
    
    if not conversation_keys:
        return Counter()
    
    all_tool_calls = []
    
    for key in conversation_keys:
        conversation_data = r.hgetall(key)
        history = conversation_data.get('conversation_history', '[]')
        
        tool_calls = extract_tool_calls_from_conversation(history)
        all_tool_calls.extend(tool_calls)
    
    return Counter(all_tool_calls)


def display_specific_tools_usage(tool_counts):
    """Display usage statistics for specific tools"""
    print("="*60)
    print("SPECIFIC TOOLS USAGE")
    print("="*60)
    
    specific_tools = [
        'get_customer_info',
        'search_customer_by_name',
        'list_all_medicines',
        'get_inventory_status',
        'check_low_stock'
    ]
    
    print("\nMonitored Tools:\n")
    
    total_calls = 0
    for tool in specific_tools:
        count = tool_counts.get(tool, 0)
        total_calls += count
        print(f"  • {tool:<30} {count:>5} calls")
    
    print(f"\n  Total calls (monitored tools): {total_calls:>5}")
    print("="*60)


def display_top_tools_usage(tool_counts, top_n=5):
    """Display top N most used tools"""
    print("\n" + "="*60)
    print(f"TOP {top_n} MOST USED TOOLS")
    print("="*60)
    
    if not tool_counts:
        print("\nNo tool usage data found in conversation history.")
        return
    
    # Get top N tools
    top_tools = tool_counts.most_common(top_n)
    
    print(f"\nTotal unique tools used: {len(tool_counts)}\n")
    print(f"{'Rank':<6} {'Tool Name':<35} {'Calls':>10}")
    print("-" * 60)
    
    for i, (tool_name, count) in enumerate(top_tools, 1):
        print(f"{i:<6} {tool_name:<35} {count:>10}")
    
    total_calls = sum(tool_counts.values())
    print("-" * 60)
    print(f"{'Total (all tools)':<42} {total_calls:>10}")
    print("="*60)


def display_all_tools_by_category(tool_counts):
    """Display all tools grouped by category"""
    print("\n" + "="*60)
    print("ALL TOOLS USAGE BY CATEGORY")
    print("="*60)
    
    if not tool_counts:
        print("\nNo tool usage data found in conversation history.")
        return
    
    # Tool categories
    categories = {
        'Customer Operations': [
            'get_customer_info',
            'search_customer_by_name',
            'get_customer_prescriptions'
        ],
        'Medicine Operations': [
            'get_medicine_info',
            'search_medicine_by_name',
            'list_all_medicines',
            'calculate_total_pills_available'
        ],
        'Dispensing Operations': [
            'check_medicine_availability',
            'dispense_medicine',
            'validate_prescription_availability'
        ],
        'Inventory Operations': [
            'get_inventory_status',
            'check_low_stock'
        ],
        'Conversation & Feedback': [
            'save_review'
        ]
    }
    
    print()
    for category, tools in categories.items():
        category_total = 0
        category_data = []
        
        for tool in tools:
            count = tool_counts.get(tool, 0)
            if count > 0:
                category_total += count
                category_data.append((tool, count))
        
        if category_total > 0:
            print(f"\n{category}:")
            print(f"  Total: {category_total} calls")
            for tool, count in sorted(category_data, key=lambda x: x[1], reverse=True):
                percentage = (count / category_total * 100) if category_total > 0 else 0
                print(f"    • {tool:<35} {count:>5} ({percentage:>5.1f}%)")
    
    # Show any tools not in categories
    all_known_tools = set()
    for tools in categories.values():
        all_known_tools.update(tools)
    
    unknown_tools = {tool: count for tool, count in tool_counts.items() if tool not in all_known_tools}
    
    if unknown_tools:
        print(f"\n\nOther/Unknown Tools:")
        print(f"  Total: {sum(unknown_tools.values())} calls")
        for tool, count in sorted(unknown_tools.items(), key=lambda x: x[1], reverse=True):
            print(f"    • {tool:<35} {count:>5}")
    
    print("\n" + "="*60)


def display_conversation_stats(r):
    """Display basic conversation statistics"""
    print("\n" + "="*60)
    print("CONVERSATION STATISTICS")
    print("="*60)
    
    conversation_keys = r.keys('conversation:*')
    print(f"\nTotal conversations analyzed: {len(conversation_keys)}")
    
    if conversation_keys:
        total_messages = 0
        for key in conversation_keys:
            conversation_data = r.hgetall(key)
            message_count = conversation_data.get('message_count', '0')
            try:
                total_messages += int(message_count)
            except (ValueError, TypeError):
                pass
        
        print(f"Total messages in conversations: {total_messages}")
        if len(conversation_keys) > 0:
            avg_messages = total_messages / len(conversation_keys)
            print(f"Average messages per conversation: {avg_messages:.1f}")
    
    print("="*60)


def display_top_longest_conversations(r, top_n=3):
    """Display the top N longest conversations"""
    print("\n" + "="*60)
    print(f"TOP {top_n} LONGEST CONVERSATIONS")
    print("="*60)
    
    conversation_keys = r.keys('conversation:*')
    
    if not conversation_keys:
        print("\nNo conversations found.")
        return
    
    # Get conversations with their message counts
    conversations = []
    for key in conversation_keys:
        conversation_data = r.hgetall(key)
        message_count = conversation_data.get('message_count', '0')
        try:
            count = int(message_count)
            conversations.append((key, count, conversation_data))
        except (ValueError, TypeError):
            pass
    
    # Sort by message count descending
    conversations.sort(key=lambda x: x[1], reverse=True)
    
    # Display top N
    for i, (key, msg_count, data) in enumerate(conversations[:top_n], 1):
        print(f"\n{'='*60}")
        print(f"Conversation #{i} - {msg_count} messages")
        print(f"{'='*60}")
        print(f"Session ID: {data.get('session_id', 'N/A')}")
        print(f"Customer ID: {data.get('customer_id', 'N/A')}")
        print(f"Timestamp: {data.get('timestamp', 'N/A')}")
        
        # Parse and display conversation history
        history_json = data.get('conversation_history', '[]')
        try:
            history = json.loads(history_json)
            print(f"\nMessages ({len(history)} total):")
            print("-" * 60)
            
            for j, message in enumerate(history, 1):
                print(f"\nMessage {j}:")
                print(f"  Type: {message.get('type', 'N/A')}")
                print(f"  Role: {message.get('role', 'N/A')}")
                
                # Show content if available
                if 'content' in message and message['content']:
                    content = message['content']
                    if isinstance(content, str):
                        # Truncate long content
                        if len(content) > 200:
                            print(f"  Content: {content[:200]}...")
                        else:
                            print(f"  Content: {content}")
                    else:
                        print(f"  Content: {content}")
                
                # Show function_name if this is a function_call type
                if message.get('type') == 'function_call':
                    print(f"  Function Name: {message.get('function_name', 'N/A')}")
                    if 'arguments' in message:
                        args = message.get('arguments', 'N/A')
                        # Truncate long arguments
                        if isinstance(args, str) and len(args) > 100:
                            print(f"  Arguments: {args[:100]}...")
                        else:
                            print(f"  Arguments: {args}")
                    if 'call_id' in message:
                        print(f"  Call ID: {message.get('call_id')}")
                
                # Show function result if this is a function_result type
                if message.get('type') == 'function_result':
                    print(f"  Function Name: {message.get('function_name', 'N/A')}")
                    if 'result' in message:
                        result = message.get('result', 'N/A')
                        # Truncate long results
                        if isinstance(result, str) and len(result) > 100:
                            print(f"  Result: {result[:100]}...")
                        else:
                            print(f"  Result: {result}")
                
                # Show old format function_call if available
                if 'function_call' in message:
                    func_call = message['function_call']
                    print(f"  Function Call (old format):")
                    print(f"    Name: {func_call.get('name', 'N/A')}")
                    if 'arguments' in func_call:
                        print(f"    Arguments: {func_call.get('arguments', 'N/A')}")
                
                # Show tool_calls if available
                if 'tool_calls' in message:
                    print(f"  Tool Calls:")
                    for tc in message['tool_calls']:
                        if 'function' in tc:
                            print(f"    - {tc['function'].get('name', 'N/A')}")
                            if 'arguments' in tc['function']:
                                print(f"      Args: {tc['function'].get('arguments', 'N/A')}")
                
                # Show all keys for debugging
                print(f"  All keys: {list(message.keys())}")
            
        except json.JSONDecodeError as e:
            print(f"\nError parsing conversation history: {e}")
            print(f"Raw data (first 500 chars): {history_json[:500]}")
    
    print("\n" + "="*60)


def main():
    """Main function"""
    print("\n" + "="*60)
    print("Pharmacy Tool Usage Statistics")
    print("(Analyzing Conversation History)")
    print("="*60 + "\n")
    
    # Connect to Redis
    r = connect_redis()
    
    # Display top 3 longest conversations to understand structure
    display_top_longest_conversations(r, top_n=3)
    
    # Display conversation stats
    display_conversation_stats(r)
    
    # Analyze all conversations and count tool usage
    tool_counts = analyze_all_conversations(r)
    
    # Display specific tools usage
    display_specific_tools_usage(tool_counts)
    
    # Display top 5 tools
    display_top_tools_usage(tool_counts, top_n=5)
    
    # Display all tools by category
    display_all_tools_by_category(tool_counts)
    
    print("\n✓ Analysis completed successfully!\n")


if __name__ == "__main__":
    main()