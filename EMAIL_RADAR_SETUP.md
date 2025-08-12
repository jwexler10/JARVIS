# Email Radar Setup Guide

## Overview
The Email Radar is a smart email monitoring system that integrates with your Discord bot to notify you of important emails. It monitors your Gmail inbox and uses AI-powered relevance scoring to only alert you when emails are worth your attention.

## Features
- 📧 Gmail monitoring with smart filtering
- 🎯 Relevance scoring (0-100) with customizable threshold
- 🤖 AI-powered email summaries
- 📱 Discord notifications for important emails
- 📋 Sender whitelist management
- 🛡️ Spam and promotional email filtering
- 🔄 Background polling every 3 minutes

## Initial Setup

### 1. Gmail API Credentials
Make sure you have Gmail API access set up:
- Your `credentials.json` should include Gmail API scope
- Run the bot once to authenticate and create `gmail_token.json`
- The bot will request Gmail permissions on first run

### 2. Discord Channel Configuration
In `email_radar.py`, update the Discord channel ID:
```python
channel_id = 1273416439776899122  # Replace with your channel ID
```

To find your channel ID:
1. Enable Developer Mode in Discord
2. Right-click your channel → Copy ID

### 3. Install Required Dependencies
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

## Configuration

### Relevance Scoring
The system scores emails 0-100 based on:

**Positive Factors (+points):**
- Sender whitelist matches (up to 100)
- Direct-to-you emails (+15)
- Small recipient count (+10-15)
- Important keywords: "urgent" (+20), "meeting" (+15), "invoice" (+18), etc.
- Security alerts (+15)
- Time-sensitive words (+10)
- Thread replies (+8)

**Negative Factors (-points):**
- Mass email indicators (-20 to -25)
- Promotional keywords (-10 to -20)
- List-Unsubscribe header (-25)
- Bulk precedence header (-20)

### Default Settings
- **Threshold**: 60 (only notify if score ≥ 60)
- **Polling interval**: 180 seconds (3 minutes)
- **Max emails per check**: 20

## Discord Commands

### Status and Help
```
email radar                    # Show current status
email radar help              # Show all commands
```

### Whitelist Management
```
email radar whitelist add boss@company.com 95    # Add sender with high score
email radar whitelist remove spam@example.com    # Remove sender
email radar whitelist list                       # Show all whitelisted senders
```

### Threshold Control
```
email radar threshold 70      # Set threshold to 70 (more restrictive)
email radar threshold 50      # Set threshold to 50 (less restrictive)
```

## Customization

### Adding Important Keywords
Edit `email_radar.py` in the `__init__` method:
```python
self.important_keywords = {
    "urgent": 20,
    "meeting": 15,
    "your_company_name": 25,    # Add your company
    "deadline": 20,
    # Add more keywords...
}
```

### Adding Spam Indicators
```python
self.spam_indicators = {
    "unsubscribe": -15,
    "marketing": -15,
    "promotional": -20,
    # Add more spam words...
}
```

### Adjusting Polling Frequency
In `discord_bot.py`, change the polling interval:
```python
await radar.start_monitoring(poll_interval=300)  # 5 minutes instead of 3
```

## Email Notification Format
Each notification includes:
- **From**: Sender name and email
- **Subject**: Email subject (truncated if long)
- **Summary**: AI-generated 2-4 bullet points
- **Relevance Score**: Score out of 100
- **Email ID**: For troubleshooting

## Troubleshooting

### Common Issues

**Gmail Authentication Errors:**
- Delete `gmail_token.json` and restart bot to re-authenticate
- Ensure Gmail API is enabled in Google Cloud Console
- Check that `credentials.json` has correct Gmail scope

**No Notifications:**
- Check threshold setting (`email radar` command)
- Verify Discord channel ID is correct
- Check bot logs for errors
- Ensure emails aren't being filtered by Gmail labels

**Permission Errors:**
- Bot needs Gmail modify permissions (not just readonly)
- Re-authenticate if you upgraded from readonly scope

### Monitoring Logs
The bot logs email radar activity:
- `📧 Found X new emails to process`
- `📊 Email from sender: score=X`
- `✅ Discord notification sent`

### Performance
- Polling every 3 minutes should be Gmail API friendly
- System tracks processed emails to avoid duplicates
- Background processing won't block Discord bot

## Security Notes

- Emails are processed locally - only summaries sent to Discord
- No email content stored permanently
- Sender whitelist persists in memory only (resets on restart)
- Email IDs in notifications are truncated for privacy

## Future Enhancements (Phase 2)

Planned features:
- Outlook/Office 365 integration
- Email persistence and history
- More advanced ML-based scoring
- Webhook-based real-time notifications
- Mark-as-read functionality
- Email thread tracking
- Calendar integration for meeting emails

---

## Quick Start
1. Update Discord channel ID in `email_radar.py`
2. Start Discord bot: `python discord_bot.py`
3. DM the bot: `email radar` to check status
4. Add important senders: `email radar whitelist add important@email.com 90`
5. Adjust threshold if needed: `email radar threshold 65`

The Email Radar will now monitor your inbox and notify you of important emails via Discord!
