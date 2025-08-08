#!/usr/bin/env python3
"""
Debug startup script to see what's happening
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Main startup function with detailed logging."""
    print("[DEBUG] Starting debug startup...")
    
    try:
        # Add project root to path
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        print("[DEBUG] Importing modules...")
        from mcp_server.config import config
        from web.app import app, socketio
        
        print("[DEBUG] Configuration:")
        print(f"   Host: {config.web_interface_host}")
        print(f"   Port: {config.web_interface_port}")
        print(f"   Debug: {config.web_interface_debug}")
        print(f"   Teams SSO: {config.teams_enable_sso}")
        
        print("[DEBUG] Starting Flask-SocketIO server...")
        socketio.run(
            app,
            host=config.web_interface_host,
            port=config.web_interface_port,
            debug=False,  # Disable debug to avoid double startup
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("[DEBUG] Server stopped by user")
    except Exception as e:
        print(f"[ERROR] Startup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
