#!/usr/bin/env python3
"""
test_gmail_auth.py - Simple Gmail Authentication Test

This script tests Gmail API authentication and helps debug connection issues.
"""

import os
import sys

def test_gmail_auth():
    """Test Gmail authentication step by step."""
    print("🔐 Testing Gmail Authentication")
    print("=" * 40)
    
    # Step 1: Check credentials file
    print("1. Checking credentials.json...")
    if not os.path.exists("credentials.json"):
        print("   ❌ credentials.json not found")
        print("   📋 Run 'python setup_gmail.py' for setup instructions")
        return False
    else:
        print("   ✅ credentials.json found")
    
    # Step 2: Check imports
    print("\n2. Checking imports...")
    try:
        from google_auth import get_gmail_creds
        from googleapiclient.discovery import build
        print("   ✅ Google API imports successful")
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("   💡 Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return False
    
    # Step 3: Test authentication
    print("\n3. Testing authentication...")
    try:
        creds = get_gmail_creds()
        print("   ✅ Authentication successful")
        
        # Check if token was created
        if os.path.exists("gmail_token.json"):
            print("   ✅ gmail_token.json created")
        
    except Exception as e:
        print(f"   ❌ Authentication failed: {e}")
        
        if "invalid_grant" in str(e):
            print("   🔧 Token expired - deleting gmail_token.json")
            try:
                if os.path.exists("gmail_token.json"):
                    os.remove("gmail_token.json")
                    print("   ✅ Deleted gmail_token.json - try again")
            except Exception:
                pass
        
        return False
    
    # Step 4: Test Gmail API
    print("\n4. Testing Gmail API...")
    try:
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        
        email_address = profile.get("emailAddress", "Unknown")
        messages_total = profile.get("messagesTotal", 0)
        
        print(f"   ✅ Gmail API connection successful")
        print(f"   📧 Email: {email_address}")
        print(f"   📊 Total messages: {messages_total}")
        
    except Exception as e:
        print(f"   ❌ Gmail API test failed: {e}")
        return False
    
    # Step 5: Test reading emails
    print("\n5. Testing email reading...")
    try:
        # Get a few recent emails
        result = service.users().messages().list(
            userId="me",
            maxResults=5,
            q="in:inbox"
        ).execute()
        
        messages = result.get("messages", [])
        print(f"   ✅ Found {len(messages)} recent emails")
        
        # Test reading one email if available
        if messages:
            msg_id = messages[0]["id"]
            msg = service.users().messages().get(userId="me", id=msg_id).execute()
            
            # Get subject
            headers = msg["payload"].get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            
            print(f"   📧 Sample email subject: {subject[:50]}...")
            
    except Exception as e:
        print(f"   ❌ Email reading test failed: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 Gmail authentication fully working!")
    print("\nNext steps:")
    print("1. Run: python test_email_radar.py")
    print("2. Start Email Radar with Discord bot")
    
    return True

if __name__ == "__main__":
    if test_gmail_auth():
        sys.exit(0)
    else:
        print("\n❌ Gmail authentication setup needed")
        print("💡 Run: python setup_gmail.py")
        sys.exit(1)
