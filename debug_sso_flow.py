#!/usr/bin/env python3
"""
Debug SSO flow step by step
"""

import requests
import json
import jwt
import time
from datetime import datetime

def test_server_endpoints():
    """Test all server endpoints."""
    print("=" * 60)
    print("TESTING SERVER ENDPOINTS")
    print("=" * 60)
    
    endpoints = [
        "http://localhost:10000/",
        "http://localhost:10000/teams",
        "http://localhost:10000/teams/working-test",
        "http://localhost:10000/auth/token-exchange",
        "http://localhost:10000/test-logs"
    ]
    
    for endpoint in endpoints:
        try:
            if "token-exchange" in endpoint:
                # POST request for token exchange
                response = requests.post(endpoint, 
                                       json={"token": "test"}, 
                                       timeout=5)
            else:
                # GET request for others
                response = requests.get(endpoint, timeout=5)
            
            print(f"✅ {endpoint} → {response.status_code}")
            
        except Exception as e:
            print(f"❌ {endpoint} → ERROR: {e}")

def create_mock_teams_token():
    """Create a mock Teams token for testing."""
    print("\n" + "=" * 60)
    print("CREATING MOCK TEAMS TOKEN")
    print("=" * 60)
    
    # Create a payload that looks like what Teams would send
    payload = {
        "aud": "api://e2f9d05e-f417-47c8-9119-e8a7ecff07dd",
        "iss": "https://login.microsoftonline.com/82b5691e-b842-4527-b212-041c19c48d3e/v2.0",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "preferred_username": "test.user@f3technologies.com",
        "name": "Test User",
        "oid": "12345678-1234-1234-1234-123456789012",
        "tid": "82b5691e-b842-4527-b212-041c19c48d3e",
        "scp": "access_as_user",
        "sub": "12345678-1234-1234-1234-123456789012",
        "upn": "test.user@f3technologies.com",
        "email": "test.user@f3technologies.com"
    }
    
    print(f"Mock token payload:")
    print(f"  Audience: {payload['aud']}")
    print(f"  Issuer: {payload['iss']}")
    print(f"  User: {payload['preferred_username']}")
    print(f"  Tenant: {payload['tid']}")
    
    # Create unsigned token for testing (our server should handle this)
    mock_token = jwt.encode(payload, "secret", algorithm="HS256")
    print(f"  Token length: {len(mock_token)}")
    print(f"  Token preview: {mock_token[:50]}...")
    
    return mock_token

def test_token_validation():
    """Test token validation with mock token."""
    print("\n" + "=" * 60)
    print("TESTING TOKEN VALIDATION")
    print("=" * 60)
    
    mock_token = create_mock_teams_token()
    
    try:
        response = requests.post(
            "http://localhost:10000/auth/token-exchange",
            headers={
                "Content-Type": "application/json",
                "X-Teams-Token": mock_token
            },
            json={"token": mock_token},
            timeout=15
        )
        
        print(f"Token exchange status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response JSON: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response text: {response.text}")
            
        if response.status_code == 200:
            print("✅ TOKEN VALIDATION SUCCESSFUL!")
        else:
            print(f"❌ TOKEN VALIDATION FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Token validation error: {e}")

def test_azure_endpoints():
    """Test Azure AD endpoints directly."""
    print("\n" + "=" * 60)
    print("TESTING AZURE AD ENDPOINTS")
    print("=" * 60)
    
    tenant_id = "82b5691e-b842-4527-b212-041c19c48d3e"
    
    endpoints = [
        f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid_configuration",
        f"https://login.microsoftonline.com/{tenant_id}/.well-known/openid_configuration",
        f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys",
        f"https://login.microsoftonline.com/common/v2.0/.well-known/openid_configuration"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            print(f"✅ {endpoint} → {response.status_code}")
            
            if response.status_code == 200 and "openid_configuration" in endpoint:
                data = response.json()
                print(f"   Issuer: {data.get('issuer', 'Unknown')}")
                print(f"   JWKS URI: {data.get('jwks_uri', 'Unknown')}")
                
        except Exception as e:
            print(f"❌ {endpoint} → ERROR: {e}")

def check_teams_manifest():
    """Check Teams manifest configuration."""
    print("\n" + "=" * 60)
    print("CHECKING TEAMS MANIFEST")
    print("=" * 60)
    
    try:
        with open("teams/manifest.json", "r") as f:
            manifest = json.load(f)
        
        print(f"App ID: {manifest.get('id', 'Unknown')}")
        print(f"Package Name: {manifest.get('packageName', 'Unknown')}")
        print(f"Version: {manifest.get('version', 'Unknown')}")
        
        web_app_info = manifest.get('webApplicationInfo', {})
        print(f"Web App ID: {web_app_info.get('id', 'Unknown')}")
        print(f"Web App Resource: {web_app_info.get('resource', 'Unknown')}")
        
        # Check if configuration matches
        expected_client_id = "e2f9d05e-f417-47c8-9119-e8a7ecff07dd"
        expected_resource = f"api://{expected_client_id}"
        
        if web_app_info.get('id') == expected_client_id:
            print("✅ Web App ID matches client ID")
        else:
            print(f"❌ Web App ID mismatch: {web_app_info.get('id')} != {expected_client_id}")
            
        if web_app_info.get('resource') == expected_resource:
            print("✅ Resource URI matches expected")
        else:
            print(f"❌ Resource URI mismatch: {web_app_info.get('resource')} != {expected_resource}")
            
    except Exception as e:
        print(f"❌ Error reading manifest: {e}")

def main():
    """Main debugging function."""
    print("🔍 COMPREHENSIVE SSO DEBUGGING")
    print(f"⏰ Started at: {datetime.now()}")
    
    # Test 1: Server endpoints
    test_server_endpoints()
    
    # Test 2: Azure AD endpoints
    test_azure_endpoints()
    
    # Test 3: Teams manifest
    check_teams_manifest()
    
    # Test 4: Token validation
    test_token_validation()
    
    print("\n" + "=" * 60)
    print("🎯 DEBUGGING COMPLETE")
    print("=" * 60)
    
    print("\n📋 NEXT STEPS:")
    print("1. Check server logs for detailed error messages")
    print("2. Test the working test page in Teams")
    print("3. Verify the exact error message from Teams SSO")
    print("4. Check if the issue is in token request or token validation")

if __name__ == "__main__":
    main()
