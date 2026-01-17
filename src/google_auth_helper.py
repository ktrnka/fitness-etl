import os

import google.auth
from google.oauth2 import service_account

SERVICE_ACCOUNT_FILE = "google_service_account.json"


def get_credentials(scopes: list[str], credentials_file: str = SERVICE_ACCOUNT_FILE):
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        creds, _ = google.auth.default(scopes=scopes)
    else:
        creds = service_account.Credentials.from_service_account_file(credentials_file, scopes=scopes)
    return creds
