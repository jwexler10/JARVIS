#!/usr/bin/env python3
"""
setup_gmail.py - Gmail API Setup Helper

This script helps you set up Gmail API access for the Email Radar.
It will guide you through the Google Cloud Console setup and test the connection.
"""

import os
import json
import webbrowser
from pathlib import Path

def check_credentials():
    """Check if credentials.json exists."""
    return os.path.exists("credentials.json")

def check_existing_gmail_integration():
    """Check if Gmail is already working in other parts of JARVIS."""
    gmail_files = [
        "google_gmail.py",
        "google_auth.py", 
        "gmail_token.json",
        "oauth_credentials.json"
    ]
    
    existing_files = []
    for file in gmail_files:
        if os.path.exists(file):
            existing_files.append(file)
    
    return existing_files

def create_sample_credentials():
    """Create a sample credentials.json template."""
    sample_creds = {
        "installed": {
            "client_id": "your-client-id.googleusercontent.com",
            "project_id": "your-project-id",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": "your-client-secret",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    with open("credentials_template.json", "w") as f:
        json.dump(sample_creds, f, indent=2)
    
    print("📄 Created credentials_template.json as an example")

def setup_instructions():
    """Print detailed setup instructions."""
    print("""
🚀 Gmail API Setup Instructions

Step 1: Google Cloud Console Setup
==================================
1. Go to: https://console.cloud.google.com/
2. Create a new project or select existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"

Step 2: Create OAuth 2.0 Credentials
====================================
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Set Application type: "Desktop application"
4. Name it: "JARVIS Email Radar"
5. Download the JSON file as "credentials.json"

Step 3: Place Credentials File
==============================
1. Save the downloaded file as "credentials.json" in this directory:
   {current_dir}

Step 4: Test Authentication
===========================
1. Run: python test_gmail_auth.py
2. Follow the browser authentication flow
3. Grant permissions for Gmail access

Important Notes:
===============
- The first time you run this, it will open a browser for authentication
- You'll need to grant permissions to read/modify Gmail
- A gmail_token.json file will be created automatically
- Keep credentials.json secure and never share it

""".format(current_dir=os.getcwd()))

def test_gmail_connection():
    """Test if Gmail connection works."""
    try:
        from google_auth import get_gmail_creds
        from googleapiclient.discovery import build
        
        print("🔄 Testing Gmail connection...")
        creds = get_gmail_creds()
        service = build("gmail", "v1", credentials=creds)
        
        # Test API call
        result = service.users().getProfile(userId="me").execute()
        email_address = result.get("emailAddress", "Unknown")
        
        print(f"✅ Gmail connection successful!")
        print(f"📧 Connected to: {email_address}")
        return True
        
    except Exception as e:
        print(f"❌ Gmail connection failed: {e}")
        return False

def main():
    print("🎯 JARVIS Email Radar - Gmail Setup")
    print("=" * 50)
    
    # Check existing files
    existing_files = check_existing_gmail_integration()
    if existing_files:
        print("📁 Found existing Gmail integration files:")
        for file in existing_files:
            print(f"   ✅ {file}")
        print()
    
    # Check credentials
    if check_credentials():
        print("✅ credentials.json found")
        
        # Test connection
        if test_gmail_connection():
            print("\n🎉 Gmail is ready for Email Radar!")
            print("\nNext steps:")
            print("1. Run: python test_email_radar.py")
            print("2. Start Discord bot: python discord_bot.py")
        else:
            print("\n🔧 Authentication needs to be refreshed")
            try:
                # Delete token files to force re-auth
                token_files = ["gmail_token.json", "oauth_credentials.json"]
                for token_file in token_files:
                    if os.path.exists(token_file):
                        os.remove(token_file)
                        print(f"🗑️ Deleted {token_file}")
                
                print("🔄 Try running the test again to re-authenticate")
            except Exception as e:
                print(f"❌ Error cleaning tokens: {e}")
    else:
        print("❌ credentials.json not found")
        print("\n📋 You need to set up Gmail API credentials first")
        
        # Create template
        create_sample_credentials()
        
        # Show instructions
        setup_instructions()
        
        # Offer to open Google Cloud Console
        try:
            response = input("🌐 Open Google Cloud Console in browser? (y/n): ").lower()
            if response in ['y', 'yes']:
                webbrowser.open("https://console.cloud.google.com/")
                print("🌐 Opened Google Cloud Console")
        except KeyboardInterrupt:
            print("\n👋 Setup cancelled")

if __name__ == "__main__":
    main()
