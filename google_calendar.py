# google_calendar.py
from googleapiclient.discovery import build
from google_auth import get_calendar_creds
from datetime import datetime, timedelta
import re

def list_upcoming_events(max_results=5):
    creds = get_calendar_creds()
    service = build("calendar", "v3", credentials=creds)
    events = (
        service.events()
        .list(
            calendarId="primary",
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
            timeMin="{}Z".format(__import__("datetime").datetime.utcnow().isoformat()),
        )
        .execute()
        .get("items", [])
    )
    return events  # each is a dict with 'summary', 'start', 'end', etc.

def create_calendar_event(title, date_str, time_str=None, duration_hours=1):
    """
    Create a calendar event.
    Args:
        title: Event title/summary
        date_str: Date in format like "tomorrow", "2025-08-15", "next friday"
        time_str: Time like "2pm", "14:30", "2:30 PM" (optional)
        duration_hours: Event duration in hours (default 1)
    """
    try:
        creds = get_calendar_creds()
        service = build("calendar", "v3", credentials=creds)
        
        # Parse the date
        event_date = parse_date(date_str)
        if not event_date:
            return f"❌ Could not understand date: {date_str}"
        
        # Parse the time
        if time_str:
            event_time = parse_time(time_str)
            if event_time:
                event_datetime = datetime.combine(event_date, event_time)
            else:
                return f"❌ Could not understand time: {time_str}"
        else:
            # Default to 10 AM if no time specified
            event_datetime = datetime.combine(event_date, datetime.min.time().replace(hour=10))
        
        # Create end time
        end_datetime = event_datetime + timedelta(hours=duration_hours)
        
        # Format for Google Calendar API
        start_time = event_datetime.isoformat()
        end_time = end_datetime.isoformat()
        
        event = {
            'summary': title,
            'start': {
                'dateTime': start_time,
                'timeZone': 'America/New_York',  # Adjust to your timezone
            },
            'end': {
                'dateTime': end_time,
                'timeZone': 'America/New_York',
            },
        }
        
        result = service.events().insert(calendarId='primary', body=event).execute()
        return f"✅ Created event '{title}' on {event_datetime.strftime('%B %d at %I:%M %p')}"
        
    except Exception as e:
        return f"❌ Failed to create event: {str(e)}"

def parse_date(date_str):
    """Parse various date formats into a date object."""
    today = datetime.now().date()
    date_str = date_str.lower().strip()
    
    if date_str in ["today"]:
        return today
    elif date_str in ["tomorrow"]:
        return today + timedelta(days=1)
    elif date_str in ["next week"]:
        return today + timedelta(days=7)
    elif "next" in date_str and any(day in date_str for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]):
        # Handle "next friday", etc.
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for i, day in enumerate(days):
            if day in date_str:
                days_ahead = i - today.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                return today + timedelta(days=days_ahead)
    else:
        # Try to parse as YYYY-MM-DD
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            pass
    
    return None

def parse_time(time_str):
    """Parse various time formats into a time object."""
    time_str = time_str.lower().strip()
    
    # Handle formats like "2pm", "2:30pm", "14:30", "2:30 PM"
    patterns = [
        r'(\d{1,2}):(\d{2})\s*(am|pm)',  # 2:30 pm
        r'(\d{1,2})\s*(am|pm)',          # 2 pm
        r'(\d{1,2}):(\d{2})',            # 14:30 (24-hour)
        r'(\d{1,2})$'                    # Just hour number
    ]
    
    for pattern in patterns:
        match = re.match(pattern, time_str)
        if match:
            groups = match.groups()
            
            if len(groups) == 3:  # Hour, minute, am/pm
                hour = int(groups[0])
                minute = int(groups[1])
                if groups[2] == 'pm' and hour != 12:
                    hour += 12
                elif groups[2] == 'am' and hour == 12:
                    hour = 0
            elif len(groups) == 2 and groups[1] in ['am', 'pm']:  # Hour, am/pm
                hour = int(groups[0])
                minute = 0
                if groups[1] == 'pm' and hour != 12:
                    hour += 12
                elif groups[1] == 'am' and hour == 12:
                    hour = 0
            elif len(groups) == 2:  # Hour, minute (24-hour)
                hour = int(groups[0])
                minute = int(groups[1])
            else:  # Just hour
                hour = int(groups[0])
                minute = 0
                # Assume PM if hour is small (like "2" -> "2 PM")
                if hour < 8:
                    hour += 12
            
            try:
                return datetime.min.time().replace(hour=hour, minute=minute)
            except:
                pass
    
    return None

def list_upcoming_events_window(timeMin, timeMax, calendarId="primary"):
    """Get events within a specific time window."""
    creds = get_calendar_creds()
    service = build("calendar", "v3", credentials=creds)
    return service.events().list(
        calendarId=calendarId,
        timeMin=timeMin, 
        timeMax=timeMax,
        singleEvents=True,
        orderBy="startTime"
    ).execute().get("items", [])

def delete_event(event_id, calendarId="primary"):
    """Delete a specific event by ID."""
    creds = get_calendar_creds()
    service = build("calendar", "v3", credentials=creds)
    service.events().delete(calendarId=calendarId, eventId=event_id).execute()
    return {"success": True, "message": f"Event {event_id} deleted successfully"}

def create_event(title, start_time, end_time=None, description=None):
    """
    Create a calendar event with ISO 8601 formatted times.
    Args:
        title: Event title/summary
        start_time: ISO 8601 start datetime string
        end_time: ISO 8601 end datetime string (optional, defaults to 1 hour after start)
        description: Optional event description
    """
    try:
        creds = get_calendar_creds()
        service = build("calendar", "v3", credentials=creds)
        
        # Parse start time
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        
        # Parse or generate end time
        if end_time:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        else:
            end_dt = start_dt + timedelta(hours=1)
        
        event = {
            'summary': title,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': 'America/New_York',  # Adjust to your timezone
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': 'America/New_York',
            },
        }
        
        if description:
            event['description'] = description
        
        result = service.events().insert(calendarId='primary', body=event).execute()
        event_id = result.get('id')
        formatted_time = start_dt.strftime('%B %d at %I:%M %p')
        
        return {
            "success": True, 
            "message": f"Created event '{title}' on {formatted_time}",
            "event_id": event_id
        }
        
    except Exception as e:
        return {"success": False, "message": f"Failed to create event: {str(e)}"}

def list_events(start_date, end_date, max_results=10):
    """
    List events in a date range for function calling.
    Args:
        start_date: ISO 8601 start date string
        end_date: ISO 8601 end date string  
        max_results: Maximum number of events to return
    """
    try:
        # Parse dates and convert to datetime strings for the API
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # If end_date is just a date (00:00:00), extend it to end of day
        if end_dt.time() == datetime.min.time():
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        
        timeMin = start_dt.isoformat() + 'Z'
        timeMax = end_dt.isoformat() + 'Z'
        
        events = list_upcoming_events_window(timeMin, timeMax)
        
        # Format events for function response
        event_list = []
        for event in events[:max_results]:
            event_info = {
                "id": event.get("id"),
                "title": event.get("summary", "Untitled"),
                "start": event.get("start", {}).get("dateTime", event.get("start", {}).get("date")),
                "end": event.get("end", {}).get("dateTime", event.get("end", {}).get("date"))
            }
            event_list.append(event_info)
        
        return {
            "success": True,
            "events": event_list,
            "count": len(event_list)
        }
        
    except Exception as e:
        return {"success": False, "message": f"Failed to list events: {str(e)}"}

def update_event(event_id, title=None, start_time=None, end_time=None, description=None):
    """
    Update an existing calendar event.
    Args:
        event_id: The Google Calendar event ID to update
        title: New event title (optional)
        start_time: New ISO 8601 start datetime (optional)
        end_time: New ISO 8601 end datetime (optional)
        description: New event description (optional)
    """
    try:
        creds = get_calendar_creds()
        service = build("calendar", "v3", credentials=creds)
        
        # Get the existing event first
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
        
        # Update only the fields that were provided
        if title is not None:
            event['summary'] = title
        if start_time is not None:
            event['start'] = {'dateTime': start_time, 'timeZone': 'America/New_York'}
        if end_time is not None:
            event['end'] = {'dateTime': end_time, 'timeZone': 'America/New_York'}
        if description is not None:
            event['description'] = description
            
        # Update the event
        updated_event = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
        
        return {
            "success": True,
            "message": f"Event updated successfully",
            "event_id": event_id,
            "title": updated_event.get('summary', 'Untitled'),
            "start": updated_event.get('start', {}).get('dateTime'),
            "end": updated_event.get('end', {}).get('dateTime')
        }
        
    except Exception as e:
        return {"success": False, "message": f"Failed to update event: {str(e)}"}

def delete_calendar_event(event_query):
    """
    Delete a calendar event based on a query (title, date, etc.)
    Args:
        event_query: Description of the event to delete
    """
    try:
        creds = get_calendar_creds()
        service = build("calendar", "v3", credentials=creds)
        
        # Get upcoming events to search through
        events_result = service.events().list(
            calendarId='primary',
            maxResults=50,
            singleEvents=True,
            orderBy='startTime',
            timeMin=datetime.utcnow().isoformat() + 'Z'
        ).execute()
        
        events = events_result.get('items', [])
        
        # Search for matching events
        query_lower = event_query.lower()
        matches = []
        
        for event in events:
            event_title = event.get('summary', '').lower()
            event_start = event.get('start', {})
            
            # Check if query matches title or contains relevant keywords
            if any(word in event_title for word in query_lower.split()) or \
               any(word in query_lower for word in event_title.split()):
                matches.append(event)
        
        if not matches:
            return f"❌ No events found matching: {event_query}"
        
        if len(matches) == 1:
            # Delete the single match
            event = matches[0]
            service.events().delete(
                calendarId='primary',
                eventId=event['id']
            ).execute()
            
            title = event.get('summary', 'Untitled Event')
            return f"✅ Deleted event: {title}"
        
        else:
            # Multiple matches - list them for user to choose
            response = f"Found {len(matches)} matching events:\n"
            for i, event in enumerate(matches, 1):
                title = event.get('summary', 'Untitled Event')
                start = event.get('start', {})
                if 'dateTime' in start:
                    dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                    time_str = dt.strftime('%B %d at %I:%M %p')
                elif 'date' in start:
                    dt = datetime.fromisoformat(start['date'])
                    time_str = dt.strftime('%B %d (All day)')
                else:
                    time_str = "Unknown time"
                
                response += f"{i}. {title} - {time_str}\n"
            
            response += "\nPlease be more specific about which event to delete."
            return response
            
    except Exception as e:
        return f"❌ Failed to delete event: {str(e)}"
