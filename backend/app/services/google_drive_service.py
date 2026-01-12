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
import io

from app.core.config import settings


# OAuth Scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive'
]


class GoogleDriveService:
    """
    سرویس یکپارچه‌سازی با Google Drive
    امکان آپلود، دانلود و همگام‌سازی فایل‌ها
    پشتیبانی از OAuth و Service Account
    """

    def __init__(self):
        self.credentials_file = settings.GOOGLE_CREDENTIALS_FILE
        self.folder_id = settings.GOOGLE_DRIVE_FOLDER_ID
        self.service = None
        self._initialized = False
        self._user_tokens: Dict[str, Dict] = {}  # Store user tokens in memory
        self._connection_status = 'disconnected'

    def get_status(self) -> Dict[str, Any]:
        """Get connection status"""
        return {
            'connected': self._initialized,
            'status': self._connection_status,
            'folder_id': self.folder_id
        }

    def _get_client_config(self) -> Dict[str, Any]:
        """Get OAuth client configuration"""
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')

        if not client_id or not client_secret:
            # Try to get from credentials file
            if self.credentials_file and os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'r') as f:
                    creds = json.load(f)
                    if 'web' in creds:
                        return creds
                    elif 'installed' in creds:
                        return creds
                    client_id = creds.get('client_id')
                    client_secret = creds.get('client_secret')

        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

    def get_oauth_url(self, redirect_uri: str, state: str = None) -> str:
        """
        Get OAuth authorization URL for user authentication
        """
        from google_auth_oauthlib.flow import Flow

        client_config = self._get_client_config()

        if not client_config.get('web', {}).get('client_id'):
            raise ValueError("Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET")

        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = redirect_uri

        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state or 'default',
            prompt='consent'
        )

        return authorization_url

    def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        """
        from google_auth_oauthlib.flow import Flow

        client_config = self._get_client_config()

        flow = Flow.from_client_config(client_config, scopes=SCOPES)
        flow.redirect_uri = redirect_uri

        flow.fetch_token(code=code)
        credentials = flow.credentials

        token_data = {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None,
            'scopes': list(credentials.scopes) if credentials.scopes else []
        }

        return token_data

    async def initialize_with_oauth_token(self, token_data: Dict[str, Any], user_id: str = 'default'):
        """Initialize with user OAuth token"""
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        try:
            credentials = Credentials(
                token=token_data['access_token'],
                refresh_token=token_data.get('refresh_token'),
                token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
                client_id=token_data.get('client_id') or os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=token_data.get('client_secret') or os.getenv('GOOGLE_CLIENT_SECRET')
            )

            self.service = await asyncio.to_thread(
                build, 'drive', 'v3', credentials=credentials
            )
            self._initialized = True
            self._connection_status = 'connected'
            self._user_tokens[user_id] = token_data

            return True
        except Exception as e:
            self._connection_status = f'error: {str(e)}'
            raise

    async def initialize(self):
        """راه‌اندازی سرویس با Service Account"""
        if self._initialized:
            return

        # First check for OAuth tokens in environment
        oauth_token = os.getenv('GOOGLE_OAUTH_TOKEN')
        if oauth_token:
            try:
                token_data = json.loads(oauth_token)
                await self.initialize_with_oauth_token(token_data)
                return
            except Exception as e:
                print(f"Failed to initialize with OAuth token: {e}")

        # Fall back to service account
        if not self.credentials_file or not os.path.exists(self.credentials_file):
            # Try credentials from environment variable
            creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
            if creds_json:
                try:
                    from google.oauth2 import service_account
                    from googleapiclient.discovery import build

                    creds_data = json.loads(creds_json)
                    credentials = service_account.Credentials.from_service_account_info(
                        creds_data,
                        scopes=SCOPES
                    )
                    self.service = await asyncio.to_thread(
                        build, 'drive', 'v3', credentials=credentials
                    )
                    self._initialized = True
                    self._connection_status = 'connected'
                    return
                except Exception as e:
                    print(f"Failed to initialize with credentials JSON: {e}")

            raise ValueError("Google credentials not found. Set GOOGLE_CREDENTIALS_FILE or GOOGLE_CREDENTIALS_JSON")

        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_file,
            scopes=SCOPES
        )

        self.service = await asyncio.to_thread(
            build, 'drive', 'v3', credentials=credentials
        )
        self._initialized = True
        self._connection_status = 'connected'

    async def _ensure_initialized(self):
        """اطمینان از راه‌اندازی"""
        if not self._initialized:
            await self.initialize()

    async def get_user_info(self) -> Optional[Dict[str, Any]]:
        """Get connected user/service account information"""
        await self._ensure_initialized()

        try:
            about = await asyncio.to_thread(
                self.service.about().get(fields='user,storageQuota').execute
            )
            return {
                'email': about['user'].get('emailAddress'),
                'name': about['user'].get('displayName'),
                'photo': about['user'].get('photoLink'),
                'storage': about.get('storageQuota', {})
            }
        except Exception as e:
            print(f"Error getting user info: {e}")
            return None

    async def test_connection(self) -> Dict[str, Any]:
        """Test the Google Drive connection"""
        try:
            await self._ensure_initialized()
            user_info = await self.get_user_info()
            return {
                'connected': True,
                'status': 'connected',
                'user': user_info
            }
        except Exception as e:
            return {
                'connected': False,
                'status': 'error',
                'error': str(e)
            }

    def disconnect(self):
        """Disconnect from Google Drive"""
        self.service = None
        self._initialized = False
        self._connection_status = 'disconnected'
        self._user_tokens.clear()

    async def create_folder(
        self,
        folder_name: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """ایجاد پوشه در Drive"""
        await self._ensure_initialized()

        parent = parent_id or self.folder_id
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
        }

        if parent:
            file_metadata['parents'] = [parent]

        try:
            folder = await asyncio.to_thread(
                self.service.files().create(
                    body=file_metadata,
                    fields='id, name, webViewLink'
                ).execute
            )
        except Exception as e:
            # If parent folder not found, create at root level
            if 'File not found' in str(e) and parent:
                print(f"Parent folder {parent} not found, creating at root level")
                file_metadata.pop('parents', None)
                folder = await asyncio.to_thread(
                    self.service.files().create(
                        body=file_metadata,
                        fields='id, name, webViewLink'
                    ).execute
                )
            else:
                raise

        return {
            'id': folder.get('id'),
            'name': folder.get('name'),
            'url': folder.get('webViewLink')
        }

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
        }

        parent = folder_id or self.folder_id
        if parent:
            file_metadata['parents'] = [parent]

        media = MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True
        )

        file = await asyncio.to_thread(
            self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, size, mimeType'
            ).execute
        )

        return {
            'id': file.get('id'),
            'name': file.get('name'),
            'url': file.get('webViewLink'),
            'size': file.get('size'),
            'mime_type': file.get('mimeType')
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
        }

        parent = folder_id or self.folder_id
        if parent:
            file_metadata['parents'] = [parent]

        media = MediaInMemoryUpload(
            content,
            mimetype=mime_type,
            resumable=True
        )

        file = await asyncio.to_thread(
            self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, size'
            ).execute
        )

        return {
            'id': file.get('id'),
            'name': file.get('name'),
            'url': file.get('webViewLink'),
            'size': file.get('size')
        }

    async def upload_stream(
        self,
        file_stream: BinaryIO,
        file_name: str,
        folder_id: Optional[str] = None,
        mime_type: str = 'application/octet-stream'
    ) -> Dict[str, Any]:
        """آپلود استریم فایل به Drive"""
        await self._ensure_initialized()

        from googleapiclient.http import MediaIoBaseUpload

        file_metadata = {
            'name': file_name,
        }

        parent = folder_id or self.folder_id
        if parent:
            file_metadata['parents'] = [parent]

        media = MediaIoBaseUpload(
            file_stream,
            mimetype=mime_type,
            resumable=True
        )

        file = await asyncio.to_thread(
            self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, size, mimeType'
            ).execute
        )

        return {
            'id': file.get('id'),
            'name': file.get('name'),
            'url': file.get('webViewLink'),
            'size': file.get('size'),
            'mime_type': file.get('mimeType')
        }

    async def download_file(
        self,
        file_id: str,
        destination_path: str = None
    ) -> bytes:
        """دانلود فایل از Drive"""
        await self._ensure_initialized()

        from googleapiclient.http import MediaIoBaseDownload

        request = self.service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = await asyncio.to_thread(downloader.next_chunk)

        content = fh.getvalue()

        if destination_path:
            async with aiofiles.open(destination_path, 'wb') as f:
                await f.write(content)

        return content

    async def list_files(
        self,
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        page_size: int = 100,
        page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """لیست فایل‌ها در پوشه"""
        await self._ensure_initialized()

        q_parts = ["trashed = false"]

        parent_id = folder_id or self.folder_id
        if parent_id:
            q_parts.append(f"'{parent_id}' in parents")

        if query:
            q_parts.append(f"name contains '{query}'")

        q = " and ".join(q_parts)

        params = {
            'q': q,
            'pageSize': page_size,
            'fields': "nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink, iconLink, thumbnailLink)"
        }

        if page_token:
            params['pageToken'] = page_token

        try:
            result = await asyncio.to_thread(
                self.service.files().list(**params).execute
            )
        except Exception as e:
            # If folder not found, try listing without parent filter
            if 'File not found' in str(e) and parent_id:
                print(f"Folder {parent_id} not found, listing all files instead")
                q_parts = ["trashed = false"]
                if query:
                    q_parts.append(f"name contains '{query}'")
                params['q'] = " and ".join(q_parts)
                result = await asyncio.to_thread(
                    self.service.files().list(**params).execute
                )
            else:
                raise

        files = result.get('files', [])
        return {
            'files': [
                {
                    'id': f['id'],
                    'name': f['name'],
                    'mime_type': f.get('mimeType'),
                    'size': f.get('size'),
                    'created': f.get('createdTime'),
                    'modified': f.get('modifiedTime'),
                    'url': f.get('webViewLink'),
                    'icon': f.get('iconLink'),
                    'thumbnail': f.get('thumbnailLink'),
                    'is_folder': f.get('mimeType') == 'application/vnd.google-apps.folder'
                }
                for f in files
            ],
            'next_page_token': result.get('nextPageToken')
        }

    async def get_file(self, file_id: str) -> Dict[str, Any]:
        """Get file metadata"""
        await self._ensure_initialized()

        file = await asyncio.to_thread(
            self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, modifiedTime, webViewLink, parents, description'
            ).execute
        )

        return {
            'id': file.get('id'),
            'name': file.get('name'),
            'mime_type': file.get('mimeType'),
            'size': file.get('size'),
            'created': file.get('createdTime'),
            'modified': file.get('modifiedTime'),
            'url': file.get('webViewLink'),
            'parents': file.get('parents', []),
            'description': file.get('description')
        }

    async def delete_file(self, file_id: str, permanent: bool = False) -> bool:
        """حذف فایل از Drive"""
        await self._ensure_initialized()

        try:
            if permanent:
                await asyncio.to_thread(
                    self.service.files().delete(fileId=file_id).execute
                )
            else:
                await asyncio.to_thread(
                    self.service.files().update(
                        fileId=file_id,
                        body={'trashed': True}
                    ).execute
                )
            return True
        except Exception:
            return False

    async def move_file(self, file_id: str, new_folder_id: str) -> Dict[str, Any]:
        """Move file to a different folder"""
        await self._ensure_initialized()

        # Get current parents
        file = await asyncio.to_thread(
            self.service.files().get(fileId=file_id, fields='parents').execute
        )
        previous_parents = ",".join(file.get('parents', []))

        # Move to new folder
        file = await asyncio.to_thread(
            self.service.files().update(
                fileId=file_id,
                addParents=new_folder_id,
                removeParents=previous_parents,
                fields='id, name, parents, webViewLink'
            ).execute
        )

        return {
            'id': file.get('id'),
            'name': file.get('name'),
            'parents': file.get('parents'),
            'url': file.get('webViewLink')
        }

    async def rename_file(self, file_id: str, new_name: str) -> Dict[str, Any]:
        """Rename a file"""
        await self._ensure_initialized()

        file = await asyncio.to_thread(
            self.service.files().update(
                fileId=file_id,
                body={'name': new_name},
                fields='id, name, webViewLink'
            ).execute
        )

        return {
            'id': file.get('id'),
            'name': file.get('name'),
            'url': file.get('webViewLink')
        }

    async def share_file(
        self,
        file_id: str,
        email: str = None,
        role: str = 'reader',
        share_type: str = 'user',
        anyone_with_link: bool = False
    ) -> Dict[str, Any]:
        """Share a file or folder"""
        await self._ensure_initialized()

        if anyone_with_link:
            permission = {
                'type': 'anyone',
                'role': role
            }
        else:
            permission = {
                'type': share_type,
                'role': role,
                'emailAddress': email
            }

        result = await asyncio.to_thread(
            self.service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=bool(email)
            ).execute
        )

        # Get shareable link
        file = await asyncio.to_thread(
            self.service.files().get(fileId=file_id, fields='webViewLink').execute
        )

        return {
            'permission_id': result.get('id'),
            'link': file.get('webViewLink')
        }

    async def get_or_create_folder(
        self,
        folder_name: str,
        parent_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """دریافت یا ایجاد پوشه"""
        await self._ensure_initialized()

        parent = parent_id or self.folder_id

        q_parts = [
            f"name = '{folder_name}'",
            "mimeType = 'application/vnd.google-apps.folder'",
            "trashed = false"
        ]

        if parent:
            q_parts.append(f"'{parent}' in parents")

        q = " and ".join(q_parts)

        try:
            result = await asyncio.to_thread(
                self.service.files().list(
                    q=q,
                    fields="files(id, name, webViewLink)"
                ).execute
            )
        except Exception as e:
            # If parent folder not found, try without parent filter
            if 'File not found' in str(e) and parent:
                print(f"Parent folder {parent} not found, searching in root")
                q_parts = [
                    f"name = '{folder_name}'",
                    "mimeType = 'application/vnd.google-apps.folder'",
                    "trashed = false"
                ]
                q = " and ".join(q_parts)
                result = await asyncio.to_thread(
                    self.service.files().list(
                        q=q,
                        fields="files(id, name, webViewLink)"
                    ).execute
                )
                parent = None  # Create at root level if needed
            else:
                raise

        files = result.get('files', [])
        if files:
            folder = files[0]
            return {
                'id': folder.get('id'),
                'name': folder.get('name'),
                'url': folder.get('webViewLink'),
                'created': False
            }

        # Create folder - use None for parent if original parent was not found
        folder = await self.create_folder(folder_name, parent if parent != self.folder_id else None)
        folder['created'] = True
        return folder

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
                        folder_id=customer_folder['id']
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
            'folder_id': customer_folder['id'],
            'folder_url': customer_folder.get('url'),
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
            folder_id=backup_folder['id'],
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
