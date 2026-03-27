#!/usr/bin/env python3
"""
Simple Flask test to isolate the server issue
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import AIEnhanced

app = Flask(__name__)
CORS(app)

@app.route('/test', methods=['POST'])
def test_endpoint():
    """Simple test endpoint"""
    try:
        data = request.get_json()
        message = data.get('message', 'Hello')
        
        # Test direct agent call
        result = AIEnhanced.run_agent(message)
        
        return jsonify({
            "success": True,
            "message": "Test successful",
            "agent_result": result.get("success", False),
            "report_length": len(result.get("report", ""))
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({
        "status": "ok",
        "message": "Simple Flask test server"
    })

if __name__ == "__main__":
    print("🧪 Starting Simple Flask Test Server...")
    app.run(host='0.0.0.0', port=5001, debug=True)