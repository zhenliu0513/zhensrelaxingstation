"""
Optional Google Sheets backup integration.
This module will append a saved Record to a Google Sheet if SHEETS_ENABLED=true.
Configuration via environment variables explained in README.
"""
import os
from models import Record
from datetime import datetime
import json

SHEETS_ENABLED = os.environ.get('SHEETS_ENABLED', 'false').lower() == 'true'
SHEET_ID = os.environ.get('SHEET_ID')
SHEET_NAME = os.environ.get('SHEET_NAME', 'Sheet1')

if SHEETS_ENABLED:
    import gspread
    from google.oauth2.service_account import Credentials

def _get_client():
    """
    Create a gspread client from either a service account file path or JSON string in env.
    """
    info = None
    service_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE')
    service_info = os.environ.get('GOOGLE_SERVICE_ACCOUNT_INFO')
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    if service_file and os.path.exists(service_file):
        creds = Credentials.from_service_account_file(service_file, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    if service_info:
        info = json.loads(service_info)
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    raise RuntimeError("Google Sheets credentials not configured")

def maybe_append_to_sheet(record: Record):
    """
    Append a single record row to Google Sheets if enabled.
    Row columns: 日期, 服务项目, 时长, 技师, 刷卡, 现金, 总额, 客人数, 备注, 保存时间
    """
    if not SHEETS_ENABLED:
        return
    if not SHEET_ID:
        raise RuntimeError("SHEET_ID not set")
    client = _get_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    therapist = record.therapist.name if record.therapist else ""
    row = [
        record.date.isoformat(),
        record.service_type,
        record.duration,
        therapist,
        f"{record.card_amount:.2f}",
        f"{record.cash_amount:.2f}",
        f"{record.total_amount:.2f}",
        str(record.customer_count),
        record.note or "",
        datetime.utcnow().isoformat()
    ]
    sheet.append_row(row, value_input_option='USER_ENTERED')
