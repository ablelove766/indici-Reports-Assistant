#!/usr/bin/env python3
"""
Debug script for Teams SSO issues
Run this to get detailed logs about your SSO configuration and token exchange
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sso_debug_detailed.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('sso_debug')

def check_environment():
    """Check environment configuration."""
    logger.info("🔧 Checking Environment Configuration...")
    
    required_vars = [
        'AZURE_CLIENT_ID',
        'AZURE_CLIENT_SECRET', 
        'AZURE_TENANT_ID',
        'AZURE_AUTHORITY',
        'AZURE_SCOPE',
        'TEAMS_APP_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'SECRET' in var:
                logger.info(f"   ✅ {var}: {'*' * (len(value) - 4) + value[-4:]}")
            else:
                logger.info(f"   ✅ {var}: {value}")
        else:
            logger.error(f"   ❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    return True

def check_azure_endpoints():
    """Check Azure AD endpoints accessibility."""
    logger.info("🌐 Checking Azure AD Endpoints...")
    
    tenant_id = os.getenv('AZURE_TENANT_ID')
    if not tenant_id:
        logger.error("❌ No tenant ID available")
        return False
    
    import requests
    
    endpoints = [
        f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid_configuration",
        f"https://login.microsoftonline.com/{tenant_id}/.well-known/openid_configuration"
    ]
    
    for endpoint in endpoints:
        try:
            logger.info(f"   Testing: {endpoint}")
            response = requests.get(endpoint, timeout=10)
            if response.status_code == 200:
                logger.info(f"   ✅ Accessible: {endpoint}")
                config = response.json()
                logger.info(f"   Authorization endpoint: {config.get('authorization_endpoint')}")
                logger.info(f"   Token endpoint: {config.get('token_endpoint')}")
                return True
            else:
                logger.warning(f"   ⚠️ Status {response.status_code}: {endpoint}")
        except Exception as e:
            logger.error(f"   ❌ Error accessing {endpoint}: {e}")
    
    return False

def check_app_registration():
    """Check Azure AD app registration details."""
    logger.info("🔍 Azure AD App Registration Checklist...")
    
    client_id = os.getenv('AZURE_CLIENT_ID')
    tenant_id = os.getenv('AZURE_TENANT_ID')
    
    logger.info("📋 Required Azure AD Configuration:")
    logger.info(f"   App Registration URL: https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/{client_id}")
    logger.info("")
    logger.info("🔹 Overview:")
    logger.info(f"   Application (client) ID: {client_id}")
    logger.info(f"   Directory (tenant) ID: {tenant_id}")
    logger.info("")
    logger.info("🔹 Expose an API:")
    logger.info(f"   Application ID URI: api://indici-reports-assistant.onrender.com/{client_id}")
    logger.info("   Scopes: access_as_user (Delegated)")
    logger.info("")
    logger.info("🔹 API permissions:")
    logger.info("   - Microsoft Graph → User.Read (Delegated) ✅ Admin consent required")
    logger.info("   - Your API → access_as_user (Delegated) ✅ Admin consent required")
    logger.info("")
    logger.info("🔹 Authentication:")
    logger.info("   - Redirect URI: https://indici-reports-assistant.onrender.com/auth/callback")
    logger.info("   - Implicit grant: ✅ Access tokens, ✅ ID tokens")
    logger.info("")
    logger.info("🚨 CRITICAL: Both permissions must have admin consent granted!")

def main():
    """Main debug function."""
    logger.info("🚀 Starting Teams SSO Debug Session...")
    logger.info("=" * 60)
    
    # Check environment
    if not check_environment():
        logger.error("❌ Environment check failed")
        return
    
    # Check Azure endpoints
    if not check_azure_endpoints():
        logger.error("❌ Azure endpoints check failed")
        return
    
    # Show app registration checklist
    check_app_registration()
    
    logger.info("")
    logger.info("🎯 Next Steps to Fix CAA20004:")
    logger.info("1. Go to Azure Portal → App registrations → Your app")
    logger.info("2. API permissions → Grant admin consent for F3Technologies")
    logger.info("3. Verify both permissions show 'Granted for F3Technologies'")
    logger.info("4. Re-upload Teams manifest (use manifest_simple.json)")
    logger.info("5. Reinstall Teams app")
    logger.info("6. Test SSO authentication")
    logger.info("")
    logger.info("📊 Debug logs saved to: sso_debug_detailed.log")
    logger.info("🔄 Run your app and check the logs for detailed token exchange info")

if __name__ == "__main__":
    main()
