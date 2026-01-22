"""
Google Drive Service
سرویس Google Drive برای پشتیبان‌گیری
"""
import os
import json
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import structlog

logger = structlog.get_logger()


class GoogleDriveService:
    """Google Drive integration for backup and file storage"""

    def __init__(self):
        self.service = None
        self._initialized = False
        self.folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
        self.credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON')

    def get_status(self) -> Dict[str, Any]:
        """Get connection status"""
        return {
            "connected": self._initialized and self.service is not None,
            "folder_configured": bool(self.folder_id),
            "credentials_configured": bool(self.credentials_json)
        }

    async def initialize(self):
        """Initialize Google Drive service"""
        if self._initialized:
            return

        if not self.credentials_json:
            logger.warning("GOOGLE_CREDENTIALS_JSON not configured")
            return

        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            creds_data = json.loads(self.credentials_json)
            credentials = service_account.Credentials.from_service_account_info(
                creds_data,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )

            self.service = await asyncio.to_thread(
                build, 'drive', 'v3', credentials=credentials
            )
            self._initialized = True
            logger.info("Google Drive service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive: {e}")

    async def _ensure_initialized(self):
        """Ensure service is initialized"""
        if not self._initialized:
            await self.initialize()
        if not self.service:
            raise RuntimeError("Google Drive not initialized. Check credentials.")

    async def list_files(self, folder_id: Optional[str] = None) -> List[Dict]:
        """List files in folder"""
        await self._ensure_initialized()

        parent = folder_id or self.folder_id
        if not parent:
            raise RuntimeError("GOOGLE_DRIVE_FOLDER_ID not configured")

        query = f"'{parent}' in parents and trashed = false"
        result = await asyncio.to_thread(
            self.service.files().list(
                q=query,
                pageSize=100,
                fields="files(id, name, mimeType, size, createdTime)"
            ).execute
        )

        return [
            {
                "id": f["id"],
                "name": f["name"],
                "type": f["mimeType"],
                "size": f.get("size"),
                "created": f.get("createdTime")
            }
            for f in result.get("files", [])
        ]

    async def upload_file(self, content: bytes, filename: str, mime_type: str = "application/octet-stream") -> Dict:
        """Upload file to Google Drive"""
        await self._ensure_initialized()

        if not self.folder_id:
            raise RuntimeError("GOOGLE_DRIVE_FOLDER_ID not configured")

        from googleapiclient.http import MediaInMemoryUpload

        file_metadata = {
            "name": filename,
            "parents": [self.folder_id]
        }

        media = MediaInMemoryUpload(content, mimetype=mime_type)

        file = await asyncio.to_thread(
            self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, name, webViewLink"
            ).execute
        )

        return {
            "id": file["id"],
            "name": file["name"],
            "url": file.get("webViewLink")
        }

    async def backup_database(self, data: Dict[str, Any]) -> Dict:
        """Create database backup"""
        await self._ensure_initialized()

        filename = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        content = json.dumps(data, indent=2, default=str).encode('utf-8')

        result = await self.upload_file(content, filename, "application/json")

        return {
            "backup_id": result["id"],
            "backup_name": filename,
            "url": result.get("url"),
            "timestamp": datetime.utcnow().isoformat()
        }

    async def download_file(self, file_id: str) -> bytes:
        """Download file from Google Drive"""
        await self._ensure_initialized()

        from googleapiclient.http import MediaIoBaseDownload
        import io

        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = await asyncio.to_thread(downloader.next_chunk)

        return fh.getvalue()


# Global instance
drive_service = GoogleDriveService()
