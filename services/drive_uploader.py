"""
services/drive_uploader.py — Upload PDF to Google Drive and return a shareable URL.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import config

logger = logging.getLogger(__name__)


class DriveUploader:
    def __init__(self) -> None:
        self._service = None
        self._enabled = bool(config.GOOGLE_DRIVE_FOLDER_ID)

    def _get_service(self):
        """Lazy-initialise the Google Drive API service."""
        if self._service is not None:
            return self._service
        try:
            from google.oauth2.service_account import Credentials
            from googleapiclient.discovery import build

            scopes = ["https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_file(
                config.GOOGLE_SERVICE_ACCOUNT_JSON, scopes=scopes
            )
            self._service = build("drive", "v3", credentials=creds)
        except Exception as exc:
            logger.warning("Could not initialise Google Drive service: %s", exc)
            self._service = None
        return self._service

    def upload(self, pdf_path: str, company_name: str) -> Optional[str]:
        """
        Upload the PDF to the configured Drive folder.
        Sets permissions to 'anyone with link can view'.
        Returns the shareable URL or None on failure.
        """
        if not self._enabled:
            return None

        try:
            from googleapiclient.http import MediaFileUpload

            service = self._get_service()
            if service is None:
                return None

            file_name = Path(pdf_path).name
            file_metadata = {
                "name": file_name,
                "parents": [config.GOOGLE_DRIVE_FOLDER_ID],
            }
            media = MediaFileUpload(pdf_path, mimetype="application/pdf", resumable=True)

            uploaded = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            file_id = uploaded.get("id")

            if not file_id:
                logger.warning("Drive upload returned no file ID")
                return None

            # Set public read permission
            service.permissions().create(
                fileId=file_id,
                body={"type": "anyone", "role": "reader"},
            ).execute()

            shareable_url = f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
            logger.info("Uploaded to Drive: %s", shareable_url)
            return shareable_url

        except Exception as exc:
            logger.error("Drive upload failed: %s", exc)
            return None
