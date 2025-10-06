"""
Redis Metrics Calculator Script - AI Agent Dashboard
This script calculates KPIs and metrics for the AI agent dashboard
"""

import redis
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Dict, List, Any


def connect_redis():
    """Connect to Redis server"""
    try:
        r = redis.Redis(
            host='redis',
            port=6379,
            decode_responses=True
        )
        r.ping()
        print("✓ Successfully connected to Redis")
        return r
    except redis.ConnectionError:
        print("✗ Failed to connect to Redis")
        return None


def get_conversations_last_week(r) -> Dict[str, Any]:
    """
    KPI: כמות שיחות בשבוע האחרון (Conversations in last week)
    Returns total count and list of recent conversations
    """
    print("\n" + "="*70)
    print("📊 KPI: Conversations in Last Week")
    print("="*70)
    
    one_week_ago = datetime.now() - timedelta(days=7)
    conversation_keys = r.keys('conversation:*')
    
    recent_conversations = []
    for key in conversation_keys:
        conv_data = r.hgetall(key)
        if conv_data and 'timestamp' in conv_data:
            timestamp = datetime.fromisoformat(conv_data['timestamp'])
            if timestamp >= one_week_ago:
                # Get conversation history and extract last message
                history = json.loads(conv_data.get('conversation_history', '[]'))
                last_message = ''
                if history:
                    # Get the last message content
                    last_msg = history[-1]
                    last_message = last_msg.get('content', '') if isinstance(last_msg, dict) else ''
                
                recent_conversations.append({
                    'session_id': conv_data.get('session_id', 'N/A'),
                    'customer_id': conv_data.get('customer_id', 'N/A'),
                    'timestamp': conv_data.get('timestamp', 'N/A'),
                    'message_count': len(history),
                    'last_message': last_message,
                    'messages': history  # Include full conversation history for modal
                })
    
    total_count = len(recent_conversations)
    
    print(f"Total conversations (last 7 days): {total_count}")
    print(f"\nRecent conversations:")
    for i, conv in enumerate(recent_conversations[:5], 1):
        print(f"  {i}. Session: {conv['session_id'][:8]}... | Customer: {conv['customer_id']} | "
              f"Messages: {conv['message_count']} | Time: {conv['timestamp']}")
    
    if len(recent_conversations) > 5:
        print(f"  ... and {len(recent_conversations) - 5} more")
    
    return {
        'total_count': total_count,
        'conversations': recent_conversations,
        'period': '7_days'
    }


def get_reviews_count(r) -> Dict[str, Any]:
    """
    KPI: כמות חוות דעת (Reviews count)
    Returns total reviews and their distribution
    """
    print("\n" + "="*70)
    print("📊 KPI: Customer Reviews")
    print("="*70)
    
    review_keys = r.keys('review:*')
    reviews = []
    
    for key in review_keys:
        review_data = r.hgetall(key)
        if review_data:
            reviews.append({
                'session_id': review_data.get('session_id', 'N/A'),
                'customer_id': review_data.get('customer_id', 'N/A'),
                'review_text': review_data.get('review_text', ''),
                'timestamp': review_data.get('timestamp', 'N/A')
            })
    
    total_count = len(reviews)
    
    print(f"Total reviews: {total_count}")
    print(f"\nSample reviews:")
    for i, review in enumerate(reviews[:3], 1):
        text_preview = review['review_text'][:60] + "..." if len(review['review_text']) > 60 else review['review_text']
        print(f"  {i}. Customer {review['customer_id']}: \"{text_preview}\"")
    
    return {
        'total_count': total_count,
        'reviews': reviews
    }


def get_messages_per_conversation(r) -> Dict[str, Any]:
    """
    KPI: כמות הודעות לכל שיחה (Messages per conversation)
    Returns average, min, max, and distribution
    """
    print("\n" + "="*70)
    print("📊 KPI: Messages per Conversation")
    print("="*70)
    
    conversation_keys = r.keys('conversation:*')
    message_counts = []
    conversation_details = []
    
    for key in conversation_keys:
        conv_data = r.hgetall(key)
        if conv_data and 'conversation_history' in conv_data:
            history = json.loads(conv_data.get('conversation_history', '[]'))
            msg_count = len(history)
            message_counts.append(msg_count)
            
            conversation_details.append({
                'session_id': conv_data.get('session_id', 'N/A'),
                'customer_id': conv_data.get('customer_id', 'N/A'),
                'message_count': msg_count,
                'timestamp': conv_data.get('timestamp', 'N/A')
            })
    
    if message_counts:
        avg_messages = sum(message_counts) / len(message_counts)
        min_messages = min(message_counts)
        max_messages = max(message_counts)
    else:
        avg_messages = min_messages = max_messages = 0
    
    print(f"Total conversations analyzed: {len(conversation_keys)}")
    print(f"Average messages per conversation: {avg_messages:.2f}")
    print(f"Min messages: {min_messages}")
    print(f"Max messages: {max_messages}")
    
    print(f"\nConversation breakdown:")
    for i, conv in enumerate(conversation_details[:5], 1):
        print(f"  {i}. Session {conv['session_id'][:8]}... | Customer: {conv['customer_id']} | "
              f"Messages: {conv['message_count']}")
    
    return {
        'total_conversations': len(conversation_keys),
        'average_messages': avg_messages,
        'min_messages': min_messages,
        'max_messages': max_messages,
        'message_counts': message_counts,
        'conversation_details': conversation_details
    }


def get_suspicious_messages(r) -> Dict[str, Any]:
    """
    KPI: כמות הודעות חשודות - התקפה ותוכן לא תקין (Suspicious messages)
    Returns count of messages that triggered security alerts
    
    NOTE: Moderation data is saved ONLY when content is flagged as suspicious.
    Safe messages are not stored to save space.
    """
    print("\n" + "="*70)
    print("📊 KPI: Suspicious Messages (Security Alerts)")
    print("="*70)
    
    # Get all moderation session keys
    moderation_keys = r.keys('moderation:*')
    # Filter out the count key
    moderation_session_keys = [k for k in moderation_keys if k != 'moderation:count']
    
    # Count actual moderation attempts from data
    actual_moderation_count = 0
    for key in moderation_session_keys:
        actual_moderation_count += r.llen(key)
    
    # Get stored count (may be 0 if not set)
    stored_count = int(r.get('moderation:count') or 0)
    
    # Use the maximum of stored count or actual count
    # (in case count wasn't incremented for older data)
    total_moderation_count = max(stored_count, actual_moderation_count)
    
    suspicious_messages = []
    openai_categories = Counter()
    llama_attacks = 0
    
    for key in moderation_session_keys:
        # Get all moderation attempts for this session (stored as list)
        session_data = r.lrange(key, 0, -1)
        for entry in session_data:
            try:
                moderation = json.loads(entry)
                if moderation.get('flagged', False):
                    # Extract OpenAI categories
                    openai_data = moderation.get('openai', {})
                    if openai_data.get('flagged'):
                        top_category = openai_data.get('top_category')
                        if top_category:
                            openai_categories[top_category] += 1
                    
                    # Count Llama attacks
                    llama_data = moderation.get('llama', {})
                    if llama_data.get('detected_attack'):
                        llama_attacks += 1
                    
                    suspicious_messages.append({
                        'session_id': key.split(':')[1] if ':' in key else 'N/A',
                        'timestamp': moderation.get('timestamp', 'N/A'),
                        'openai_flagged': openai_data.get('flagged', False),
                        'openai_category': openai_data.get('top_category'),
                        'openai_score': openai_data.get('top_score'),
                        'llama_detected': llama_data.get('detected_attack', False),
                        'llama_score': llama_data.get('score'),
                        'message': moderation.get('message', 'N/A')[:100]
                    })
            except json.JSONDecodeError:
                continue
    
    total_suspicious = len(suspicious_messages)
    
    print(f"Total moderation checks: {total_moderation_count}")
    print(f"⚠️  Total suspicious messages flagged: {total_suspicious}")
    
    if total_suspicious == 0:
        print(f"\n✅ No suspicious content detected - all messages were safe!")
        print(f"   (Note: Only flagged content is stored in the database)")
    else:
        print(f"\n🚨 Suspicious content detected!")
        
        if openai_categories:
            print(f"\nOpenAI Moderation Categories:")
            for category, count in openai_categories.most_common():
                print(f"  - {category}: {count}")
        
        if llama_attacks > 0:
            print(f"\nLlama Guard Prompt Injection Attacks: {llama_attacks}")
        
        print(f"\nSample suspicious messages:")
        for i, msg in enumerate(suspicious_messages[:3], 1):
            print(f"  {i}. Session {msg['session_id'][:8]}...")
            if msg['openai_flagged']:
                print(f"     OpenAI: {msg['openai_category']} (score: {msg['openai_score']:.4f})")
            if msg['llama_detected']:
                print(f"     Llama: Prompt injection (score: {msg['llama_score']:.4f})")
            print(f"     Message: {msg['message'][:60]}...")
    
    return {
        'total_moderation_checks': total_moderation_count,
        'total_suspicious': total_suspicious,
        'openai_categories': dict(openai_categories),
        'llama_attacks': llama_attacks,
        'suspicious_messages': suspicious_messages
    }


def get_tool_usage_stats(r) -> Dict[str, Any]:
    """
    נתוני שימוש Tools - Popular tool calls
    Analyzes tool usage from conversation messages AND test results
    """
    print("\n" + "="*70)
    print("📊 Tool Usage Statistics")
    print("="*70)
    
    conversation_keys = r.keys('conversation:*')
    test_result_keys = r.keys('test_result:*')
    
    tool_counter = Counter()
    tool_details = defaultdict(list)
    
    # Method 1: From conversation history
    conv_tools_found = 0
    for key in conversation_keys:
        conv_data = r.hgetall(key)
        if conv_data and 'conversation_history' in conv_data:
            history = json.loads(conv_data.get('conversation_history', '[]'))
            session_id = conv_data.get('session_id', 'N/A')
            
            for message in history:
                # Check for our custom function_call format (from frontend)
                if message.get('type') == 'function_call' and message.get('function_name'):
                    tool_name = message.get('function_name')
                    tool_counter[tool_name] += 1
                    conv_tools_found += 1
                    tool_details[tool_name].append({
                        'session_id': session_id,
                        'source': 'conversation',
                        'timestamp': message.get('timestamp', conv_data.get('timestamp', 'N/A')),
                        'arguments': message.get('arguments', {})
                    })
                
                # Also check for OpenAI standard format (tool_calls array)
                elif message.get('role') == 'assistant' and 'tool_calls' in message:
                    for tool_call in message.get('tool_calls', []):
                        tool_name = tool_call.get('function', {}).get('name', 'unknown')
                        tool_counter[tool_name] += 1
                        conv_tools_found += 1
                        tool_details[tool_name].append({
                            'session_id': session_id,
                            'source': 'conversation',
                            'timestamp': conv_data.get('timestamp', 'N/A')
                        })
    
    # Method 2: From test results (has tools_called field)
    test_tools_found = 0
    for key in test_result_keys:
        test_data = r.hgetall(key)
        if test_data and 'tools_called' in test_data:
            try:
                tools_called = json.loads(test_data['tools_called'])
                test_name = test_data.get('test_name', 'N/A')
                timestamp = test_data.get('timestamp', 'N/A')
                
                for tool_call in tools_called:
                    tool_name = tool_call.get('name', 'unknown')
                    tool_counter[tool_name] += 1
                    test_tools_found += 1
                    tool_details[tool_name].append({
                        'test_name': test_name,
                        'source': 'test_result',
                        'timestamp': timestamp
                    })
            except (json.JSONDecodeError, KeyError):
                continue
    
    total_tool_calls = sum(tool_counter.values())
    
    print(f"Total tool calls: {total_tool_calls}")
    print(f"  From conversations: {conv_tools_found}")
    print(f"  From test results: {test_tools_found}")
    print(f"Unique tools used: {len(tool_counter)}")
    
    if tool_counter:
        print(f"\n🔧 Most popular tools:")
        for i, (tool, count) in enumerate(tool_counter.most_common(10), 1):
            percentage = (count / total_tool_calls * 100) if total_tool_calls > 0 else 0
            print(f"  {i}. {tool}: {count} calls ({percentage:.1f}%)")
    else:
        print("\n⚠️  No tool usage data found.")
        print("   Tools will appear here after:")
        print("   - Running the AI agent with actual conversations")
        print("   - Running test cases that use pharmacy tools")
    
    return {
        'total_tool_calls': total_tool_calls,
        'from_conversations': conv_tools_found,
        'from_tests': test_tools_found,
        'unique_tools': len(tool_counter),
        'tool_breakdown': dict(tool_counter),
        'tool_details': dict(tool_details)
    }


def get_test_results(r) -> Dict[str, Any]:
    """
    טסטים - Test results overview
    Analyzes test execution results from the test runner
    """
    print("\n" + "="*70)
    print("📊 Test Results")
    print("="*70)
    
    test_count = int(r.get('test_results:count') or 0)
    test_keys = r.keys('test_result:*')
    
    test_results = []
    success_count = 0
    in_progress_count = 0
    failed_count = 0
    
    for key in test_keys:
        test_data = r.hgetall(key)
        if test_data:
            # Parse judge evaluation to get status
            status = 'unknown'
            if 'judge_evaluation' in test_data:
                try:
                    judge_eval = json.loads(test_data['judge_evaluation'])
                    status = judge_eval.get('final_status', 'unknown')
                except json.JSONDecodeError:
                    pass
            
            # Get expected outcome
            expected = test_data.get('expected_outcome', 'N/A')
            
            test_results.append({
                'test_name': test_data.get('test_name', 'N/A'),
                'subject': test_data.get('subject', 'N/A'),
                'status': status,
                'expected_outcome': expected,
                'timestamp': test_data.get('timestamp', 'N/A'),
                'turns': test_data.get('turns', 'N/A')
            })
            
            # Count by status
            if status == 'success':
                success_count += 1
            elif status == 'in_progress':
                in_progress_count += 1
            elif status == 'failed':
                failed_count += 1
    
    print(f"Total test executions: {len(test_results)}")
    print(f"✅ Success: {success_count}")
    print(f"⏳ In Progress: {in_progress_count}")
    print(f"❌ Failed: {failed_count}")
    
    if test_results:
        print(f"\n🧪 Recent test results:")
        for i, test in enumerate(test_results[:5], 1):
            status_icons = {
                'success': '✅',
                'failed': '❌',
                'in_progress': '⏳',
                'unknown': '❓'
            }
            icon = status_icons.get(test['status'], '❓')
            print(f"  {icon} {i}. {test['test_name']}")
            print(f"      Subject: {test['subject']} | Expected: {test['expected_outcome']} | Turns: {test['turns']}")
    else:
        print("\n⚠️  No test results available yet.")
        print("   Run the test suite to see results here.")
    
    return {
        'total_count': test_count,
        'total_results': len(test_results),
        'success': success_count,
        'in_progress': in_progress_count,
        'failed': failed_count,
        'test_results': test_results
    }


def calculate_all_metrics(r) -> Dict[str, Any]:
    """Calculate all metrics and return comprehensive report"""
    print("\n" + "🎯"*35)
    print("AI AGENT DASHBOARD METRICS CALCULATOR")
    print("🎯"*35)
    
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'conversations_last_week': get_conversations_last_week(r),
        'reviews': get_reviews_count(r),
        'messages_per_conversation': get_messages_per_conversation(r),
        'suspicious_messages': get_suspicious_messages(r),
        'tool_usage': get_tool_usage_stats(r),
        'test_results': get_test_results(r)
    }
    
    return metrics


def display_summary(metrics: Dict[str, Any]):
    """Display executive summary of all metrics"""
    print("\n" + "="*70)
    print("📈 EXECUTIVE SUMMARY")
    print("="*70)
    
    print(f"\n🗓️  Reporting Period: Last 7 days")
    print(f"📅  Generated: {metrics['timestamp']}")
    
    print(f"\n📊 Key Performance Indicators:")
    print(f"  • Conversations (7 days): {metrics['conversations_last_week']['total_count']}")
    print(f"  • Customer Reviews: {metrics['reviews']['total_count']}")
    print(f"  • Avg Messages/Conv: {metrics['messages_per_conversation']['average_messages']:.2f}")
    print(f"  • Tool Calls: {metrics['tool_usage']['total_tool_calls']} (Conv: {metrics['tool_usage']['from_conversations']}, Tests: {metrics['tool_usage']['from_tests']})")
    print(f"  • Suspicious Messages: {metrics['suspicious_messages']['total_suspicious']}")
    print(f"  • Test Results: {metrics['test_results']['total_results']} (✅{metrics['test_results']['success']}, ❌{metrics['test_results']['failed']})")
    
    print("\n" + "="*70)


def export_metrics_json(metrics: Dict[str, Any], filename: str = 'metrics_export.json'):
    """Export metrics to JSON file for dashboard consumption"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Metrics exported to: {filename}")


def main():
    """Main function"""
    # Connect to Redis
    r = connect_redis()
    if not r:
        return
    
    # Calculate all metrics
    metrics = calculate_all_metrics(r)
    
    # Display summary
    display_summary(metrics)
    
    # Export to JSON
    export_metrics_json(metrics)
    
    print("\n✅ Metrics calculation completed successfully!")
    print("\n💡 Next steps:")
    print("  1. Review the metrics output above")
    print("  2. Use metrics_export.json for dashboard integration")
    print("  3. Schedule this script to run periodically for real-time data")


if __name__ == "__main__":
    main()