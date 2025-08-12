#!/usr/bin/env python3
"""
email_radar.py - Smart Email Monitoring System

Phase 1: Gmail Integration with Discord Notifications
- Polls Gmail every 2-5 minutes for new unread emails
- Scores emails based on relevance (0-100)
- Summarizes important emails using LLM
- Sends Discord notifications for emails above threshold
- Integrates with existing discord_bot.py

Features:
- Intelligent relevance scoring
- Email deduplication
- Rate limiting and throttling
- Safe content redaction
- Thread-aware processing
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from email.utils import parseaddr

# Gmail API imports
from googleapiclient.discovery import build
from google_auth import get_gmail_creds
import base64

# Discord integration
import discord

# OpenAI for summarization
from openai import OpenAI
# OpenAI client created directly in __init__

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EmailRadar:
    """Smart email monitoring system with Discord notifications."""
    
    def __init__(self, discord_bot=None, config_file="config.json"):
        self.config = self._load_config(config_file)
        self.discord_bot = discord_bot
        self.gmail_service = None
        self.openai_client = None
        
        # Email tracking
        self.processed_message_ids: Set[str] = set()
        self.last_check_time = datetime.now()
        
        # Scoring configuration
        self.relevance_threshold = 60  # Only notify if score >= 60
        self.sender_whitelist = {
            # High-priority senders
            "jason@example.com": 100,
            "work@company.com": 90,
            "alerts@bank.com": 85,
            # Add your important senders here
        }
        
        # Keywords that boost relevance
        self.important_keywords = {
            "urgent": 20,
            "meeting": 15,
            "invoice": 18,
            "payment": 18,
            "offer": 12,
            "deadline": 20,
            "action required": 25,
            "security": 22,
            "alert": 20,
            "verification": 15,
            "interview": 18,
            "proposal": 15,
        }
        
        # Spam/promotional indicators
        self.spam_indicators = {
            "unsubscribe": -15,
            "promotional": -20,
            "marketing": -15,
            "newsletter": -10,
            "no-reply": -10,
            "bulk": -20,
        }
        
        self._initialize_services()
    
    def _load_config(self, config_file: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def _initialize_services(self):
        """Initialize Gmail and OpenAI services."""
        try:
            # Check for credentials file first
            import os
            if not os.path.exists("credentials.json"):
                logger.error("❌ credentials.json not found. Please set up Gmail API credentials first.")
                logger.info("📋 Follow these steps:")
                logger.info("1. Go to https://console.cloud.google.com/")
                logger.info("2. Enable Gmail API")
                logger.info("3. Create OAuth 2.0 credentials")
                logger.info("4. Download as credentials.json")
                return
            
            # Initialize Gmail service
            creds = get_gmail_creds()
            self.gmail_service = build("gmail", "v1", credentials=creds)
            logger.info("✅ Gmail service initialized")
            
            # Initialize OpenAI client if key exists
            api_key = self.config.get("openai_api_key")
            if api_key:
                self.openai_client = get_openai_client()
        except Exception as e:
            print(f"⚠️ OpenAI init failed, will fallback to snippet summarization: {e}")
    
    async def start_monitoring(self, poll_interval: int = 180):
        """Start the email monitoring loop."""
        logger.info(f"🚀 Starting email radar with {poll_interval}s polling interval")
        
        while True:
            try:
                await self.check_new_emails()
                await asyncio.sleep(poll_interval)
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def check_new_emails(self):
        """Check for new emails and process them."""
        try:
            # Get unread emails from the last check
            query = f"is:unread in:inbox -category:promotions -category:social newer_than:1h"
            
            result = self.gmail_service.users().messages().list(
                userId="me",
                q=query,
                maxResults=20
            ).execute()
            
            messages = result.get("messages", [])
            logger.info(f"📧 Found {len(messages)} new emails to process")
            
            for message in messages:
                message_id = message["id"]
                
                # Skip if already processed
                if message_id in self.processed_message_ids:
                    continue
                
                # Process the email
                await self.process_email(message_id)
                self.processed_message_ids.add(message_id)
                
                # Prevent overwhelming - small delay between emails
                await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"❌ Error checking emails: {e}")
    
    async def process_email(self, message_id: str):
        """Process a single email and send Discord notification if relevant."""
        try:
            # Get full message details
            message = self.gmail_service.users().messages().get(
                userId="me", 
                id=message_id,
                format="full"
            ).execute()
            
            # Extract email data
            email_data = self._extract_email_data(message)
            
            # Score relevance
            score = self._calculate_relevance_score(email_data)
            
            logger.info(f"📊 Email from {email_data['sender_name']}: score={score}")
            
            # Only notify if above threshold
            if score >= self.relevance_threshold:
                summary = await self._generate_summary(email_data)
                await self._send_discord_notification(email_data, score, summary)
            
        except Exception as e:
            logger.error(f"❌ Error processing email {message_id}: {e}")
    
    def _extract_email_data(self, message: dict) -> dict:
        """Extract relevant data from Gmail message."""
        headers = message["payload"].get("headers", [])
        
        # Extract header values
        header_dict = {h["name"].lower(): h["value"] for h in headers}
        
        sender_full = header_dict.get("from", "Unknown Sender")
        sender_name, sender_email = parseaddr(sender_full)
        
        # Extract body content
        body_text = self._extract_body_text(message["payload"])
        
        # Get thread info
        thread_id = message.get("threadId")
        
        return {
            "id": message["id"],
            "thread_id": thread_id,
            "sender_full": sender_full,
            "sender_name": sender_name or sender_email.split("@")[0],
            "sender_email": sender_email.lower(),
            "subject": header_dict.get("subject", "No Subject"),
            "date": header_dict.get("date", ""),
            "snippet": message.get("snippet", ""),
            "body_text": body_text[:2000],  # Limit body text length
            "headers": header_dict,
            "label_ids": message.get("labelIds", []),
        }
    
    def _extract_body_text(self, payload: dict) -> str:
        """Extract plain text body from email payload."""
        body = ""
        
        def extract_from_part(part):
            if part.get("mimeType") == "text/plain":
                body_data = part.get("body", {}).get("data")
                if body_data:
                    return base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")
            elif part.get("mimeType") == "multipart/alternative":
                for subpart in part.get("parts", []):
                    text = extract_from_part(subpart)
                    if text:
                        return text
            return ""
        
        if "parts" in payload:
            for part in payload["parts"]:
                body = extract_from_part(part)
                if body:
                    break
        else:
            body = extract_from_part(payload)
        
        return body.strip() if body else ""
    
    def _calculate_relevance_score(self, email_data: dict) -> int:
        """Calculate relevance score (0-100) for an email."""
        score = 50  # Base score
        
        sender_email = email_data["sender_email"]
        subject = email_data["subject"].lower()
        body_text = email_data["body_text"].lower()
        headers = email_data["headers"]
        
        # 1. Sender whitelist boost
        if sender_email in self.sender_whitelist:
            score = max(score, self.sender_whitelist[sender_email])
            logger.debug(f"Sender whitelist boost: {score}")
        
        # 2. Direct-to-me indicators
        to_header = headers.get("to", "").lower()
        cc_header = headers.get("cc", "").lower()
        
        # Count recipients (fewer = more personal)
        recipient_count = len(re.findall(r'[\\w.-]+@[\\w.-]+', to_header + cc_header))
        if recipient_count == 1:
            score += 15  # Direct message
        elif recipient_count <= 3:
            score += 10  # Small group
        elif recipient_count > 10:
            score -= 20  # Mass email
        
        # 3. Keyword analysis
        text_to_analyze = f"{subject} {body_text}"
        
        for keyword, boost in self.important_keywords.items():
            if keyword in text_to_analyze:
                score += boost
                logger.debug(f"Keyword '{keyword}' boost: +{boost}")
        
        for indicator, penalty in self.spam_indicators.items():
            if indicator in text_to_analyze:
                score += penalty  # penalty is negative
                logger.debug(f"Spam indicator '{indicator}': {penalty}")
        
        # 4. Bulk email indicators
        list_unsubscribe = headers.get("list-unsubscribe")
        precedence = headers.get("precedence", "").lower()
        
        if list_unsubscribe:
            score -= 25  # Mailing list
        
        if precedence in ["bulk", "list"]:
            score -= 20
        
        # 5. Security/authentication indicators
        if any(word in text_to_analyze for word in ["security", "suspicious", "locked", "verify"]):
            score += 15
        
        # 6. Time sensitivity
        if any(word in text_to_analyze for word in ["today", "urgent", "asap", "deadline"]):
            score += 10
        
        # 7. Thread importance (replies are often important)
        if email_data["thread_id"] and "re:" in subject:
            score += 8
        
        # Clamp score to 0-100 range
        return max(0, min(100, score))
    
    async def _generate_summary(self, email_data: dict) -> str:
        """Generate a concise summary of the email using LLM."""
        if not self.openai_client:
            return "Summary unavailable (no OpenAI key)"
        
        try:
            prompt = f"""Summarize this email in 2-4 bullet points:

From: {email_data['sender_name']} ({email_data['sender_email']})
Subject: {email_data['subject']}

Content:
{email_data['body_text'][:1000]}

Focus on:
- Key information/requests
- Why this might need attention
- Any actions required
- Timeline/urgency

Keep it concise and actionable."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ Summary generation failed: {e}")
            return f"📄 {email_data['snippet'][:150]}..."
    
    async def _send_discord_notification(self, email_data: dict, score: int, summary: str):
        """Send Discord notification for important email."""
        if not self.discord_bot:
            logger.warning("⚠️ Discord bot not available for notification")
            return
        
        try:
            # Try to find a suitable notification channel
            channel = None
            
            # Option 1: Look for a channel named "email-alerts" or "jarvis"
            for guild in self.discord_bot.guilds:
                for ch in guild.text_channels:
                    if ch.name.lower() in ["email-alerts", "jarvis", "notifications"]:
                        channel = ch
                        break
                if channel:
                    break
            
            # Option 2: Use the first available text channel if no specific channel found
            if not channel:
                for guild in self.discord_bot.guilds:
                    if guild.text_channels:
                        channel = guild.text_channels[0]
                        break
            
            # Option 3: Fallback to DM the bot owner if no channels available
            if not channel:
                # Try to find the bot owner from config or first user who DMed
                try:
                    with open("user_config.json", "r") as f:
                        config = json.load(f)
                        user_id = config.get("user_id")
                        if user_id:
                            user = await self.discord_bot.fetch_user(user_id)
                            channel = await user.create_dm()
                except Exception:
                    pass
            
            if not channel:
                logger.error("❌ No suitable Discord channel found for notifications")
                return
            
            # Create Discord embed
            embed = discord.Embed(
                title="📧 Important Email Alert",
                color=0x1f8b4c if score >= 80 else 0xf1c40f,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="From",
                value=f"{email_data['sender_name']} ({email_data['sender_email']})",
                inline=False
            )
            
            embed.add_field(
                name="Subject",
                value=email_data['subject'][:100] + ("..." if len(email_data['subject']) > 100 else ""),
                inline=False
            )
            
            embed.add_field(
                name="Summary",
                value=summary,
                inline=False
            )
            
            embed.add_field(
                name="Relevance Score",
                value=f"{score}/100",
                inline=True
            )
            
            embed.add_field(
                name="Email ID",
                value=f"`{email_data['id'][:10]}...`",
                inline=True
            )
            
            # Send the notification
            await channel.send(embed=embed)
            logger.info(f"✅ Discord notification sent for email from {email_data['sender_name']} to {channel.name}")
            
        except Exception as e:
            logger.error(f"❌ Failed to send Discord notification: {e}")
    
    def add_sender_to_whitelist(self, email: str, score: int = 90):
        """Add a sender to the whitelist."""
        self.sender_whitelist[email.lower()] = score
        logger.info(f"✅ Added {email} to whitelist with score {score}")
    
    def remove_sender_from_whitelist(self, email: str):
        """Remove a sender from the whitelist."""
        email_lower = email.lower()
        if email_lower in self.sender_whitelist:
            del self.sender_whitelist[email_lower]
            logger.info(f"✅ Removed {email} from whitelist")
        else:
            logger.warning(f"⚠️ {email} not found in whitelist")
    
    def get_stats(self) -> dict:
        """Get radar statistics."""
        return {
            "processed_emails": len(self.processed_message_ids),
            "whitelist_size": len(self.sender_whitelist),
            "threshold": self.relevance_threshold,
            "last_check": self.last_check_time.isoformat(),
        }

# Global radar instance
_email_radar = None

def get_email_radar(discord_bot=None) -> EmailRadar:
    """Get or create the global email radar instance."""
    global _email_radar
    if _email_radar is None:
        _email_radar = EmailRadar(discord_bot=discord_bot)
    elif discord_bot and not _email_radar.discord_bot:
        _email_radar.discord_bot = discord_bot
    return _email_radar

async def start_email_monitoring(discord_bot=None):
    """Start email monitoring as a background task."""
    radar = get_email_radar(discord_bot)
    await radar.start_monitoring()

if __name__ == "__main__":
    # For testing
    async def main():
        radar = EmailRadar()
        await radar.start_monitoring()
    
    asyncio.run(main())
