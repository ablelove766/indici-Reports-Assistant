#!/usr/bin/env python3
"""
Script to help find the correct Azure AD tenant ID
"""

import requests
import json

def test_tenant_id(tenant_id):
    """Test if a tenant ID is valid."""
    print(f"[TEST] Testing tenant ID: {tenant_id}")
    
    url = f"https://login.microsoftonline.com/{tenant_id}/v2.0/.well-known/openid_configuration"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"[TEST] Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] Tenant is valid!")
            print(f"[INFO] Issuer: {data.get('issuer', 'Unknown')}")
            print(f"[INFO] Authorization endpoint: {data.get('authorization_endpoint', 'Unknown')}")
            return True
        else:
            print(f"[ERROR] Tenant not found (404) or other error")
            return False
            
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")
        return False

def find_tenant_by_domain(domain):
    """Try to find tenant by domain name."""
    print(f"[SEARCH] Searching for tenant by domain: {domain}")
    
    # Try common tenant discovery methods
    discovery_urls = [
        f"https://login.microsoftonline.com/{domain}/v2.0/.well-known/openid_configuration",
        f"https://login.microsoftonline.com/{domain}.onmicrosoft.com/v2.0/.well-known/openid_configuration"
    ]
    
    for url in discovery_urls:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                issuer = data.get('issuer', '')
                # Extract tenant ID from issuer URL
                if '/v2.0' in issuer:
                    tenant_id = issuer.split('/')[-2]
                    print(f"[FOUND] Tenant ID: {tenant_id}")
                    return tenant_id
        except:
            continue
    
    print(f"[NOT FOUND] Could not find tenant for domain: {domain}")
    return None

def main():
    """Main function to help find correct tenant."""
    print("=" * 60)
    print("AZURE AD TENANT ID FINDER")
    print("=" * 60)
    
    # Test your current tenant ID
    current_tenant = "82b5691e-b842-4527-b212-041c19c48d3e"
    print(f"\n1. Testing your current tenant ID:")
    if test_tenant_id(current_tenant):
        print("[SUCCESS] Your current tenant ID is working!")
        return current_tenant
    
    # Try to find by common domain names
    print(f"\n2. Trying to find tenant by domain names:")
    
    common_domains = [
        "f3technologies",
        "f3tech", 
        "indici",
        "f3technologies.com",
        "indici.com"
    ]
    
    for domain in common_domains:
        tenant_id = find_tenant_by_domain(domain)
        if tenant_id:
            print(f"[FOUND] Working tenant ID: {tenant_id}")
            return tenant_id
    
    print("\n" + "=" * 60)
    print("[ACTION REQUIRED] Could not find a working tenant ID")
    print("Please do the following:")
    print("1. Go to https://portal.azure.com")
    print("2. Click 'Azure Active Directory'")
    print("3. Click 'Overview'")
    print("4. Copy the 'Tenant ID' value")
    print("5. Update your .env file with the correct tenant ID")
    print("=" * 60)
    
    return None

if __name__ == "__main__":
    main()
