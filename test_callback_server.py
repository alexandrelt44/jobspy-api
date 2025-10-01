#!/usr/bin/env python3
"""
Simple test callback server to receive job completion notifications
"""

from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)

# Store received callbacks for inspection
callbacks_received = []

@app.route('/callback', methods=['POST'])
def receive_callback():
    """Receive job completion callback"""
    try:
        data = request.get_json()
        callback_info = {
            "received_at": datetime.now().isoformat(),
            "data": data,
            "headers": dict(request.headers)
        }
        callbacks_received.append(callback_info)
        
        print(f"🔔 Callback received at {callback_info['received_at']}")
        print(f"   Job ID: {data.get('job_id', 'unknown')}")
        print(f"   Status: {data.get('status', 'unknown')}")
        print(f"   Total Jobs: {data.get('result', {}).get('total_jobs', 'N/A')}")
        
        return jsonify({"success": True, "message": "Callback received"}), 200
        
    except Exception as e:
        print(f"❌ Callback error: {e}")
        return jsonify({"success": False, "error": str(e)}), 400

@app.route('/callbacks', methods=['GET'])
def list_callbacks():
    """List all received callbacks"""
    return jsonify({
        "total_callbacks": len(callbacks_received),
        "callbacks": callbacks_received
    })

@app.route('/clear', methods=['POST'])
def clear_callbacks():
    """Clear all received callbacks"""
    global callbacks_received
    callbacks_received = []
    return jsonify({"success": True, "message": "Callbacks cleared"})

if __name__ == '__main__':
    print("🎯 Starting test callback server on http://localhost:5001")
    print("   Callback endpoint: http://localhost:5001/callback")
    print("   View callbacks: http://localhost:5001/callbacks")
    app.run(host='0.0.0.0', port=5001, debug=True)