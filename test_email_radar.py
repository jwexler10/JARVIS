#!/usr/bin/env python3
"""
test_email_radar.py - Test script for Email Radar functionality

This script tests the email radar components without starting Discord bot.
Use this to verify Gmail API access and scoring logic.
"""

import asyncio
import json
from email_radar import EmailRadar

async def test_email_radar():
    """Test email radar functionality."""
    print("🚀 Testing Email Radar System")
    print("=" * 50)
    
    try:
        # Initialize radar without Discord bot
        radar = EmailRadar()
        
        # Test 1: Check service initialization
        print("\n1. Testing service initialization...")
        if radar.gmail_service:
            print("   ✅ Gmail service initialized")
        else:
            print("   ❌ Gmail service failed")
            return
        
        if radar.openai_client:
            print("   ✅ OpenAI client initialized")
        else:
            print("   ⚠️ OpenAI client not available")
        
        # Test 2: Test Gmail API access
        print("\n2. Testing Gmail API access...")
        try:
            result = radar.gmail_service.users().messages().list(
                userId="me",
                q="is:unread in:inbox",
                maxResults=5
            ).execute()
            
            messages = result.get("messages", [])
            print(f"   ✅ Found {len(messages)} unread emails")
            
            # Test processing one email if available
            if messages:
                print(f"\n3. Testing email processing...")
                test_message_id = messages[0]["id"]
                
                # Get email details
                message = radar.gmail_service.users().messages().get(
                    userId="me", 
                    id=test_message_id,
                    format="full"
                ).execute()
                
                # Extract data
                email_data = radar._extract_email_data(message)
                print(f"   📧 Sample email:")
                print(f"      From: {email_data['sender_name']} ({email_data['sender_email']})")
                print(f"      Subject: {email_data['subject'][:50]}...")
                
                # Test scoring
                score = radar._calculate_relevance_score(email_data)
                print(f"      Relevance Score: {score}/100")
                
                # Test summarization if OpenAI available
                if radar.openai_client:
                    print(f"   🤖 Generating summary...")
                    summary = await radar._generate_summary(email_data)
                    print(f"      Summary: {summary[:100]}...")
                else:
                    print(f"   ⚠️ Skipping summary (no OpenAI key)")
                
            else:
                print("   📭 No unread emails to test with")
        
        except Exception as e:
            print(f"   ❌ Gmail API access failed: {e}")
            return
        
        # Test 3: Test whitelist functionality
        print("\n4. Testing whitelist functionality...")
        radar.add_sender_to_whitelist("test@example.com", 95)
        stats = radar.get_stats()
        print(f"   ✅ Whitelist size: {stats['whitelist_size']}")
        
        radar.remove_sender_from_whitelist("test@example.com")
        stats = radar.get_stats()
        print(f"   ✅ After removal: {stats['whitelist_size']}")
        
        # Test 4: Show current stats
        print("\n5. Email Radar Statistics:")
        stats = radar.get_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        print("\n" + "=" * 50)
        print("✅ Email Radar test completed successfully!")
        print("\nNext steps:")
        print("1. Update Discord channel ID in email_radar.py")
        print("2. Start Discord bot: python discord_bot.py")
        print("3. Use 'email radar' commands in Discord DM")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure credentials.json exists")
        print("2. Run 'python google_gmail.py' first to authenticate")
        print("3. Check Gmail API is enabled in Google Cloud Console")

if __name__ == "__main__":
    asyncio.run(test_email_radar())
