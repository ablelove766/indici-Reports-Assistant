"""Flask web application for indici MCP Chatbot."""

import asyncio
import logging
import json
import traceback
from flask import Flask, render_template, request, jsonify, make_response, session, g
from flask_socketio import SocketIO, emit
from datetime import datetime
try:
    from flask_session import Session
    FLASK_SESSION_AVAILABLE = True
except ImportError:
    FLASK_SESSION_AVAILABLE = False
    print("⚠️ Flask-Session not available, using default session management")
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.config import config
from chatbot.chat_handler import chat_handler
from chatbot.mcp_client import mcp_client
from web.auth import auth_manager, require_teams_auth, get_current_user, get_teams_token

# Configure logging for production (Render.com compatible)
def setup_production_logging():
    """Setup logging that works on Render.com and locally."""
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler (works on Render.com)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set specific loggers to appropriate levels
    logging.getLogger('werkzeug').setLevel(logging.INFO)
    logging.getLogger('socketio').setLevel(logging.INFO)
    logging.getLogger('engineio').setLevel(logging.INFO)
    logging.getLogger('teams_sso').setLevel(logging.DEBUG)  # Our SSO logger

    return logging.getLogger(__name__)

logger = setup_production_logging()
logger.info("[FLASK] Flask application logging initialized for production")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'indici-mcp-chatbot-secret-key'

# Configure Flask-Session for Teams SSO (if available)
if FLASK_SESSION_AVAILABLE:
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'indici_teams_'
    Session(app)
else:
    # Use default Flask session management
    app.config['SESSION_PERMANENT'] = False

# Initialize SocketIO with Teams-compatible CORS
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

# Store active sessions with user context
active_sessions = {}
authenticated_users = {}  # Store authenticated user sessions

# Teams-compatible CSP headers
def add_teams_headers(response):
    """Add headers required for Microsoft Teams integration with SSO support."""
    # Content Security Policy for Teams iframe embedding with SSO support
    csp_policy = (
        "default-src 'self' https://teams.microsoft.com https://*.teams.microsoft.com "
        "https://teams.live.com https://*.teams.live.com https://indici-reports-assistant.onrender.com "
        "https://login.microsoftonline.com https://*.login.microsoftonline.com "
        "https://graph.microsoft.com https://*.graph.microsoft.com; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net "
        "https://cdnjs.cloudflare.com https://teams.microsoft.com https://*.teams.microsoft.com "
        "https://res.cdn.office.net https://login.microsoftonline.com; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com "
        "https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
        "img-src 'self' data: https: https://graph.microsoft.com; "
        "connect-src 'self' wss: ws: https://teams.microsoft.com https://*.teams.microsoft.com "
        "wss://indici-reports-assistant.onrender.com https://indici-reports-assistant.onrender.com "
        "https://login.microsoftonline.com https://*.login.microsoftonline.com "
        "https://graph.microsoft.com https://*.graph.microsoft.com; "
        "frame-ancestors https://teams.microsoft.com https://*.teams.microsoft.com "
        "https://teams.live.com https://*.teams.live.com; "
        "frame-src 'self' https://teams.microsoft.com https://*.teams.microsoft.com "
        "https://login.microsoftonline.com;"
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
    # Log Teams access for debugging
    print("[RENDER] Teams tab accessed", flush=True)
    logger.info("[TEAMS] Teams tab accessed")
    logger.info(f"[TEAMS] User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    logger.info(f"[TEAMS] Request URL: {request.url}")
    logger.info(f"[TEAMS] Request args: {dict(request.args)}")

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

@app.route('/teams/debug')
def teams_debug():
    """Microsoft Teams SSO debug page."""
    return render_template('teams_debug.html')

@app.route('/teams/sso-test')
def teams_sso_test():
    """Microsoft Teams SSO step-by-step test page."""
    return render_template('teams_sso_test.html')

@app.route('/teams/force-sso')
def teams_force_sso():
    """Force Teams SSO with aggressive initialization."""
    print("[RENDER] Force SSO page accessed", flush=True)
    logger.info("[TEAMS] Force SSO page accessed")
    return render_template('index.html', teams_mode=True, force_sso=True)

@app.route('/teams/simple-test')
def teams_simple_test():
    """Simple Teams SSO test page."""
    print("[RENDER] Simple SSO test page accessed", flush=True)
    logger.info("[TEAMS] Simple SSO test page accessed")
    return render_template('teams_simple_test.html')

@app.route('/teams/working-test')
def teams_working_test():
    """Working Teams SSO test page."""
    print("[RENDER] Working SSO test page accessed", flush=True)
    logger.info("[TEAMS] Working SSO test page accessed")
    return render_template('sso_working_test.html')

@app.route('/test-logs')
def test_logs():
    """Test route to verify logging works on Render.com."""
    print("🧪 [RENDER] Test logs route called", flush=True)
    logger.info("🧪 Test logs route called")
    logger.debug("🧪 Debug level log")
    logger.warning("🧪 Warning level log")
    logger.error("🧪 Error level log")

    return jsonify({
        "message": "Test logs generated",
        "timestamp": datetime.now().isoformat(),
        "azure_config": {
            "client_id": config.azure_client_id,
            "tenant_id": config.azure_tenant_id,
            "teams_sso_enabled": config.teams_enable_sso
        }
    })

@app.route('/teams/privacy')
def teams_privacy():
    """Teams privacy policy page."""
    return render_template('teams_privacy.html')

@app.route('/teams/terms')
def teams_terms():
    """Teams terms of use page."""
    return render_template('teams_terms.html')

# ============================================================================
# MICROSOFT TEAMS SSO AUTHENTICATION ROUTES
# ============================================================================

@app.route('/auth/login')
def auth_login():
    """Initiate Teams SSO login flow."""
    try:
        # Build authorization URL
        auth_url = auth_manager.msal_app.get_authorization_request_url(
            scopes=[config.azure_scope],
            redirect_uri=config.get("azure_ad.redirect_uri", "https://indici-reports-assistant.onrender.com/auth/callback")
        )

        return jsonify({
            "auth_url": auth_url,
            "success": True
        })

    except Exception as e:
        logger.error(f"Error initiating login: {e}")
        return jsonify({
            "error": "Failed to initiate login",
            "success": False
        }), 500

@app.route('/auth/callback')
def auth_callback():
    """Handle Teams SSO callback."""
    try:
        # Get authorization code from query parameters
        code = request.args.get('code')
        if not code:
            return jsonify({"error": "Authorization code not provided"}), 400

        # Exchange code for token
        result = auth_manager.msal_app.acquire_token_by_authorization_code(
            code,
            scopes=[config.azure_scope],
            redirect_uri=config.get("azure_ad.redirect_uri", "https://indici-reports-assistant.onrender.com/auth/callback")
        )

        if "access_token" in result:
            # Store token in session
            session['access_token'] = result['access_token']
            session['user_info'] = result.get('id_token_claims', {})

            return jsonify({
                "success": True,
                "user": result.get('id_token_claims', {})
            })
        else:
            logger.error(f"Token acquisition failed: {result.get('error_description', 'Unknown error')}")
            return jsonify({
                "error": "Failed to acquire token",
                "success": False
            }), 400

    except Exception as e:
        logger.error(f"Error in auth callback: {e}")
        return jsonify({
            "error": "Authentication callback failed",
            "success": False
        }), 500

@app.route('/auth/token-exchange', methods=['POST'])
def token_exchange():
    """Exchange Teams token for application token (On-Behalf-Of flow)."""
    # Force immediate log output
    print("[RENDER] Token exchange endpoint called", flush=True)
    logger.info("[TOKEN] Token exchange endpoint called")
    logger.debug(f"   Request headers: {dict(request.headers)}")
    logger.debug(f"   Request method: {request.method}")
    logger.debug(f"   Request URL: {request.url}")
    logger.debug(f"   Request remote addr: {request.remote_addr}")

    # Also log to stdout directly for Render.com
    print(f"[RENDER] Request URL: {request.url}", flush=True)
    print(f"[RENDER] Request method: {request.method}", flush=True)
    print(f"[RENDER] Request headers: {dict(request.headers)}", flush=True)

    try:
        data = request.get_json()
        print(f"🔍 [RENDER] Request data keys: {list(data.keys()) if data else 'No data'}", flush=True)
        logger.debug(f"   Request data keys: {list(data.keys()) if data else 'No data'}")

        teams_token = data.get('token') if data else None

        if not teams_token:
            print("❌ [RENDER] No Teams token provided in request", flush=True)
            logger.error("❌ No Teams token provided in request")
            return jsonify({"error": "Teams token required"}), 400

        print(f"✅ [RENDER] Teams token received (length: {len(teams_token)})", flush=True)
        logger.info(f"   Teams token received (first 50 chars): {teams_token[:50]}...")

        # Validate Teams token
        print("🔍 [RENDER] Step 1: Validating Teams token...", flush=True)
        logger.info("🔍 Step 1: Validating Teams token...")
        user_payload = auth_manager.validate_teams_token(teams_token)
        if not user_payload:
            print("❌ [RENDER] Teams token validation failed", flush=True)
            logger.error("❌ Teams token validation failed")
            return jsonify({"error": "Invalid Teams token"}), 401

        print(f"✅ [RENDER] Teams token validated for user: {user_payload.get('preferred_username', 'Unknown')}", flush=True)
        logger.info(f"✅ Teams token validated for user: {user_payload.get('preferred_username', 'Unknown')}")

        # Exchange for Graph token
        print("🔄 [RENDER] Step 2: Exchanging Teams token for Graph token...", flush=True)
        logger.info("🔄 Step 2: Exchanging Teams token for Graph token...")
        graph_token = auth_manager.exchange_token_for_graph_token(teams_token)
        if not graph_token:
            print("❌ [RENDER] Token exchange failed - this is likely the CAA20004 error", flush=True)
            logger.error("❌ Token exchange failed - this is likely the CAA20004 error")
            return jsonify({
                "error": "Token exchange failed",
                "details": "This is likely due to missing admin consent. Check Azure AD app permissions."
            }), 500

        print("✅ [RENDER] Graph token obtained successfully", flush=True)
        logger.info("✅ Graph token obtained successfully")

        # Get user info from Graph
        logger.info("🔄 Step 3: Getting user info from Microsoft Graph...")
        user_info = auth_manager.get_user_info_from_graph(graph_token)
        if not user_info:
            logger.error("❌ Failed to get user info from Graph API")
            return jsonify({"error": "Failed to get user info"}), 500

        logger.info(f"✅ User info obtained: {user_info.get('displayName', 'Unknown')}")

        # Store in session
        logger.info("💾 Storing tokens and user info in session...")
        session['access_token'] = graph_token
        session['user_info'] = user_info
        session['teams_token'] = teams_token

        logger.info("✅ Token exchange completed successfully!")
        return jsonify({
            "success": True,
            "user": {
                "id": user_info.get("id"),
                "displayName": user_info.get("displayName"),
                "userPrincipalName": user_info.get("userPrincipalName"),
                "mail": user_info.get("mail")
            }
        })

    except Exception as e:
        logger.error(f"❌ Exception in token exchange: {e}")
        logger.error(f"   Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"   Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": "Token exchange failed",
            "success": False,
            "details": str(e)
        }), 500

@app.route('/auth/user')
def get_user():
    """Get current authenticated user information."""
    try:
        user_info = session.get('user_info')
        if not user_info:
            return jsonify({"error": "Not authenticated"}), 401

        return jsonify({
            "success": True,
            "user": {
                "id": user_info.get("id"),
                "displayName": user_info.get("displayName"),
                "userPrincipalName": user_info.get("userPrincipalName"),
                "mail": user_info.get("mail")
            }
        })

    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return jsonify({
            "error": "Failed to get user info",
            "success": False
        }), 500

@app.route('/auth/logout', methods=['POST'])
def auth_logout():
    """Logout user and clear session."""
    try:
        session.clear()
        return jsonify({
            "success": True,
            "message": "Logged out successfully"
        })

    except Exception as e:
        logger.error(f"Error during logout: {e}")
        return jsonify({
            "error": "Logout failed",
            "success": False
        }), 500

@app.route('/auth/status')
def auth_status():
    """Get current authentication status."""
    try:
        user_info = session.get('user_info')
        access_token = session.get('access_token')

        return jsonify({
            "authenticated": bool(user_info and access_token),
            "user": user_info if user_info else None,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Error getting auth status: {e}")
        return jsonify({
            "authenticated": False,
            "error": str(e)
        }), 500

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
            "remote_addr": request.remote_addr,
            "authenticated": False,
            "user_context": None
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

@socketio.on('user_authenticated')
def handle_user_authenticated(data):
    """Handle user authentication event from Teams SSO."""
    try:
        session_id = request.sid
        user_data = data.get('user', {})

        logger.info(f"🔐 User authenticated: {session_id} - {user_data.get('displayName', 'Unknown')}")

        # Update session with user context
        if session_id in active_sessions:
            active_sessions[session_id]["authenticated"] = True
            active_sessions[session_id]["user_context"] = user_data
            active_sessions[session_id]["authenticated_at"] = datetime.now()

        # Store in authenticated users
        authenticated_users[session_id] = {
            "user": user_data,
            "authenticated_at": datetime.now(),
            "session_id": session_id
        }

        # Send authentication confirmation
        emit('auth_confirmed', {
            "success": True,
            "user": user_data,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"Authentication confirmed for {session_id}")

    except Exception as e:
        logger.error(f"❌ Error handling user authentication: {e}")
        emit('auth_error', {
            "error": "Authentication processing failed",
            "timestamp": datetime.now().isoformat()
        })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    session_id = request.sid

    # Clean up active sessions
    if session_id in active_sessions:
        user_context = active_sessions[session_id].get("user_context")
        if user_context:
            logger.info(f"👤 Authenticated user disconnected: {user_context.get('displayName', 'Unknown')}")
        del active_sessions[session_id]

    # Clean up authenticated users
    if session_id in authenticated_users:
        del authenticated_users[session_id]

    logger.info(f"Client disconnected: {session_id}")

@socketio.on('user_message')
def handle_user_message(data):
    """Handle incoming user message."""
    try:
        session_id = request.sid
        message = data.get('message', '').strip()
        user_context = data.get('userContext')
        is_authenticated = data.get('isAuthenticated', False)

        if not message:
            emit('bot_message', {
                "message": "❌ Please enter a message.",
                "timestamp": datetime.now().isoformat(),
                "type": "error"
            })
            return

        # Update session stats and user context
        if session_id in active_sessions:
            active_sessions[session_id]["message_count"] += 1
            if user_context:
                active_sessions[session_id]["user_context"] = user_context
                active_sessions[session_id]["authenticated"] = is_authenticated

        logger.info(f"📨 Received message from {session_id}: '{message}'")
        if user_context:
            logger.info(f"👤 User: {user_context.get('displayName', 'Unknown')} ({user_context.get('userPrincipalName', 'Unknown')})")
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
        # Force immediate output for Render.com
        print("[RENDER] Starting indici MCP Chatbot Web Interface...", flush=True)
        print(f"[RENDER] Host: {config.web_interface_host}", flush=True)
        print(f"[RENDER] Port: {config.web_interface_port}", flush=True)
        print(f"[RENDER] Debug: {config.web_interface_debug}", flush=True)
        print(f"[RENDER] Teams SSO enabled: {config.teams_enable_sso}", flush=True)
        print(f"[RENDER] Azure Client ID: {config.azure_client_id}", flush=True)
        print(f"[RENDER] Azure Tenant ID: {config.azure_tenant_id}", flush=True)

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
