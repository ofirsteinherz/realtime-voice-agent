"""
Conversation service for saving conversation history.
"""
import redis
import json
from datetime import datetime
from typing import Dict, List, Optional


# Redis connection singleton
_redis_client = None

def get_redis_connection() -> redis.Redis:
    """
    Get or create Redis connection.
    Uses singleton pattern to avoid creating multiple connections.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host='redis', 
            port=6379, 
            decode_responses=True
        )
    return _redis_client


def save_conversation_data(session_id: str, customer_id: Optional[int], messages: List[Dict]) -> Dict:
    """
    Save conversation history to Redis.
    
    Args:
        session_id: Unique session identifier (UUID)
        customer_id: The customer's unique identifier (optional, can be None initially)
        messages: List of conversation messages
        
    Returns:
        Result dictionary with success status
    """
    try:
        r = get_redis_connection()
        
        # Default to empty list if no messages provided
        if messages is None:
            messages = []
        
        print(f"Saving conversation for session {session_id}, customer {customer_id}, {len(messages)} messages")
        
        conversation_data = {
            'session_id': session_id,
            'customer_id': str(customer_id) if customer_id else 'unknown',
            'conversation_history': json.dumps(messages, ensure_ascii=False),
            'timestamp': datetime.now().isoformat(),
            'message_count': str(len(messages))
        }
        
        # Update existing conversation (same key = update)
        r.hset(f"conversation:{session_id}", mapping=conversation_data)
        
        return {
            'success': True,
            'session_id': session_id,
            'customer_id': customer_id if customer_id else 'unknown',
            'message_count': len(messages),
            'timestamp': conversation_data['timestamp']
        }
    except Exception as e:
        return {
            'success': False,
            'error': 'database_error',
            'message': str(e)
        }