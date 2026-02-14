import io
import os
from enum import StrEnum

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from loguru import logger

from src.google_auth_helper import get_credentials

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class FileTypes(StrEnum):
    SHEET = "application/vnd.google-apps.spreadsheet"


def get_drive_service(credentials_file: str = "google_service_account.json"):
    creds = get_credentials(SCOPES, credentials_file)
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def find_file_by_name(drive_service, filename: str, mime_type: str | None = None) -> str | None:
    query = f"name='{filename}'"
    if mime_type:
        query += f" and mimeType='{mime_type}'"
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()

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
                logger.debug(f"Download progress: {int(status.progress() * 100)}%")
