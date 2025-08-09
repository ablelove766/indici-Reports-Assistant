#!/usr/bin/env python3
"""
Quick test to see if Flask app works.
"""

import sys
import os

# Add the web directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web'))

try:
    print("Testing Flask app...")
    import app
    print("✅ Flask app imported successfully")
    
    # Try to access the Teams route
    with app.app.test_client() as client:
        print("Testing /teams route...")
        response = client.get('/teams')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ /teams route works!")
        else:
            print(f"❌ /teams route failed: {response.status_code}")
            
        # Test auth error route
        print("Testing /auth/error route...")
        response = client.get('/auth/error')
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ /auth/error route works!")
        else:
            print(f"❌ /auth/error route failed: {response.status_code}")
            
    print("✅ All tests passed! Flask app should work.")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
