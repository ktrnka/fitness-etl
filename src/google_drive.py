import io
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

SERVICE_ACCOUNT_FILE = "google_service_account.json"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_drive_service(credentials_file: str = SERVICE_ACCOUNT_FILE):
    creds = service_account.Credentials.from_service_account_file(credentials_file, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)


def find_file_by_name(service, filename: str) -> str | None:
    results = service.files().list(q=f"name='{filename}'", fields="files(id, name)").execute()

    files = results.get("files", [])
    if not files:
        return None

    return files[0]["id"]


def download_file(service, file_id: str, destination_path: str):
    request = service.files().get_media(fileId=file_id)

    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

    with open(destination_path, "wb") as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Download progress: {int(status.progress() * 100)}%")
