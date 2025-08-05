# google_gmail.py

from googleapiclient.discovery import build
from google_auth import get_gmail_creds
import base64

def list_unread_messages(max_results=5):
    creds = get_gmail_creds()   # re-uses credentials.json + gmail_token.json
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(
        userId="me",
        labelIds=["INBOX", "UNREAD"],
        maxResults=max_results
    ).execute()
    return results.get("messages", [])

def get_recent_emails(max_results=5):
    """Get recent emails with subject, sender, and snippet."""
    try:
        creds = get_gmail_creds()
        service = build("gmail", "v1", credentials=creds)
        
        # Get list of recent messages
        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            maxResults=max_results
        ).execute()
        
        messages = results.get("messages", [])
        email_list = []
        
        for msg in messages:
            # Get full message details
            full_msg = service.users().messages().get(userId="me", id=msg["id"]).execute()
            
            # Extract headers
            headers = full_msg["payload"].get("headers", [])
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
            
            # Get snippet
            snippet = full_msg.get("snippet", "")
            
            email_list.append({
                "id": msg["id"],
                "subject": subject,
                "sender": sender,
                "snippet": snippet
            })
        
        return email_list
        
    except Exception as e:
        return [{"error": f"Failed to retrieve emails: {str(e)}"}]

def read_email_content(email_id):
    """Read the full content of a specific email."""
    try:
        creds = get_gmail_creds()
        service = build("gmail", "v1", credentials=creds)
        
        # Get the email
        message = service.users().messages().get(userId="me", id=email_id).execute()
        
        # Extract headers
        headers = message["payload"].get("headers", [])
        subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
        sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown Sender")
        date = next((h["value"] for h in headers if h["name"] == "Date"), "Unknown Date")
        
        # Extract body
        body = extract_email_body(message["payload"])
        
        return {
            "subject": subject,
            "sender": sender,
            "date": date,
            "body": body
        }
        
    except Exception as e:
        return {"error": f"Failed to read email: {str(e)}"}

def extract_email_body(payload):
    """Extract the body content from email payload."""
    body = ""
    
    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/plain":
                if "data" in part["body"]:
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    break
            elif part["mimeType"] == "text/html":
                if "data" in part["body"] and not body:  # Use HTML only if no plain text
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
    else:
        if payload["mimeType"] == "text/plain" and "data" in payload["body"]:
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
    
    return body if body else "No readable content found"
