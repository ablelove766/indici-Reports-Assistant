#!/usr/bin/env python3
"""
Simple launcher for the Flask application.
"""

import sys
import os

# Add the web directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web'))

# Import and run the app
if __name__ == '__main__':
    try:
        print("Starting Flask application...")
        import app
        print("App module imported successfully")
    except Exception as e:
        print(f"Error importing app: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
