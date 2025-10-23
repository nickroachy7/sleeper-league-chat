"""
Flask API Server for Fantasy League Assistant
Provides REST API endpoints for the web UI
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from fantasy_assistant import chat
from logger_config import setup_logger
from config import API_PORT, FLASK_ENV, LOG_FILE
import json

# Setup logging
logger = setup_logger('api_server')

app = Flask(__name__)
CORS(app)  # Enable CORS for web UI

# Store conversation history per session
# In production, use Redis or a proper session store
conversations = {}


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    logger.debug("Health check requested")
    return jsonify({
        'status': 'ok',
        'service': 'Fantasy League Assistant API',
        'port': API_PORT,
        'environment': FLASK_ENV,
        'sessions': len(conversations)
    })


@app.route('/api/chat', methods=['POST'])
def chat_endpoint():
    """
    Chat endpoint for sending messages to the assistant
    
    Request body:
    {
        "message": "What are the current standings?",
        "session_id": "unique-session-id" (optional)
    }
    
    Response:
    {
        "response": "Here are the current standings...",
        "session_id": "unique-session-id"
    }
    """
    try:
        data = request.json
        message = data.get('message')
        session_id = data.get('session_id', 'default')
        
        if not message:
            logger.warning(f"Empty message received from session {session_id}")
            return jsonify({'error': 'Message is required'}), 400
        
        logger.info(f"Processing message from session {session_id}: {message[:50]}...")
        
        # Get or create conversation history for this session
        conversation_history = conversations.get(session_id)
        
        # Get response from assistant
        response, updated_history = chat(message, conversation_history)
        
        # Store updated conversation history
        conversations[session_id] = updated_history
        
        logger.info(f"Successfully processed message for session {session_id}")
        
        return jsonify({
            'response': response,
            'session_id': session_id
        })
    
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True, extra={
            'session_id': session_id,
            'user_message': message[:100] if message else None
        })
        return jsonify({'error': str(e)}), 500


@app.route('/api/reset', methods=['POST'])
def reset_conversation():
    """
    Reset conversation history for a session
    
    Request body:
    {
        "session_id": "unique-session-id"
    }
    """
    try:
        data = request.json
        session_id = data.get('session_id', 'default')
        
        if session_id in conversations:
            del conversations[session_id]
            logger.info(f"Reset conversation for session {session_id}")
        
        return jsonify({'message': 'Conversation reset successfully'})
    
    except Exception as e:
        logger.error(f"Error resetting conversation: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/league', methods=['GET'])
def get_league():
    """Get basic league information"""
    try:
        from league_queries import get_league_info
        league_info = get_league_info()
        logger.debug("League info requested")
        return jsonify(league_info)
    except Exception as e:
        logger.error(f"Error fetching league info: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/standings', methods=['GET'])
def get_standings_endpoint():
    """Get current league standings"""
    try:
        from league_queries import get_standings
        standings = get_standings()
        logger.debug("Standings requested")
        return jsonify(standings)
    except Exception as e:
        logger.error(f"Error fetching standings: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import sys
    
    logger.info("="*70)
    logger.info("🚀 FANTASY LEAGUE ASSISTANT API SERVER")
    logger.info("="*70)
    logger.info(f"Server starting on http://localhost:{API_PORT}")
    logger.info(f"Environment: {FLASK_ENV}")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info("\nEndpoints:")
    logger.info("  GET  /api/health           - Health check")
    logger.info("  POST /api/chat             - Send message to assistant")
    logger.info("  POST /api/reset            - Reset conversation")
    logger.info("  GET  /api/league           - Get league info")
    logger.info("  GET  /api/standings        - Get standings")
    logger.info("="*70)
    
    # Debug mode based on environment
    debug_mode = FLASK_ENV == 'development'
    
    logger.info(f"Starting Flask server (debug={debug_mode})...")
    app.run(host='0.0.0.0', port=API_PORT, debug=debug_mode, use_reloader=False)

