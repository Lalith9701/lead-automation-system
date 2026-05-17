"""
services/sheets_logger.py — Google Sheets logging via gspread.

Columns (1-indexed):
  1  Timestamp
  2  Full Name
  3  Email
  4  Company
  5  Website
  6  Industry
  7  Role
  8  Report Status
  9  PDF Path
  10 Drive URL
  11 Enrichment Confidence
  12 Error Notes
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

import config

logger = logging.getLogger(__name__)

# Column indices (1-based for gspread)
COL_TIMESTAMP = 1
COL_FULL_NAME = 2
COL_EMAIL = 3
COL_COMPANY = 4
COL_WEBSITE = 5
COL_INDUSTRY = 6
COL_ROLE = 7
COL_STATUS = 8
COL_PDF_PATH = 9
COL_DRIVE_URL = 10
COL_CONFIDENCE = 11
COL_ERRORS = 12


class SheetsLogger:
    def __init__(self) -> None:
        self._sheet = None
        self._enabled = bool(config.GOOGLE_SHEET_ID)

    def _get_sheet(self):
        """Lazy-initialise the gspread worksheet."""
        if self._sheet is not None:
            return self._sheet
        try:
            import gspread
            from google.oauth2.service_account import Credentials

            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
            creds = Credentials.from_service_account_file(
                config.GOOGLE_SERVICE_ACCOUNT_JSON, scopes=scopes
            )
            gc = gspread.authorize(creds)
            spreadsheet = gc.open_by_key(config.GOOGLE_SHEET_ID)
            self._sheet = spreadsheet.sheet1
            self._ensure_header()
        except Exception as exc:
            logger.warning("Could not initialise Google Sheets: %s", exc)
            self._sheet = None
        return self._sheet

    def _ensure_header(self) -> None:
        """Add header row if the sheet is empty."""
        try:
            sheet = self._sheet
            if sheet and not sheet.row_values(1):
                sheet.append_row(
                    [
                        "Timestamp",
                        "Full Name",
                        "Email",
                        "Company",
                        "Website",
                        "Industry",
                        "Role",
                        "Report Status",
                        "PDF Path",
                        "Drive URL",
                        "Enrichment Confidence",
                        "Error Notes",
                    ]
                )
        except Exception as exc:
            logger.debug("Header check failed: %s", exc)

    def append_lead(self, lead_data: dict) -> Optional[int]:
        """
        Append a new row for the lead and return the row index.
        Returns None if Sheets is not configured or fails.
        """
        if not self._enabled:
            return None
        try:
            sheet = self._get_sheet()
            if sheet is None:
                return None

            row = [
                datetime.now().isoformat(timespec="seconds"),
                lead_data.get("full_name", ""),
                lead_data.get("email", ""),
                lead_data.get("company_name", ""),
                lead_data.get("company_website", ""),
                lead_data.get("industry", ""),
                lead_data.get("role", ""),
                "processing",  # initial status
                "",  # PDF path
                "",  # Drive URL
                "",  # confidence
                "",  # errors
            ]
            sheet.append_row(row)
            # Return the index of the row we just added
            return len(sheet.get_all_values())
        except Exception as exc:
            logger.warning("Sheets append_lead failed: %s", exc)
            return None

    def update_status(
        self,
        row_index: int,
        status: str,
        pdf_path: str = "",
        drive_url: str = "",
        confidence: str = "",
        error_notes: str = "",
    ) -> None:
        """Update status and optional fields for an existing row."""
        if not self._enabled or row_index is None:
            return
        try:
            sheet = self._get_sheet()
            if sheet is None:
                return

            updates = {
                COL_STATUS: status,
            }
            if pdf_path:
                updates[COL_PDF_PATH] = pdf_path
            if drive_url:
                updates[COL_DRIVE_URL] = drive_url
            if confidence:
                updates[COL_CONFIDENCE] = confidence
            if error_notes:
                updates[COL_ERRORS] = error_notes

            for col, value in updates.items():
                sheet.update_cell(row_index, col, value)

        except Exception as exc:
            logger.warning("Sheets update_status failed: %s", exc)
