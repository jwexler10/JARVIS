# google_commands.py
"""
Google service integration commands for Jarvis
"""

from google_calendar import list_upcoming_events, create_calendar_event, delete_calendar_event, list_upcoming_events_window, delete_event
from google_gmail import get_recent_emails, read_email_content
from google_drive import list_my_files
import re
from datetime import datetime, timedelta
import dateparser
import difflib

def handle_calendar_command(command: str) -> str:
    """Handle calendar-related commands."""
    cmd_lower = command.lower()
    
    # Check my calendar/schedule/events
    if any(phrase in cmd_lower for phrase in ["check my calendar", "what's on my calendar", "my schedule", "upcoming events", "what do i have"]):
        try:
            events = list_upcoming_events(5)
            if not events:
                return "📅 You have no upcoming events on your calendar."
            
            response = "📅 Your upcoming events:\n"
            for i, event in enumerate(events, 1):
                title = event.get('summary', 'No title')
                
                # Format the start time
                start = event.get('start', {})
                if 'dateTime' in start:
                    # Parse datetime
                    from datetime import datetime
                    dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    time_str = dt.strftime('%B %d at %I:%M %p')
                elif 'date' in start:
                    # All-day event
                    from datetime import datetime
                    dt = datetime.fromisoformat(start['date'])
                    time_str = dt.strftime('%B %d (All day)')
                else:
                    time_str = "Date/time unknown"
                
                response += f"{i}. {title} - {time_str}\n"
            
            return response.strip()
            
        except Exception as e:
            return f"❌ Failed to check calendar: {str(e)}"
    
    # Schedule/create an event
    elif any(phrase in cmd_lower for phrase in ["schedule", "create event", "add to calendar", "book", "set up meeting", "create an event", "make an appointment"]):
        return parse_and_create_event(command)
    
    # Delete an event
    elif any(phrase in cmd_lower for phrase in ["delete", "remove", "cancel"]) and any(phrase in cmd_lower for phrase in ["event", "appointment", "meeting"]):
        return handle_delete_event(command)
    
    return None

def parse_and_create_event(command: str) -> str:
    """Parse a natural language command to create a calendar event."""
    try:
        # Extract event title (everything in quotes or after "schedule"/"book")
        title_patterns = [
            r'"([^"]+)"',  # "meeting with client"
            r"'([^']+)'",  # 'doctor appointment'
            r'called [\'"]([^\'"]+)[\'"]',  # called "doctor appointment"
            r'schedule (?:a |an )?(.+?) (?:for|on|at)',  # schedule a meeting for...
            r'book (?:a |an )?(.+?) (?:for|on|at)',      # book an appointment for...
            r'create (?:a |an )?event (?:called |named )?(.+?) (?:for|on|at)',  # create event called...
            r'make (?:a |an )?(?:appointment|meeting) (?:called |named )?(.+?) (?:for|on|at)',  # make appointment called...
        ]
        
        title = None
        for pattern in title_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                break
        
        if not title:
            # Fallback: try to extract title after common keywords
            keywords = ["schedule", "book", "create event", "add to calendar"]
            for keyword in keywords:
                if keyword in command.lower():
                    parts = command.lower().split(keyword, 1)
                    if len(parts) > 1:
                        title = parts[1].strip().split(' for ')[0].split(' on ')[0].split(' at ')[0]
                        break
        
        if not title:
            return "❌ I couldn't understand what event you want to schedule. Try: 'Schedule a meeting with Bob for tomorrow at 2pm'"
        
        # Extract date
        date_patterns = [
            r'\b(today|tomorrow|next week)\b',
            r'\b(next \w+day)\b',  # next friday, next monday
            r'\b(\d{4}-\d{2}-\d{2})\b',  # 2025-08-15
            r'\bon (\w+ \d+)\b',  # on August 15
        ]
        
        date_str = None
        for pattern in date_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                break
        
        if not date_str:
            date_str = "today"  # Default to today
        
        # Extract time
        time_patterns = [
            r'\bat (\d{1,2}:\d{2}\s*(?:am|pm)?)\b',  # at 2:30pm
            r'\bat (\d{1,2}\s*(?:am|pm))\b',         # at 2pm
            r'\bat (\d{1,2})\b',                     # at 2 (assume pm for small numbers)
        ]
        
        time_str = None
        for pattern in time_patterns:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                time_str = match.group(1)
                break
        
        # Extract duration
        duration = 1  # Default 1 hour
        duration_match = re.search(r'for (\d+) hours?', command, re.IGNORECASE)
        if duration_match:
            duration = int(duration_match.group(1))
        
        # Create the event
        result = create_calendar_event(title, date_str, time_str, duration)
        return result
        
    except Exception as e:
        return f"❌ Failed to parse event details: {str(e)}"

def enhanced_date_parse(command: str):
    """
    Enhanced date parsing with multiple strategies for better accuracy.
    """
    import re
    from datetime import datetime, timedelta
    
    # Strategy 1: Try dateparser with the full command
    dt = dateparser.parse(command, settings={"PREFER_DATES_FROM": "future"})
    if dt:
        return dt
    
    # Strategy 2: Extract date/time patterns and parse them separately
    date_patterns = [
        r'\bon\s+((?:january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2}(?:st|nd|rd|th)?(?:\s+\d{4})?)',
        r'\bon\s+((?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))',
        r'\bon\s+(tomorrow|today|yesterday)',
        r'\b(next\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday))',
        r'\b(august\s+\d{1,2}(?:st|nd|rd|th)?)',
        r'\b(\d{1,2}/\d{1,2}(?:/\d{2,4})?)',
        r'\b(\d{4}-\d{1,2}-\d{1,2})',
    ]
    
    time_patterns = [
        r'\bat\s+(\d{1,2}:\d{2}\s*(?:am|pm))',
        r'\bat\s+(\d{1,2}\s*(?:am|pm))',
        r'\b(\d{1,2}:\d{2})',
        r'\b(\d{1,2}(?:am|pm))',
    ]
    
    # Extract date
    date_str = None
    for pattern in date_patterns:
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            break
    
    # Extract time
    time_str = None
    for pattern in time_patterns:
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            time_str = match.group(1)
            break
    
    # Try parsing the extracted components
    if date_str:
        # Try date string alone
        dt = dateparser.parse(date_str, settings={"PREFER_DATES_FROM": "future"})
        if dt:
            # If we have a time, try to combine them
            if time_str:
                time_dt = dateparser.parse(time_str)
                if time_dt:
                    # Combine date and time
                    dt = dt.replace(hour=time_dt.hour, minute=time_dt.minute)
            return dt
    
    # Strategy 3: Handle relative dates manually
    command_lower = command.lower()
    now = datetime.now()
    
    if 'tomorrow' in command_lower:
        dt = now + timedelta(days=1)
        # Try to extract time
        if time_str:
            time_dt = dateparser.parse(time_str)
            if time_dt:
                dt = dt.replace(hour=time_dt.hour, minute=time_dt.minute)
        return dt
    
    if 'today' in command_lower:
        dt = now
        if time_str:
            time_dt = dateparser.parse(time_str)
            if time_dt:
                dt = dt.replace(hour=time_dt.hour, minute=time_dt.minute)
        return dt
    
    # Handle "next Friday", "next Monday", etc.
    next_day_match = re.search(r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)', command_lower)
    if next_day_match:
        day_name = next_day_match.group(1)
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        target_day = days.index(day_name)
        current_day = now.weekday()
        
        days_ahead = target_day - current_day
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        dt = now + timedelta(days=days_ahead)
        if time_str:
            time_dt = dateparser.parse(time_str)
            if time_dt:
                dt = dt.replace(hour=time_dt.hour, minute=time_dt.minute)
        return dt
    
    # Strategy 4: Try common date formats manually
    august_match = re.search(r'august\s+(\d{1,2})(?:st|nd|rd|th)?', command_lower)
    if august_match:
        day = int(august_match.group(1))
        year = now.year if now.month <= 8 else now.year + 1
        dt = datetime(year, 8, day)
        if time_str:
            time_dt = dateparser.parse(time_str)
            if time_dt:
                dt = dt.replace(hour=time_dt.hour, minute=time_dt.minute)
        return dt
    
    return None

def handle_delete_event(command: str) -> str:
    """Parse a command to delete a calendar event with improved date/time parsing and fuzzy matching."""
    try:
        # 1) Parse date/time from command using enhanced parsing
        dt = enhanced_date_parse(command)
        if not dt:
            return "❌ I couldn't understand the date and time. Could you please rephrase? For example: 'Cancel my doctor appointment on August 1st at 10 AM'"
        
        # Get the day window
        start_day = datetime(dt.year, dt.month, dt.day, 0, 0, 0)
        end_day = start_day + timedelta(days=1)
        
        # 2) Search only within that day
        events = list_upcoming_events_window(
            start_day.isoformat() + "Z", 
            end_day.isoformat() + "Z"
        )
        
        if not events:
            date_str = dt.strftime("%B %d")
            return f"❌ I couldn't find any appointments on {date_str}. Are you sure about the date?"
        
        # Extract keywords from the command (remove common cancel words)
        cancel_words = {"cancel", "delete", "remove", "my", "the", "event", "appointment", "meeting", "on", "at", "in", "for"}
        command_words = set(command.lower().split()) - cancel_words
        search_phrase = " ".join(command_words)
        
        # 3) Fuzzy match on event summaries
        event_titles = [event.get("summary", "Untitled") for event in events]
        
        # Try multiple matching strategies
        matches = []
        
        # Strategy 1: Direct fuzzy matching against search phrase
        fuzzy_matches = difflib.get_close_matches(search_phrase, event_titles, n=3, cutoff=0.4)
        for title in fuzzy_matches:
            event = next(e for e in events if e.get("summary") == title)
            matches.append(event)
        
        # Strategy 2: Check if any words from command appear in event titles
        if not matches:
            for event in events:
                title = event.get("summary", "").lower()
                if any(word in title for word in command_words if len(word) > 2):
                    matches.append(event)
        
        # 4) Handle results
        if len(matches) == 1:
            # Perfect match - delete it
            event = matches[0]
            delete_event(event["id"])
            
            title = event.get("summary", "Untitled Event")
            when = dt.strftime("%B %d %Y at %I:%M %p")
            return f"✅ Canceled your '{title}' on {when}."
        
        elif len(matches) == 0:
            date_str = dt.strftime("%B %d")
            time_str = dt.strftime("%I:%M %p")
            return f"❌ I couldn't find any '{search_phrase}' on {date_str} at {time_str}. Did I get the date or title right?"
        
        else:
            # Multiple matches - ask for clarification
            date_str = dt.strftime("%B %d")
            response = f"I found multiple appointments on {date_str}:\n"
            
            for i, event in enumerate(matches[:3], 1):  # Limit to 3 matches
                title = event.get("summary", "Untitled")
                start = event.get("start", {})
                
                if "dateTime" in start:
                    event_dt = dateparser.parse(start["dateTime"])
                    time_str = event_dt.strftime("%I:%M %p") if event_dt else "Unknown time"
                elif "date" in start:
                    time_str = "All day"
                else:
                    time_str = "Unknown time"
                
                response += f"{i}. {title} at {time_str}\n"
            
            response += "\nWhich one should I cancel? Please be more specific."
            return response
            
    except Exception as e:
        return f"❌ Failed to cancel event: {str(e)}"

def handle_email_command(command: str) -> str:
    """Handle email-related commands."""
    cmd_lower = command.lower()
    
    # Check emails - expanded patterns to catch more variations
    if any(phrase in cmd_lower for phrase in [
        "check my email", "read my email", "show me emails", "any new emails", "recent emails",
        "what's my email", "email looking like", "check email", "show emails", "my emails",
        "inbox", "gmail", "any mail", "new mail", "latest emails"
    ]):
        try:
            emails = get_recent_emails(5)
            if not emails:
                return "📧 No recent emails found."
            
            if "error" in emails[0]:
                return f"❌ {emails[0]['error']}"
            
            response = "📧 Your recent emails:\n"
            for i, email in enumerate(emails, 1):
                sender = email.get('sender', 'Unknown').split('<')[0].strip()  # Clean sender name
                subject = email.get('subject', 'No subject')
                snippet = email.get('snippet', '')[:60] + "..." if len(email.get('snippet', '')) > 60 else email.get('snippet', '')
                
                response += f"{i}. From: {sender}\n   Subject: {subject}\n   Preview: {snippet}\n\n"
            
            return response.strip()
            
        except Exception as e:
            return f"❌ Failed to check emails: {str(e)}"
    
    # Read specific email (if user mentions "first email", "latest email", etc.)
    elif any(phrase in cmd_lower for phrase in ["read the first", "read the latest", "open the first", "show me the first"]):
        try:
            emails = get_recent_emails(1)
            if not emails or "error" in emails[0]:
                return "❌ No emails found or error retrieving emails."
            
            email_content = read_email_content(emails[0]['id'])
            if "error" in email_content:
                return f"❌ {email_content['error']}"
            
            response = f"📧 **Email from {email_content['sender']}**\n"
            response += f"**Subject:** {email_content['subject']}\n"
            response += f"**Date:** {email_content['date']}\n\n"
            response += f"**Content:**\n{email_content['body'][:500]}..."  # Limit content length
            
            return response
            
        except Exception as e:
            return f"❌ Failed to read email: {str(e)}"
    
    return None

def handle_drive_command(command: str) -> str:
    """Handle Google Drive related commands."""
    cmd_lower = command.lower()
    
    if any(phrase in cmd_lower for phrase in ["check my drive", "show my files", "list my files", "what's in my drive", "show me my google drive", "google drive files", "my drive files"]):
        try:
            files = list_my_files(10)
            if not files:
                return "📁 No files found in your Google Drive."
            
            response = "📁 Your recent Google Drive files:\n"
            for i, file in enumerate(files, 1):
                name = file.get('name', 'Unknown')
                file_type = file.get('mimeType', '').split('.')[-1] if '.' in file.get('mimeType', '') else 'file'
                response += f"{i}. {name} ({file_type})\n"
            
            return response.strip()
            
        except Exception as e:
            return f"❌ Failed to check Google Drive: {str(e)}"
    
    return None

def handle_google_command(command: str) -> str:
    """Main handler for all Google service commands."""
    # Try calendar commands first
    result = handle_calendar_command(command)
    if result:
        return result
    
    # Try email commands
    result = handle_email_command(command)
    if result:
        return result
    
    # Try drive commands
    result = handle_drive_command(command)
    if result:
        return result
    
    return None  # No Google command matched
