"""
WarungTech AI API Server
Flask API wrapper for the crypto investment and business analysis agent
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import traceback
from datetime import datetime
import threading
import time

# Import the main agent
from main import run_crypto_agent_indonesia, ChatHistoryManager, FeedbackSystem

app = Flask(__name__)
CORS(app, origins=['*'])  # Allow all origins for development

# Global variables for managing conversations
active_conversations = {}
conversation_lock = threading.Lock()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'WarungTech AI API is running',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0'
    })

@app.route('/chat', methods=['POST'])
def chat_endpoint():
    """
    Main chat endpoint for WarungTech AI
    
    Expected JSON payload:
    {
        "message": "User message",
        "user_id": "optional_user_id",
        "conversation_id": "optional_conversation_id"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                'success': False,
                'error': 'Message is required'
            }), 400
        
        user_message = data['message'].strip()
        user_id = data.get('user_id', 'mobile_user')
        conversation_id = data.get('conversation_id')
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': 'Message cannot be empty'
            }), 400
        
        print(f"\n🤖 Received chat request:")
        print(f"   User ID: {user_id}")
        print(f"   Message: {user_message}")
        print(f"   Conversation ID: {conversation_id}")
        
        # Run the AI agent
        result = run_crypto_agent_indonesia(
            user_query=user_message,
            user_id=user_id,
            verbose=False  # Don't print to console for API
        )
        
        if result['success']:
            # Extract key information from the report
            report = result['report']
            
            # Try to extract structured data from the report
            response_data = {
                'message': extract_summary_from_report(report),
                'full_report': report,
                'conversation_id': result['conversation_id'],
                'user_profile': result['state'].get('user_profile', {}),
                'timestamp': datetime.now().isoformat(),
                'analysis_type': detect_analysis_type(user_message, report)
            }
            
            return jsonify({
                'success': True,
                'data': response_data
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            }), 500
            
    except Exception as e:
        print(f"❌ Error in chat endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/quick-action', methods=['POST'])
def quick_action_endpoint():
    """
    Handle quick actions from the mobile app
    
    Expected JSON payload:
    {
        "action": "check_revenue|create_promo|payment_qr|crypto_analysis",
        "user_id": "optional_user_id",
        "params": {}
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'action' not in data:
            return jsonify({
                'success': False,
                'error': 'Action is required'
            }), 400
        
        action = data['action']
        user_id = data.get('user_id', 'mobile_user')
        params = data.get('params', {})
        
        # Map actions to appropriate queries
        action_queries = {
            'check_revenue': 'Tolong analisis omzet dan performa bisnis warung saya hari ini',
            'create_promo': 'Saya ingin buat promo untuk meningkatkan penjualan. Tolong analisis bisnis dan berikan rekomendasi promo yang tepat',
            'payment_qr': 'Bagaimana cara terima pembayaran dengan QR code dan apa keuntungan pakai blockchain?',
            'crypto_analysis': 'Saya ingin investasi crypto dengan dana 5 juta. Tolong analisis dan berikan rekomendasi',
            'explain_risk': 'Jelaskan risiko investasi crypto dan blockchain untuk bisnis warung',
            'business_analysis': 'Analisis kondisi bisnis warung saya dan berikan rekomendasi untuk meningkatkan omzet'
        }
        
        query = action_queries.get(action)
        if not query:
            return jsonify({
                'success': False,
                'error': f'Unknown action: {action}'
            }), 400
        
        # Add parameters to query if provided
        if params:
            if 'amount' in params:
                query = query.replace('5 juta', f"{params['amount']} juta")
            if 'business_type' in params:
                query += f" untuk bisnis {params['business_type']}"
        
        print(f"\n⚡ Quick action request:")
        print(f"   Action: {action}")
        print(f"   Generated query: {query}")
        
        # Run the AI agent
        result = run_crypto_agent_indonesia(
            user_query=query,
            user_id=user_id,
            verbose=False
        )
        
        if result['success']:
            # Create action-specific response
            response_data = create_action_response(action, result)
            
            return jsonify({
                'success': True,
                'data': response_data
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Unknown error occurred')
            }), 500
            
    except Exception as e:
        print(f"❌ Error in quick action endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/conversation-history/<user_id>', methods=['GET'])
def get_conversation_history(user_id):
    """Get conversation history for a user"""
    try:
        chat_manager = ChatHistoryManager(user_id)
        limit = request.args.get('limit', 10, type=int)
        
        conversations = chat_manager.get_recent_conversations(limit)
        
        return jsonify({
            'success': True,
            'data': {
                'conversations': conversations,
                'total': len(chat_manager.conversations)
            }
        })
        
    except Exception as e:
        print(f"❌ Error getting conversation history: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback for a conversation"""
    try:
        data = request.get_json()
        
        required_fields = ['user_id', 'conversation_id', 'rating']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        user_id = data['user_id']
        conversation_id = data['conversation_id']
        feedback_data = {
            'rating': data['rating'],
            'helpful': data.get('helpful', True),
            'accuracy': data.get('accuracy', 5),
            'comments': data.get('comments', ''),
            'suggestions': data.get('suggestions', '')
        }
        
        # Save feedback
        chat_manager = ChatHistoryManager(user_id)
        success = chat_manager.add_feedback(conversation_id, feedback_data)
        
        if success:
            # Also save to global feedback system
            feedback_system = FeedbackSystem()
            feedback_system.add_feedback(user_id, conversation_id, feedback_data)
            
            return jsonify({
                'success': True,
                'message': 'Feedback submitted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid conversation ID'
            }), 400
            
    except Exception as e:
        print(f"❌ Error submitting feedback: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def extract_summary_from_report(report):
    """Extract a concise summary from the full AI report"""
    lines = report.split('\n')
    
    # Look for executive summary or key points
    summary_lines = []
    in_summary = False
    
    for line in lines:
        line = line.strip()
        if 'ringkasan' in line.lower() or 'executive summary' in line.lower():
            in_summary = True
            continue
        elif line.startswith('#') and in_summary:
            break
        elif in_summary and line and not line.startswith('#'):
            summary_lines.append(line)
            if len(summary_lines) >= 3:  # Limit to 3 key points
                break
    
    if summary_lines:
        return ' '.join(summary_lines)
    
    # Fallback: extract first meaningful paragraph
    for line in lines:
        line = line.strip()
        if len(line) > 50 and not line.startswith('#') and not line.startswith('='):
            return line[:300] + '...' if len(line) > 300 else line
    
    return "Analisis telah selesai. Lihat laporan lengkap untuk detail rekomendasi."

def detect_analysis_type(user_message, report):
    """Detect the type of analysis performed"""
    message_lower = user_message.lower()
    report_lower = report.lower()
    
    if any(word in message_lower for word in ['bisnis', 'warung', 'toko', 'omzet', 'promo']):
        if any(word in message_lower for word in ['crypto', 'bitcoin', 'investasi']):
            return 'comprehensive'
        return 'business'
    elif any(word in message_lower for word in ['crypto', 'bitcoin', 'ethereum', 'investasi']):
        return 'crypto'
    else:
        return 'general'

def create_action_response(action, result):
    """Create action-specific response format"""
    base_response = {
        'message': extract_summary_from_report(result['report']),
        'full_report': result['report'],
        'conversation_id': result['conversation_id'],
        'timestamp': datetime.now().isoformat(),
        'action': action
    }
    
    # Add action-specific data
    if action == 'check_revenue':
        base_response.update({
            'revenue_data': {
                'today': 'Rp 450.000',
                'transactions': 18,
                'trend': 'increasing',
                'comparison': '+12% vs yesterday'
            }
        })
    elif action == 'create_promo':
        base_response.update({
            'promo_suggestions': [
                {'type': 'Flash Sale', 'discount': '20%', 'duration': '24 jam'},
                {'type': 'Bundle Deal', 'discount': 'Buy 2 Get 1', 'duration': '1 minggu'},
                {'type': 'Loyalty Reward', 'discount': '15%', 'duration': '2 minggu'}
            ]
        })
    elif action == 'payment_qr':
        base_response.update({
            'qr_info': {
                'amount': 'Rp 25.000',
                'method': 'IDRX (Blockchain)',
                'benefits': ['Biaya rendah', 'Transparan', 'Aman']
            }
        })
    elif action == 'crypto_analysis':
        base_response.update({
            'crypto_recommendations': [
                {'coin': 'BTC', 'allocation': '40%', 'risk': 'Low'},
                {'coin': 'ETH', 'allocation': '30%', 'risk': 'Medium'},
                {'coin': 'BNB', 'allocation': '20%', 'risk': 'Medium'},
                {'coin': 'SOL', 'allocation': '10%', 'risk': 'High'}
            ]
        })
    
    return base_response

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 WARUNGTECH AI API SERVER")
    print("="*80)
    print("📡 Starting Flask API server...")
    print("🔗 Endpoints available:")
    print("   POST /chat - Main chat interface")
    print("   POST /quick-action - Quick action handler")
    print("   GET  /conversation-history/<user_id> - Get chat history")
    print("   POST /feedback - Submit feedback")
    print("   GET  /health - Health check")
    print("="*80)
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',  # Allow external connections
        port=5000,       # Port 5000 for AI API
        debug=True,      # Enable debug mode
        threaded=True    # Enable threading
    )