import os
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials


def get_sheet_service():
    creds_path = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    return build("sheets", "v4", credentials=creds)


def append_row(spreadsheet_id, sheet_name, values):
    service = get_sheet_service()
    body = {"values": [values]}

    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=sheet_name,
        valueInputOption="RAW",
        body=body
    ).execute()
