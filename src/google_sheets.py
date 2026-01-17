import pandas as pd
from googleapiclient.discovery import build

from src.google_auth_helper import get_credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly"
]


def get_sheets_service():
    creds = get_credentials(SCOPES)
    return build("sheets", "v4", credentials=creds)


def find_spreadsheet_by_name(service, name: str) -> str | None:
    creds = get_credentials(SCOPES)
    drive_service = build("drive", "v3", credentials=creds)
    
    results = drive_service.files().list(
        q=f"name='{name}' and mimeType='application/vnd.google-apps.spreadsheet'",
        fields="files(id, name)"
    ).execute()
    
    files = results.get("files", [])
    if not files:
        return None
    
    return files[0]["id"]


def write_dataframe(service, spreadsheet_id: str, sheet_name: str, df: pd.DataFrame):
    values = [df.index.name] + df.columns.tolist()
    data = [values]
    
    for idx, row in df.iterrows():
        row_data = [str(idx)] + [None if pd.isna(val) else val for val in row.tolist()]
        data.append(row_data)
    
    body = {"values": data}
    
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=sheet_name
    ).execute()
    
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=sheet_name,
        valueInputOption="RAW",
        body=body
    ).execute()
