#!/usr/bin/env python3
"""
Create Teams app package with updated manifest
"""

import zipfile
import os
import json

def create_teams_package():
    """Create a Teams app package (.zip) with the updated manifest."""
    print("Creating Teams app package...")
    
    # Files to include in the package
    files_to_include = [
        "teams/manifest.json",
        "teams/teams/color.png",
        "teams/teams/outline.png"
    ]
    
    # Check if all files exist
    missing_files = []
    for file_path in files_to_include:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    # Create the zip package
    package_path = "teams/indici-reports-assistant.zip"
    
    try:
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in files_to_include:
                # Add file to zip with just the filename (not the full path)
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname)
                print(f"✅ Added {file_path} as {arcname}")
        
        print(f"✅ Teams package created: {package_path}")
        
        # Verify the package
        with zipfile.ZipFile(package_path, 'r') as zipf:
            files_in_zip = zipf.namelist()
            print(f"📦 Package contents: {files_in_zip}")
            
            # Verify manifest content
            with zipf.open('manifest.json') as manifest_file:
                manifest_data = json.loads(manifest_file.read().decode('utf-8'))
                print(f"📋 App ID: {manifest_data.get('id', 'Unknown')}")
                print(f"📋 App Name: {manifest_data.get('name', {}).get('short', 'Unknown')}")
                print(f"📋 Version: {manifest_data.get('version', 'Unknown')}")
                
                web_app_info = manifest_data.get('webApplicationInfo', {})
                print(f"📋 Web App ID: {web_app_info.get('id', 'Unknown')}")
                print(f"📋 Resource URI: {web_app_info.get('resource', 'Unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating package: {e}")
        return False

def main():
    """Main function."""
    print("=" * 60)
    print("TEAMS APP PACKAGE CREATOR")
    print("=" * 60)
    
    if create_teams_package():
        print("\n" + "=" * 60)
        print("✅ SUCCESS!")
        print("=" * 60)
        print("\n📋 NEXT STEPS:")
        print("1. Update Azure AD Application ID URI to:")
        print("   api://indici-reports-assistant.onrender.com/e2f9d05e-f417-47c8-9119-e8a7ecff07dd")
        print("\n2. Upload the new Teams package:")
        print("   - Go to Teams Admin Center or Teams Developer Portal")
        print("   - Upload: teams/indici-reports-assistant.zip")
        print("\n3. Test SSO again after both changes are made")
        print("=" * 60)
    else:
        print("\n❌ Failed to create Teams package")

if __name__ == "__main__":
    main()
