# app/drive_utils.py

import io
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv

# Load environment variables from .env (for local dev)
load_dotenv()

# Google Drive folder MIME type
FOLDER_MIME_TYPE = 'application/vnd.google-apps.folder'

# Scopes for read-only access
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """Initializes and returns Google Drive API service."""
    # Load credentials from environment variable
    credentials_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    creds = service_account.Credentials.from_service_account_info(
        credentials_info, scopes=SCOPES
    )
    return build('drive', 'v3', credentials=creds)

def list_files_in_folder(folder_id):
    """
    Lists files in a specified Google Drive folder (non-recursive).
    Returns a list of dictionaries with file 'id' and 'name'.
    """
    service = get_drive_service()
    query = f"'{folder_id}' in parents and mimeType != '{FOLDER_MIME_TYPE}' and trashed = false"
    results = service.files().list(
        q=query,
        pageSize=1000,
        fields="files(id, name)"
    ).execute()
    return results.get('files', [])

def download_file(file_id, file_name, save_dir="app/images"):
    """
    Downloads a file from Google Drive using its file ID.
    Saves it to the specified local directory and returns the file path.
    """
    os.makedirs(save_dir, exist_ok=True)  # Ensure save directory exists

    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)
    filepath = os.path.join(save_dir, file_name)

    with io.FileIO(filepath, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()

    return filepath