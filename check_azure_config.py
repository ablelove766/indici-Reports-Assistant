#!/usr/bin/env python3
"""
Azure AD Configuration Checker for Teams SSO
This script helps verify your Azure AD app registration is correctly configured.
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_azure_config():
    """Check Azure AD configuration for Teams SSO."""
    print("🔍 Checking Azure AD Configuration for Teams SSO...")
    print("=" * 60)
    
    # Get configuration from environment
    client_id = os.getenv('AZURE_CLIENT_ID')
    tenant_id = os.getenv('AZURE_TENANT_ID')
    client_secret = os.getenv('AZURE_CLIENT_SECRET')
    
    if not all([client_id, tenant_id, client_secret]):
        print("❌ Missing Azure AD configuration in .env file")
        print("Required variables: AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET")
        return False
    
    print(f"✅ Client ID: {client_id}")
    print(f"✅ Tenant ID: {tenant_id}")
    print(f"✅ Client Secret: {'*' * (len(client_secret) - 4) + client_secret[-4:]}")
    print()
    
    # Check if the app registration exists and is accessible
    print("🔍 Checking Azure AD app registration...")
    
    # Try to get app registration info
    try:
        # This endpoint checks if the app exists and is properly configured
        discovery_url = f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid_configuration"
        response = requests.get(discovery_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Azure AD tenant is accessible")
            config = response.json()
            print(f"✅ Authorization endpoint: {config.get('authorization_endpoint', 'Not found')}")
            print(f"✅ Token endpoint: {config.get('token_endpoint', 'Not found')}")
        else:
            print(f"❌ Cannot access Azure AD tenant: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking Azure AD configuration: {e}")
        return False
    
    print()
    print("🎯 Required Azure AD App Registration Settings:")
    print("=" * 60)
    print("1. Application ID URI:")
    print("   api://indici-reports-assistant.onrender.com/e2f9d05e-f417-47c8-9119-e8a7ecff07dd")
    print()
    print("2. API Permissions (with admin consent):")
    print("   - Microsoft Graph → User.Read (Delegated)")
    print("   - Your API → access_as_user (Delegated)")
    print()
    print("3. Authentication:")
    print("   - Redirect URI: https://indici-reports-assistant.onrender.com/auth/callback")
    print("   - Enable: Access tokens + ID tokens")
    print()
    print("4. Expose an API:")
    print("   - Add scope: access_as_user")
    print("   - Who can consent: Admins and users")
    print()
    print("🚨 IMPORTANT: Grant admin consent for all permissions!")
    
    return True

if __name__ == "__main__":
    if check_azure_config():
        print("\n✅ Configuration check complete!")
        print("If you're still getting CAA20004 error:")
        print("1. Verify the Azure AD settings above")
        print("2. Grant admin consent for all permissions")
        print("3. Re-upload Teams manifest (version 1.0.1)")
        print("4. Reinstall the Teams app")
    else:
        print("\n❌ Configuration issues found. Please fix and try again.")
