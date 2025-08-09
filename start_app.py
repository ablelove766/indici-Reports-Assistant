#!/usr/bin/env python3
"""
Simple script to start the Flask application.
"""

import sys
import os

# Add the web directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web'))

if __name__ == '__main__':
    try:
        print("Starting Flask application...")

        # Import the app module
        import app
        print("Flask app module imported successfully")

        # Get the Flask app and socketio instances
        flask_app = app.app
        socketio = app.socketio
        config = app.config

        print(f"Starting server on {config.web_interface_host}:{config.web_interface_port}")

        # Start the server explicitly
        socketio.run(
            flask_app,
            host=config.web_interface_host,
            port=config.web_interface_port,
            debug=config.web_interface_debug,
            allow_unsafe_werkzeug=True
        )

    except Exception as e:
        print(f"Error starting Flask app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
