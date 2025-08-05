# google_auth.py

import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# OAuth2 scopes for the various Google services
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]  # Read/write for creating events
DRIVE_SCOPES    = ["https://www.googleapis.com/auth/drive.readonly"]
GMAIL_SCOPES    = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_creds(scopes, creds_file="credentials.json", token_file="token.json"):
    """
    Returns valid credentials for the given OAuth2 scopes.
    Will refresh an existing token or launch the OAuth flow if needed.
    """
    creds = None
    # 1) Load existing token if available
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    # 2) If no valid creds, run through the OAuth2 flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
            creds = flow.run_local_server(port=0)
        # 3) Save the credentials for next time
        with open(token_file, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
    return creds

def get_calendar_creds(creds_file="credentials.json", token_file="calendar_token.json"):
    """Get credentials authorized for Google Calendar (read-only)."""
    return get_creds(CALENDAR_SCOPES, creds_file, token_file)

def get_drive_creds(creds_file="credentials.json", token_file="drive_token.json"):
    """Get credentials authorized for Google Drive (read-only)."""
    return get_creds(DRIVE_SCOPES, creds_file, token_file)

def get_gmail_creds(creds_file="credentials.json", token_file="gmail_token.json"):
    """Get credentials authorized for Gmail (read-only)."""
    return get_creds(GMAIL_SCOPES, creds_file, token_file)
