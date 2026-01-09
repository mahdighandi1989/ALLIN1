"""
File Service Module
ماژول مدیریت فایل‌ها
"""
import os
import uuid
import hashlib
import aiofiles
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime
from pathlib import Path

from app.core.config import settings


class FileService:
    """
    سرویس مدیریت فایل‌ها
    آپلود، دانلود و مدیریت فایل‌های سیستم
    """

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_size = settings.MAX_UPLOAD_SIZE
        self.allowed_types = settings.ALLOWED_FILE_TYPES

    async def initialize(self):
        """ایجاد دایرکتوری آپلود"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # ایجاد زیرپوشه‌ها
        subdirs = ['attachments', 'exports', 'temp', 'backups']
        for subdir in subdirs:
            (self.upload_dir / subdir).mkdir(exist_ok=True)

    def _generate_filename(self, original_name: str) -> str:
        """تولید نام فایل یکتا"""
        ext = Path(original_name).suffix.lower()
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        return f"{timestamp}_{unique_id}{ext}"

    def _get_file_hash(self, content: bytes) -> str:
        """محاسبه هش فایل"""
        return hashlib.sha256(content).hexdigest()

    def _validate_file(self, filename: str, size: int) -> tuple[bool, str]:
        """اعتبارسنجی فایل"""
        ext = Path(filename).suffix.lower()

        if ext not in self.allowed_types:
            return False, f"File type '{ext}' not allowed"

        if size > self.max_size:
            max_mb = self.max_size / (1024 * 1024)
            return False, f"File size exceeds {max_mb}MB limit"

        return True, ""

    async def save_file(
        self,
        content: bytes,
        original_name: str,
        subfolder: str = "attachments",
        customer_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """ذخیره فایل"""
        # اعتبارسنجی
        valid, error = self._validate_file(original_name, len(content))
        if not valid:
            raise ValueError(error)

        # تعیین مسیر
        if customer_id:
            folder = self.upload_dir / subfolder / customer_id
        else:
            folder = self.upload_dir / subfolder

        folder.mkdir(parents=True, exist_ok=True)

        # ذخیره فایل
        filename = self._generate_filename(original_name)
        file_path = folder / filename

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        return {
            'filename': filename,
            'original_name': original_name,
            'path': str(file_path),
            'relative_path': str(file_path.relative_to(self.upload_dir)),
            'size': len(content),
            'hash': self._get_file_hash(content),
            'extension': Path(original_name).suffix.lower(),
            'mime_type': self._get_mime_type(original_name),
            'created_at': datetime.utcnow().isoformat()
        }

    async def read_file(self, file_path: str) -> bytes:
        """خواندن فایل"""
        full_path = Path(file_path)
        if not full_path.is_absolute():
            full_path = self.upload_dir / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        async with aiofiles.open(full_path, 'rb') as f:
            return await f.read()

    async def delete_file(self, file_path: str) -> bool:
        """حذف فایل"""
        full_path = Path(file_path)
        if not full_path.is_absolute():
            full_path = self.upload_dir / file_path

        if full_path.exists():
            full_path.unlink()
            return True
        return False

    async def list_files(
        self,
        subfolder: str = "attachments",
        customer_id: Optional[str] = None,
        extension: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """لیست فایل‌ها"""
        if customer_id:
            folder = self.upload_dir / subfolder / customer_id
        else:
            folder = self.upload_dir / subfolder

        if not folder.exists():
            return []

        files = []
        for file_path in folder.iterdir():
            if file_path.is_file():
                if extension and not file_path.suffix.lower() == extension:
                    continue

                stat = file_path.stat()
                files.append({
                    'filename': file_path.name,
                    'path': str(file_path),
                    'relative_path': str(file_path.relative_to(self.upload_dir)),
                    'size': stat.st_size,
                    'extension': file_path.suffix.lower(),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        return sorted(files, key=lambda x: x['modified'], reverse=True)

    def _get_mime_type(self, filename: str) -> str:
        """تشخیص نوع MIME"""
        ext = Path(filename).suffix.lower()
        mime_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
        }
        return mime_types.get(ext, 'application/octet-stream')

    async def create_export(
        self,
        data: Dict[str, Any],
        format: str = "json",
        filename_prefix: str = "export"
    ) -> Dict[str, Any]:
        """ایجاد فایل خروجی"""
        import json

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

        if format == "json":
            content = json.dumps(data, indent=2, default=str).encode('utf-8')
            filename = f"{filename_prefix}_{timestamp}.json"
        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            if isinstance(data, list) and data:
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            content = output.getvalue().encode('utf-8')
            filename = f"{filename_prefix}_{timestamp}.csv"
        else:
            raise ValueError(f"Unsupported format: {format}")

        return await self.save_file(content, filename, subfolder="exports")

    async def cleanup_temp_files(self, max_age_hours: int = 24):
        """پاکسازی فایل‌های موقت"""
        temp_folder = self.upload_dir / "temp"
        if not temp_folder.exists():
            return 0

        deleted_count = 0
        threshold = datetime.utcnow().timestamp() - (max_age_hours * 3600)

        for file_path in temp_folder.iterdir():
            if file_path.is_file():
                if file_path.stat().st_mtime < threshold:
                    file_path.unlink()
                    deleted_count += 1

        return deleted_count


# Singleton instance
file_service = FileService()
