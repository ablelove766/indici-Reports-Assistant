"""Flask web application for indici MCP Chatbot."""

import asyncio
import logging
import json
import traceback
from flask import Flask, render_template, request, jsonify, make_response
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

# Initialize SocketIO with Teams-compatible CORS
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

# Store active sessions
active_sessions = {}

# Teams-compatible CSP headers
def add_teams_headers(response):
    """Add headers required for Microsoft Teams integration."""
    # Content Security Policy for Teams iframe embedding
    csp_policy = (
        "default-src 'self' https://teams.microsoft.com https://*.teams.microsoft.com "
        "https://teams.live.com https://*.teams.live.com https://indici-reports-assistant.onrender.com; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net "
        "https://cdnjs.cloudflare.com https://teams.microsoft.com https://*.teams.microsoft.com "
        "https://res.cdn.office.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com "
        "https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https:; "
        "connect-src 'self' wss: ws: https://teams.microsoft.com https://*.teams.microsoft.com "
        "wss://indici-reports-assistant.onrender.com https://indici-reports-assistant.onrender.com; "
        "frame-ancestors https://teams.microsoft.com https://*.teams.microsoft.com "
        "https://teams.live.com https://*.teams.live.com; "
        "frame-src 'self' https://teams.microsoft.com https://*.teams.microsoft.com;"
    )

    response.headers['Content-Security-Policy'] = csp_policy
    response.headers['X-Frame-Options'] = 'ALLOWALL'  # Allow iframe embedding
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    return response

@app.after_request
def after_request(response):
    """Add security headers to all responses."""
    return add_teams_headers(response)

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
    # Check if running in Teams context
    teams_context = request.args.get('teams', 'false').lower() == 'true'
    return render_template('index.html', teams_mode=teams_context)

@app.route('/teams')
def teams_tab():
    """Microsoft Teams tab interface."""
    # Get configuration parameters
    view_mode = request.args.get('view', 'full')
    responsive_mode = request.args.get('responsive', 'auto')
    practice_id = request.args.get('practiceId', '')

    return render_template('index.html',
                         teams_mode=True,
                         view_mode=view_mode,
                         responsive_mode=responsive_mode,
                         practice_id=practice_id)

@app.route('/teams/config')
def teams_config():
    """Teams tab configuration page."""
    return render_template('teams_config.html')

@app.route('/teams/privacy')
def teams_privacy():
    """Teams privacy policy page."""
    return render_template('teams_privacy.html')

@app.route('/teams/terms')
def teams_terms():
    """Teams terms of use page."""
    return render_template('teams_terms.html')

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
        logger.error(f"Error traceback: {traceback.format_exc()}")
        # Return a basic status instead of error
        return jsonify({
            "status": "operational",
            "error": str(e),
            "configuration": {"basic": True},
            "performance": {"requests": 0, "errors": 0},
            "components": {"status": "unknown"}
        }), 200

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    try:
        session_id = request.sid
        client_info = {
            "connected_at": datetime.now(),
            "message_count": 0,
            "user_agent": request.headers.get('User-Agent', 'Unknown'),
            "remote_addr": request.remote_addr
        }
        active_sessions[session_id] = client_info

        logger.info(f"✅ Client connected: {session_id} from {request.remote_addr}")
        logger.info(f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}")

        # Send welcome message
        emit('bot_message', {
            "message": "👋 Welcome to the indici Reports Assistant! How can I help you today?",
            "timestamp": datetime.now().isoformat(),
            "type": "greeting"
        })

        logger.info(f"Welcome message sent to {session_id}")

    except Exception as e:
        logger.error(f"❌ Error in handle_connect: {e}")
        import traceback
        traceback.print_exc()

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
        
        logger.info(f"📨 Received message from {session_id}: '{message}'")
        logger.info(f"Session info: {active_sessions.get(session_id, 'Unknown')}")

        # Show typing indicator
        emit('bot_typing', {"typing": True})
        logger.info(f"🔄 Typing indicator sent to {session_id}")
        
        # Process message asynchronously
        def process_message():
            try:
                logger.info(f"🔄 Starting async message processing for {session_id}")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Handle the message
                logger.info(f"🤖 Calling chat_handler.handle_message...")
                response_data = loop.run_until_complete(
                    chat_handler.handle_message(message, session_id)
                )
                logger.info(f"✅ Chat handler response: {response_data}")

                loop.close()

                # Send response
                logger.info(f"📤 Sending response to {session_id}")
                socketio.emit('bot_typing', {"typing": False}, room=session_id)
                socketio.emit('bot_message', {
                    "message": response_data["response"],
                    "timestamp": response_data["timestamp"],
                    "type": response_data["type"],
                    "success": response_data["success"]
                }, room=session_id)
                logger.info(f"✅ Response sent successfully to {session_id}")
                
            except Exception as e:
                logger.error(f"❌ Error processing message for {session_id}: {str(e)}")
                import traceback
                traceback.print_exc()

                socketio.emit('bot_typing', {"typing": False}, room=session_id)
                socketio.emit('bot_message', {
                    "message": f"❌ Sorry, I encountered an error: {str(e)}",
                    "timestamp": datetime.now().isoformat(),
                    "type": "error",
                    "success": False
                }, room=session_id)
                logger.info(f"Error message sent to {session_id}")
        
        # Run in background thread
        socketio.start_background_task(process_message)
        
    except Exception as e:
        logger.error(f"❌ Error in handle_user_message for {session_id}: {str(e)}")
        import traceback
        traceback.print_exc()

        emit('bot_message', {
            "message": "❌ An unexpected error occurred. Please try again.",
            "timestamp": datetime.now().isoformat(),
            "type": "error"
        })
        logger.info(f"Main error message sent to {session_id}")

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
    try:
        logger.info(f"Starting indici MCP Chatbot Web Interface")
        logger.info(f"Host: {config.web_interface_host}")
        logger.info(f"Port: {config.web_interface_port}")
        logger.info(f"Debug: {config.web_interface_debug}")

        # Start the web application with SocketIO
        socketio.run(
            app,
            host=config.web_interface_host,
            port=config.web_interface_port,
            debug=config.web_interface_debug,
            allow_unsafe_werkzeug=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        import traceback
        traceback.print_exc()
        raise
