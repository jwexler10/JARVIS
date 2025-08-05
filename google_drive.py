# google_drive.py
from googleapiclient.discovery import build
from google_auth import get_drive_creds

def list_my_files(page_size=10):
    creds = get_drive_creds()
    service = build("drive", "v3", credentials=creds)
    results = (
        service.files()
        .list(pageSize=page_size, fields="files(id, name, mimeType)")
        .execute()
    )
    return results.get("files", [])  # list of {'id':…, 'name':…, …}
