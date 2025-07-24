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
    # credentials_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    credentials_info = {
  "type": "service_account",
  "project_id": "meter-ocr-project-466817",
  "private_key_id": "92bbe1a65b4e78dbcef86ff3f508ace480930b77",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCf7VQ++Dg8t4+E\nCBE2u8jReM7mh+cNHs2WX+Q4j/WnhX4VbJ2is4YpEXMaQAnsRaiCzK+eYnPfRzxr\nXutd6ls7wW3jTt3rOK7WMlOR3rIJwI0zrjJgb59vyiASHZpJgQ2//6Vp7d3w8zwK\nOkyqB6nI+CsLnCZ2aMioFaQwt4O1dzJD7dOyfY4YP5283+e2BMwHU0YRV2K10/2c\ny6g4mBzns7H3zQcdGG3Iw9tstt2OBmFg/O4DYv0+1+2ppOo/11ob8MlbgwMBex0m\n11dv71q5zNzMcP4G96KzKIoVOA0PYGoEnhzpV9Qb69zDLug+/Sc5iB0OR0FISzSs\nh4k/dB11AgMBAAECggEAJxzv5Puno1/ga3HepeR825BAh9yWi1ysernGkvfQZHFv\nUfWPww5Fgk9Id5PQaXbq3NyLGgEppiKhuf/LsBskR4PJ6JUuDLx+9Bd4XV1Z7S0o\ny4ovu2qpU3mbaNrRFGeJ8ZpoPfVFOcv/M+Aoxk/b/DEHtA3zUTPU2Vj7oEeNoIhc\nqWL3Rmt4iq2qMMA5EOC4Fxt8TwTWGbq/c0psvolPulDFZL7cyQRTpvGXEhjtkGOg\n1eHG/u6KEk16rqTWMKUe7TBR/v6lVLcNNJFJU4k67m1+xGX39Xc6pbrH0ZXhuLQA\nSPgXDz0Vli/62LceuOd3d7/+elBRtqQ7TUR/Qx7+oQKBgQDM6U5uEuowiygf5VAJ\nyGY3kzfAvJ2BcyxEAjN4favuwEQslvBrRDzI1C9c/YF9UgraSIcFIfPsNupaQhAr\nzwS177eSvzcPITYTYtF45aOaLU8cYFthv6w0eTZjRUMMO53X2FJKFfbDmv4NZ3pa\ntuCfjYpnzmINC0SlvTqU5oTqIQKBgQDHzNnVz6OLpLPo1JrGStWVUqImAdeU4dYn\n+fTDLrSL2b+yM/T6LbC+0kbYxJX1dCoMy5o8Sjx606KzQyxKfmTVgz7yv9Ldf289\nrBLGtYnlGxCNp07eHoojVtgSqHasYgd/Ws/iytDjy1IOc6K0kwmBb3VikxuPRTEs\nCI0d4VNQ1QKBgCB1/TS2zl6uTMbwvsMt+fNn4PcpahItup9zcc/uqKQD1UjzCFcV\n0kNGSdKDXlYJ/yohPzJy9H9BG9L8kC9AdlCUDxKyM/iznCtqBiEOz+IGt3eZVCCi\nCpetdA451KtFbnXZEQAnhpXqIcDh2aIxQlhERd639RR36oIO/g7Ejd3BAoGBAJTg\n3gjmGdV6OtzpXxMWvCPyWQS9Jqi3x14ucOXnrXzwGlltQcQRu7vU8BmiEqO9lX/H\nTvxRzNMxU/EDwsMXf4dhrswvh66owHlR+QO8Ti47hpAm9Sup0gEXOxZcFWHKAhAx\n2OoDerfizxgZrkmjrteV+AAl4clWI5fOH2j+d5ipAoGAT00M5AqrZFjrz4PIHRR2\nCpbXIMD28gV7E4dvT+TIaONnViJDQGm9FMSPns8Xqsx+1rRgmtiNFJQIAtZWHJqa\nYj9gypkJe7qj3NQ55tf+lcs9OXhJpm0wl3O/ZP8y6vPQ1wPpfS7jdUPSWKpH4JsQ\nwuv0YHVatp2OFKrKoRcRaoM=\n-----END PRIVATE KEY-----\n",
  "client_email": "meter-ocr-reader@meter-ocr-project-466817.iam.gserviceaccount.com",
  "client_id": "111440708014105770767",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/meter-ocr-reader%40meter-ocr-project-466817.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

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