from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load the OAuth credentials you just obtained
SCOPES = ['https://www.googleapis.com/auth/calendar']
creds = Credentials.from_authorized_user_file('oauth_credentials.json', scopes=SCOPES)

# Build the Calendar service
service = build('calendar', 'v3', credentials=creds)

# Fetch the next 5 events from your primary calendar
events_result = service.events().list(
    calendarId='primary', maxResults=5, singleEvents=True,
    orderBy='startTime').execute()
events = events_result.get('items', [])

if not events:
    print('No upcoming events found.')
else:
    print('Upcoming events:')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(f" - {start} | {event.get('summary', 'No title')}")
