"""
Google Drive Service Module
ماژول همگام‌سازی با Google Drive
"""
import os
import json
import asyncio
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime
import aiofiles

from app.core.config import settings


class GoogleDriveService:
    """
    سرویس یکپارچه‌سازی با Google Drive
    امکان آپلود، دانلود و همگام‌سازی فایل‌ها
    """

    def __init__(self):
        self.credentials_file = settings.GOOGLE_CREDENTIALS_FILE
        self.folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
        self.service = None
        self._initialized = False

    async def initialize(self):
        """راه‌اندازی سرویس"""
        if self._initialized:
            return

        if not self.credentials_file or not os.path.exists(self.credentials_file):
            raise ValueError("Google credentials file not found")

        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_file,
            scopes=['https://www.googleapis.com/auth/drive']
        )

        self.service = await asyncio.to_thread(
            build, 'drive', 'v3', credentials=credentials
        )
        self._initialized = True

    async def _ensure_initialized(self):
        """اطمینان از راه‌اندازی"""
        if not self._initialized:
            await self.initialize()

    async def create_folder(
        self,
        folder_name: str,
        parent_id: Optional[str] = None
    ) -> str:
        """ایجاد پوشه در Drive"""
        await self._ensure_initialized()

        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id or self.folder_id]
        }

        folder = await asyncio.to_thread(
            self.service.files().create,
            body=file_metadata,
            fields='id'
        )
        result = await asyncio.to_thread(folder.execute)
        return result.get('id')

    async def upload_file(
        self,
        file_path: str,
        file_name: Optional[str] = None,
        folder_id: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """آپلود فایل به Drive"""
        await self._ensure_initialized()

        from googleapiclient.http import MediaFileUpload

        if not file_name:
            file_name = os.path.basename(file_path)

        file_metadata = {
            'name': file_name,
            'parents': [folder_id or self.folder_id]
        }

        media = MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True
        )

        file = await asyncio.to_thread(
            self.service.files().create,
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink, size'
        )
        result = await asyncio.to_thread(file.execute)

        return {
            'id': result.get('id'),
            'name': result.get('name'),
            'url': result.get('webViewLink'),
            'size': result.get('size')
        }

    async def upload_bytes(
        self,
        content: bytes,
        file_name: str,
        folder_id: Optional[str] = None,
        mime_type: str = 'application/octet-stream'
    ) -> Dict[str, Any]:
        """آپلود محتوای باینری به Drive"""
        await self._ensure_initialized()

        from googleapiclient.http import MediaInMemoryUpload

        file_metadata = {
            'name': file_name,
            'parents': [folder_id or self.folder_id]
        }

        media = MediaInMemoryUpload(
            content,
            mimetype=mime_type,
            resumable=True
        )

        file = await asyncio.to_thread(
            self.service.files().create,
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink, size'
        )
        result = await asyncio.to_thread(file.execute)

        return {
            'id': result.get('id'),
            'name': result.get('name'),
            'url': result.get('webViewLink'),
            'size': result.get('size')
        }

    async def download_file(
        self,
        file_id: str,
        destination_path: str
    ) -> str:
        """دانلود فایل از Drive"""
        await self._ensure_initialized()

        from googleapiclient.http import MediaIoBaseDownload
        import io

        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = await asyncio.to_thread(downloader.next_chunk)

        async with aiofiles.open(destination_path, 'wb') as f:
            await f.write(fh.getvalue())

        return destination_path

    async def list_files(
        self,
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """لیست فایل‌ها در پوشه"""
        await self._ensure_initialized()

        parent_id = folder_id or self.folder_id
        q = f"'{parent_id}' in parents and trashed = false"
        if query:
            q += f" and {query}"

        results = await asyncio.to_thread(
            self.service.files().list,
            q=q,
            pageSize=page_size,
            fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)"
        )
        result = await asyncio.to_thread(results.execute)

        files = result.get('files', [])
        return [
            {
                'id': f['id'],
                'name': f['name'],
                'mime_type': f.get('mimeType'),
                'size': f.get('size'),
                'created': f.get('createdTime'),
                'modified': f.get('modifiedTime'),
                'url': f.get('webViewLink')
            }
            for f in files
        ]

    async def delete_file(self, file_id: str) -> bool:
        """حذف فایل از Drive"""
        await self._ensure_initialized()

        try:
            await asyncio.to_thread(
                self.service.files().delete(fileId=file_id).execute
            )
            return True
        except Exception:
            return False

    async def get_or_create_folder(
        self,
        folder_name: str,
        parent_id: Optional[str] = None
    ) -> str:
        """دریافت یا ایجاد پوشه"""
        await self._ensure_initialized()

        parent = parent_id or self.folder_id
        q = f"name = '{folder_name}' and '{parent}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"

        results = await asyncio.to_thread(
            self.service.files().list,
            q=q,
            fields="files(id)"
        )
        result = await asyncio.to_thread(results.execute)

        files = result.get('files', [])
        if files:
            return files[0]['id']

        return await self.create_folder(folder_name, parent)

    async def sync_customer_folder(
        self,
        account_no: str,
        local_files: List[str]
    ) -> Dict[str, Any]:
        """همگام‌سازی پوشه مشتری"""
        await self._ensure_initialized()

        # ایجاد/دریافت پوشه مشتری
        customer_folder = await self.get_or_create_folder(f"Customer_{account_no}")

        synced_files = []
        errors = []

        for file_path in local_files:
            if os.path.exists(file_path):
                try:
                    result = await self.upload_file(
                        file_path,
                        folder_id=customer_folder
                    )
                    synced_files.append(result)
                except Exception as e:
                    errors.append({
                        'file': file_path,
                        'error': str(e)
                    })
            else:
                errors.append({
                    'file': file_path,
                    'error': 'File not found'
                })

        return {
            'folder_id': customer_folder,
            'synced': synced_files,
            'errors': errors,
            'timestamp': datetime.utcnow().isoformat()
        }

    async def backup_database(
        self,
        backup_data: Dict[str, Any],
        backup_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """پشتیبان‌گیری از دیتابیس به Drive"""
        await self._ensure_initialized()

        if not backup_name:
            backup_name = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

        # ایجاد پوشه پشتیبان‌گیری
        backup_folder = await self.get_or_create_folder("Backups")

        # آپلود
        content = json.dumps(backup_data, indent=2, default=str).encode('utf-8')
        result = await self.upload_bytes(
            content,
            backup_name,
            folder_id=backup_folder,
            mime_type='application/json'
        )

        return {
            'backup_id': result['id'],
            'backup_name': backup_name,
            'url': result['url'],
            'timestamp': datetime.utcnow().isoformat()
        }


class GoogleDriveSyncManager:
    """
    مدیر همگام‌سازی خودکار با Google Drive
    """

    def __init__(self, drive_service: GoogleDriveService):
        self.drive_service = drive_service
        self.sync_interval = settings.GOOGLE_DRIVE_SYNC_INTERVAL
        self._running = False
        self._task = None

    async def start(self):
        """شروع همگام‌سازی خودکار"""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._sync_loop())

    async def stop(self):
        """توقف همگام‌سازی"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _sync_loop(self):
        """حلقه همگام‌سازی"""
        while self._running:
            try:
                await self._perform_sync()
            except Exception as e:
                print(f"Sync error: {e}")

            await asyncio.sleep(self.sync_interval)

    async def _perform_sync(self):
        """اجرای همگام‌سازی"""
        # این متد می‌تواند برای همگام‌سازی تغییرات جدید استفاده شود
        pass


# Singleton instances
drive_service = GoogleDriveService()
sync_manager = GoogleDriveSyncManager(drive_service)
