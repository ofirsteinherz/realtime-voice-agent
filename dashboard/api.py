"""
Dashboard API Server
Provides metrics endpoints for the AI Agent Dashboard
"""

from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

# Add backend to path to import metrics calculator
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from redis_metrics_calculator import (
    connect_redis,
    get_conversations_last_week,
    get_reviews_count,
    get_messages_per_conversation,
    get_suspicious_messages,
    get_tool_usage_stats,
    get_test_results
)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access


@app.route('/api/metrics', methods=['GET'])
def get_all_metrics():
    """
    Get all dashboard metrics in one call
    Returns comprehensive metrics data for the dashboard
    """
    try:
        r = connect_redis()
        if not r:
            return jsonify({'error': 'Failed to connect to Redis'}), 500
        
        metrics = {
            'conversations_last_week': get_conversations_last_week(r),
            'reviews': get_reviews_count(r),
            'messages_per_conversation': get_messages_per_conversation(r),
            'suspicious_messages': get_suspicious_messages(r),
            'tool_usage': get_tool_usage_stats(r),
            'test_results': get_test_results(r)
        }
        
        return jsonify(metrics)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        r = connect_redis()
        if not r:
            return jsonify({'status': 'unhealthy', 'redis': 'disconnected'}), 503
        
        return jsonify({'status': 'healthy', 'redis': 'connected'})
    
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503


if __name__ == '__main__':
    print("\n🚀 Dashboard API Server Starting...")
    print("📊 Metrics endpoint: http://localhost:8002/api/metrics")
    print("❤️  Health check: http://localhost:8002/api/health")
    print("\n")
    
    app.run(host='0.0.0.0', port=8002, debug=True)