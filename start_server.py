#!/usr/bin/env python3
"""Simple server starter script"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Starting server...")
    from web.app import app, socketio
    print("App imported successfully")
    
    print("Starting SocketIO server on 0.0.0.0:10000...")
    socketio.run(
        app,
        host='0.0.0.0',
        port=10000,
        debug=True,
        allow_unsafe_werkzeug=True
    )
except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()
