#!/usr/bin/env python3
"""
Verify Azure AD configuration and fix SSO issues
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_tenant_id():
    """Verify the tenant ID is correct and accessible."""
    tenant_id = os.getenv('AZURE_TENANT_ID')
    print(f"[VERIFY] Testing tenant ID: {tenant_id}")
    
    if not tenant_id:
        print("[ERROR] No AZURE_TENANT_ID found in environment")
        return False
    
    # Test multiple Azure AD endpoints
    test_urls = [
        f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid_configuration",
        f"https://login.microsoftonline.com/{tenant_id}/.well-known/openid_configuration",
        f"https://login.microsoftonline.com/{tenant_id}/discovery/v2.0/keys"
    ]
    
    for url in test_urls:
        try:
            print(f"[TEST] Testing: {url}")
            response = requests.get(url, timeout=10)
            print(f"[TEST] Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"[SUCCESS] Tenant ID is valid! Endpoint working: {url}")
                
                if 'openid_configuration' in url:
                    data = response.json()
                    print(f"[INFO] Issuer: {data.get('issuer', 'Unknown')}")
                    print(f"[INFO] Authorization endpoint: {data.get('authorization_endpoint', 'Unknown')}")
                    print(f"[INFO] Token endpoint: {data.get('token_endpoint', 'Unknown')}")
                
                return True
            else:
                print(f"[ERROR] Failed with status: {response.status_code}")
                
        except Exception as e:
            print(f"[ERROR] Request failed: {e}")
    
    print(f"[CRITICAL] Tenant ID {tenant_id} is NOT VALID")
    print("[ACTION] Please verify your tenant ID in Azure Portal:")
    print("1. Go to https://portal.azure.com")
    print("2. Azure Active Directory → Overview")
    print("3. Copy the correct 'Tenant ID'")
    
    return False

def verify_app_registration():
    """Verify the app registration configuration."""
    client_id = os.getenv('AZURE_CLIENT_ID')
    print(f"[VERIFY] Testing app registration: {client_id}")
    
    if not client_id:
        print("[ERROR] No AZURE_CLIENT_ID found in environment")
        return False
    
    # Test the application ID URI
    app_id_uri = f"api://{client_id}"
    print(f"[INFO] Expected Application ID URI: {app_id_uri}")
    print(f"[INFO] Expected scope: {app_id_uri}/access_as_user")
    
    print("[ACTION] Verify in Azure Portal:")
    print("1. App registrations → Dev-ind-chat-bot → Expose an API")
    print(f"2. Application ID URI should be: {app_id_uri}")
    print(f"3. Scope should be: access_as_user")
    print("4. API permissions should include:")
    print("   - Microsoft Graph → User.Read (Delegated)")
    print(f"   - Your API → {app_id_uri}/access_as_user (Delegated)")
    print("5. Both permissions should have 'Admin consent granted'")
    
    return True

def test_msal_initialization():
    """Test MSAL client initialization."""
    print("[VERIFY] Testing MSAL initialization...")
    
    try:
        from msal import ConfidentialClientApplication
        
        client_id = os.getenv('AZURE_CLIENT_ID')
        client_secret = os.getenv('AZURE_CLIENT_SECRET')
        tenant_id = os.getenv('AZURE_TENANT_ID')
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        
        print(f"[MSAL] Client ID: {client_id}")
        print(f"[MSAL] Tenant ID: {tenant_id}")
        print(f"[MSAL] Authority: {authority}")
        print(f"[MSAL] Client Secret: {'Present' if client_secret else 'Missing'}")
        
        if not all([client_id, client_secret, tenant_id]):
            print("[ERROR] Missing required configuration for MSAL")
            return False
        
        # Try to create MSAL app
        msal_app = ConfidentialClientApplication(
            client_id=client_id,
            client_credential=client_secret,
            authority=authority
        )
        
        print("[SUCCESS] MSAL client created successfully")
        
        # Test getting accounts (should work even without tokens)
        accounts = msal_app.get_accounts()
        print(f"[MSAL] Cached accounts: {len(accounts)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] MSAL initialization failed: {e}")
        return False

def create_test_token_payload():
    """Create a test token payload to verify our validation logic."""
    print("[TEST] Creating test token payload...")
    
    import jwt
    import time
    
    # Create a test payload that matches what Teams would send
    test_payload = {
        "aud": f"api://{os.getenv('AZURE_CLIENT_ID')}",
        "iss": f"https://login.microsoftonline.com/{os.getenv('AZURE_TENANT_ID')}/v2.0",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "preferred_username": "test.user@domain.com",
        "name": "Test User",
        "oid": "12345678-1234-1234-1234-123456789012",
        "tid": os.getenv('AZURE_TENANT_ID'),
        "scp": "access_as_user"
    }
    
    print(f"[TEST] Test payload created:")
    print(f"   Audience: {test_payload['aud']}")
    print(f"   Issuer: {test_payload['iss']}")
    print(f"   User: {test_payload['preferred_username']}")
    
    return test_payload

def main():
    """Main verification function."""
    print("=" * 70)
    print("AZURE AD CONFIGURATION VERIFICATION")
    print("=" * 70)
    
    success = True
    
    # Test 1: Verify tenant ID
    print("\n1. VERIFYING TENANT ID")
    print("-" * 30)
    if not verify_tenant_id():
        success = False
        print("[CRITICAL] Tenant ID verification failed!")
        print("[ACTION] Fix your tenant ID before proceeding")
    
    # Test 2: Verify app registration
    print("\n2. VERIFYING APP REGISTRATION")
    print("-" * 30)
    verify_app_registration()
    
    # Test 3: Test MSAL
    print("\n3. TESTING MSAL INITIALIZATION")
    print("-" * 30)
    if not test_msal_initialization():
        success = False
    
    # Test 4: Create test payload
    print("\n4. TESTING TOKEN VALIDATION LOGIC")
    print("-" * 30)
    create_test_token_payload()
    
    print("\n" + "=" * 70)
    
    if success:
        print("[SUCCESS] Basic configuration looks good!")
        print("[NEXT] The issue is likely:")
        print("1. Missing admin consent for API permissions")
        print("2. Incorrect Application ID URI in Azure AD")
        print("3. Teams manifest not matching Azure AD configuration")
        
        print("\n[IMMEDIATE ACTIONS]:")
        print("1. Verify Application ID URI in Azure AD matches: api://e2f9d05e-f417-47c8-9119-e8a7ecff07dd")
        print("2. Grant admin consent for both API permissions")
        print("3. Test SSO using the working test page")
        
    else:
        print("[ERROR] Critical configuration issues found!")
        print("[ACTION] Fix the tenant ID and configuration issues first")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
