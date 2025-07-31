"""Flask web application for indici MCP Chatbot."""

import asyncio
import logging
import json
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.config import config
from chatbot.chat_handler import chat_handler
from chatbot.mcp_client import mcp_client

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.logging_level),
    format=config.logging_format
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'indici-mcp-chatbot-secret-key'

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store active sessions
active_sessions = {}

# Initialize MCP client connection
def init_mcp_client():
    """Initialize the MCP client connection."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(mcp_client.connect())
        chat_handler.set_mcp_client(mcp_client)
        loop.close()
        logger.info("MCP client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MCP client: {str(e)}")

# Initialize MCP client on startup
init_mcp_client()

@app.route('/')
def index():
    """Main chat interface."""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    try:
        # Run async health check in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        health_result = loop.run_until_complete(chat_handler.health_check())
        loop.close()
        
        return jsonify({
            "status": "healthy" if health_result.get("success") else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "details": health_result
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/samples')
def get_samples():
    """Get sample queries."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        samples_result = loop.run_until_complete(chat_handler.get_sample_queries())
        loop.close()
        
        return jsonify(samples_result)
    except Exception as e:
        logger.error(f"Error getting samples: {str(e)}")
        return jsonify({
            "samples": [],
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/metrics')
def get_metrics():
    """Get professional performance metrics."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        metrics = loop.run_until_complete(chat_handler.get_performance_metrics())
        loop.close()

        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/diagnose', methods=['POST'])
def diagnose_message():
    """Diagnose how a message would be processed."""
    try:
        data = request.get_json()
        message = data.get('message', '')

        if not message:
            return jsonify({"error": "Message is required"}), 400

        diagnosis = chat_handler.diagnose_message(message)
        return jsonify(diagnosis)
    except Exception as e:
        logger.error(f"Error diagnosing message: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset-metrics', methods=['POST'])
def reset_metrics():
    """Reset performance metrics."""
    try:
        result = chat_handler.reset_metrics()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sidebar-config')
def get_sidebar_config():
    """Get sidebar configuration."""
    try:
        config = chat_handler.get_sidebar_configuration()
        return jsonify(config)
    except Exception as e:
        logger.error(f"Error getting sidebar config: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/system-status')
def get_system_status():
    """Get system status."""
    try:
        status = chat_handler.get_system_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({"error": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    session_id = request.sid
    active_sessions[session_id] = {
        "connected_at": datetime.now(),
        "message_count": 0
    }
    
    logger.info(f"Client connected: {session_id}")
    
    # Send welcome message
    emit('bot_message', {
        "message": "👋 Welcome to the indici Reports Assistant! How can I help you today?",
        "timestamp": datetime.now().isoformat(),
        "type": "greeting"
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    session_id = request.sid
    if session_id in active_sessions:
        del active_sessions[session_id]
    
    logger.info(f"Client disconnected: {session_id}")

@socketio.on('user_message')
def handle_user_message(data):
    """Handle incoming user message."""
    try:
        session_id = request.sid
        message = data.get('message', '').strip()
        
        if not message:
            emit('bot_message', {
                "message": "❌ Please enter a message.",
                "timestamp": datetime.now().isoformat(),
                "type": "error"
            })
            return
        
        # Update session stats
        if session_id in active_sessions:
            active_sessions[session_id]["message_count"] += 1
        
        logger.info(f"Received message from {session_id}: {message}")
        
        # Show typing indicator
        emit('bot_typing', {"typing": True})
        
        # Process message asynchronously
        def process_message():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Handle the message
                response_data = loop.run_until_complete(
                    chat_handler.handle_message(message, session_id)
                )
                
                loop.close()
                
                # Send response
                socketio.emit('bot_typing', {"typing": False}, room=session_id)
                socketio.emit('bot_message', {
                    "message": response_data["response"],
                    "timestamp": response_data["timestamp"],
                    "type": response_data["type"],
                    "success": response_data["success"]
                }, room=session_id)
                
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                socketio.emit('bot_typing', {"typing": False}, room=session_id)
                socketio.emit('bot_message', {
                    "message": f"❌ Sorry, I encountered an error: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                    "type": "error",
                    "success": False
                }, room=session_id)
        
        # Run in background thread
        socketio.start_background_task(process_message)
        
    except Exception as e:
        logger.error(f"Error handling user message: {str(e)}")
        emit('bot_message', {
            "message": "❌ An unexpected error occurred. Please try again.",
            "timestamp": datetime.now().isoformat(),
            "type": "error"
        })

@socketio.on('sample_query')
def handle_sample_query(data):
    """Handle sample query selection."""
    try:
        query = data.get('query', '').strip()
        if query:
            # Emit the query as if user typed it
            emit('user_message_echo', {
                "message": query,
                "timestamp": datetime.now().isoformat()
            })
            
            # Process the query
            handle_user_message({"message": query})
        
    except Exception as e:
        logger.error(f"Error handling sample query: {str(e)}")
        emit('bot_message', {
            "message": "❌ Error processing sample query.",
            "timestamp": datetime.now().isoformat(),
            "type": "error"
        })

@socketio.on('clear_chat')
def handle_clear_chat():
    """Handle chat clearing."""
    try:
        session_id = request.sid
        
        # Clear chat history
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response_data = loop.run_until_complete(
            chat_handler.handle_message("clear", session_id)
        )
        loop.close()
        
        emit('chat_cleared', {
            "timestamp": datetime.now().isoformat()
        })
        
        emit('bot_message', {
            "message": response_data["response"],
            "timestamp": response_data["timestamp"],
            "type": response_data["type"]
        })
        
    except Exception as e:
        logger.error(f"Error clearing chat: {str(e)}")
        emit('bot_message', {
            "message": "❌ Error clearing chat.",
            "timestamp": datetime.now().isoformat(),
            "type": "error"
        })

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    logger.info(f"Starting indici MCP Chatbot Web Interface")
    logger.info(f"Host: {config.web_interface_host}")
    logger.info(f"Port: {config.web_interface_port}")
    logger.info(f"Debug: {config.web_interface_debug}")
    
    # Start the web application
    socketio.run(
        app,
        host=config.web_interface_host,
        port=config.web_interface_port,
        debug=config.web_interface_debug,
        allow_unsafe_werkzeug=True
    )
