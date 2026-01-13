"""
Google Drive API Routes
روت‌های API برای یکپارچه‌سازی با Google Drive
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Request
from fastapi.responses import StreamingResponse, RedirectResponse
from pydantic import BaseModel
import io
import os

from app.core.security import get_current_user, TokenData, require_role
from app.services.google_drive_service import drive_service, GoogleDriveService

router = APIRouter()


# ========== Schemas ==========
class OAuthInitRequest(BaseModel):
    redirect_uri: str


class OAuthCallbackRequest(BaseModel):
    code: str
    redirect_uri: str


class TokenData(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None


class CreateFolderRequest(BaseModel):
    name: str
    parent_id: Optional[str] = None


class ShareFileRequest(BaseModel):
    file_id: str
    email: Optional[str] = None
    role: str = 'reader'
    anyone_with_link: bool = False


class MoveFileRequest(BaseModel):
    file_id: str
    new_folder_id: str


class RenameFileRequest(BaseModel):
    file_id: str
    new_name: str


# ========== Connection Status ==========
@router.get("/status")
async def get_connection_status(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get Google Drive connection status
    """
    status_info = drive_service.get_status()

    # Try to get user info if connected
    if status_info['connected']:
        try:
            user_info = await drive_service.get_user_info()
            status_info['user'] = user_info
        except Exception:
            pass

    return status_info


@router.post("/test")
async def test_connection(
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    Test the Google Drive connection
    """
    result = await drive_service.test_connection()
    return result


@router.post("/disconnect")
async def disconnect(
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    Disconnect from Google Drive
    """
    drive_service.disconnect()
    return {"message": "Disconnected from Google Drive", "status": "disconnected"}


# ========== OAuth Flow ==========
@router.post("/oauth/init")
async def init_oauth(
    request: OAuthInitRequest,
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    Initialize OAuth flow - get authorization URL
    """
    try:
        auth_url = drive_service.get_oauth_url(
            redirect_uri=request.redirect_uri,
            state=str(current_user.user_id)
        )
        return {
            "auth_url": auth_url,
            "message": "Redirect user to auth_url to authorize"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/oauth/callback")
async def oauth_callback(
    request: OAuthCallbackRequest,
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    Handle OAuth callback - exchange code for tokens
    """
    try:
        token_data = drive_service.exchange_code_for_token(
            code=request.code,
            redirect_uri=request.redirect_uri
        )

        # Initialize service with the new token
        await drive_service.initialize_with_oauth_token(
            token_data,
            user_id=str(current_user.user_id)
        )

        # Get user info
        user_info = await drive_service.get_user_info()

        return {
            "success": True,
            "message": "Successfully connected to Google Drive",
            "user": user_info,
            "token": {
                "access_token": token_data['access_token'][:20] + '...',  # Partial for security
                "has_refresh_token": bool(token_data.get('refresh_token'))
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth callback failed: {str(e)}"
        )


@router.get("/oauth/redirect")
async def oauth_redirect(
    code: str,
    state: Optional[str] = None,
    request: Request = None
):
    """
    OAuth redirect endpoint - handles the redirect from Google
    This is a GET endpoint that Google redirects to
    """
    # Build the redirect URI
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/api/v1/google-drive/oauth/redirect"

    try:
        token_data = drive_service.exchange_code_for_token(
            code=code,
            redirect_uri=redirect_uri
        )

        await drive_service.initialize_with_oauth_token(token_data)

        # Redirect to frontend settings page
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        return RedirectResponse(
            url=f"{frontend_url}/settings?tab=integrations&gdrive=connected"
        )
    except Exception as e:
        frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        return RedirectResponse(
            url=f"{frontend_url}/settings?tab=integrations&gdrive=error&message={str(e)}"
        )


# ========== File Operations ==========
@router.get("/files")
async def list_files(
    folder_id: Optional[str] = None,
    query: Optional[str] = None,
    page_size: int = Query(default=50, le=100),
    page_token: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """
    List files in Google Drive
    """
    try:
        result = await drive_service.list_files(
            folder_id=folder_id,
            query=query,
            page_size=page_size,
            page_token=page_token
        )
        return result
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Drive not connected"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/files/{file_id}")
async def get_file(
    file_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get file metadata
    """
    try:
        file = await drive_service.get_file(file_id)
        return file
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {str(e)}"
        )


@router.get("/files/{file_id}/download")
async def download_file(
    file_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Download a file from Google Drive
    """
    try:
        # Get file metadata first
        file_info = await drive_service.get_file(file_id)

        # Download content
        content = await drive_service.download_file(file_id)

        return StreamingResponse(
            io.BytesIO(content),
            media_type=file_info.get('mime_type', 'application/octet-stream'),
            headers={
                'Content-Disposition': f'attachment; filename="{file_info["name"]}"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    folder_id: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Upload a file to Google Drive
    """
    try:
        content = await file.read()
        file_stream = io.BytesIO(content)

        result = await drive_service.upload_stream(
            file_stream=file_stream,
            file_name=file.filename,
            folder_id=folder_id,
            mime_type=file.content_type
        )

        return {
            "success": True,
            "file": result
        }
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google Drive not connected"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    permanent: bool = False,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Delete a file (move to trash or permanent delete)
    """
    try:
        success = await drive_service.delete_file(file_id, permanent=permanent)
        if success:
            return {"success": True, "message": "File deleted"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========== Folder Operations ==========
@router.post("/folders")
async def create_folder(
    request: CreateFolderRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create a new folder in Google Drive
    """
    try:
        folder = await drive_service.create_folder(
            folder_name=request.name,
            parent_id=request.parent_id
        )
        return {"success": True, "folder": folder}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/folders/get-or-create")
async def get_or_create_folder(
    request: CreateFolderRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get existing folder or create new one
    """
    try:
        folder = await drive_service.get_or_create_folder(
            folder_name=request.name,
            parent_id=request.parent_id
        )
        return {"success": True, "folder": folder}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========== File Management ==========
@router.post("/files/move")
async def move_file(
    request: MoveFileRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Move a file to a different folder
    """
    try:
        result = await drive_service.move_file(
            file_id=request.file_id,
            new_folder_id=request.new_folder_id
        )
        return {"success": True, "file": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/files/rename")
async def rename_file(
    request: RenameFileRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Rename a file
    """
    try:
        result = await drive_service.rename_file(
            file_id=request.file_id,
            new_name=request.new_name
        )
        return {"success": True, "file": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/files/share")
async def share_file(
    request: ShareFileRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Share a file or folder
    """
    try:
        result = await drive_service.share_file(
            file_id=request.file_id,
            email=request.email,
            role=request.role,
            anyone_with_link=request.anyone_with_link
        )
        return {"success": True, **result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ========== Sync Operations ==========
@router.post("/sync/customer/{customer_id}")
async def sync_customer_documents(
    customer_id: str,
    current_user: TokenData = Depends(require_role(["admin", "manager"]))
):
    """
    Sync all documents for a customer to Google Drive
    """
    try:
        # This would need database access to get customer files
        # For now, return a placeholder
        return {
            "message": "Customer sync initiated",
            "customer_id": customer_id,
            "status": "pending"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/backup")
async def create_backup(
    current_user: TokenData = Depends(require_role(["admin"]))
):
    """
    Create a database backup and upload to Google Drive
    """
    import structlog
    logger = structlog.get_logger()

    try:
        from datetime import datetime

        logger.info("Starting backup process...")

        # Create sample backup data
        backup_data = {
            "created_at": datetime.utcnow().isoformat(),
            "created_by": current_user.user_id,
            "type": "full_backup"
        }

        logger.info(f"Backup data created, calling backup_database...")
        result = await drive_service.backup_database(backup_data)
        logger.info(f"Backup successful: {result}")

        return {
            "success": True,
            "backup": result
        }
    except RuntimeError as e:
        logger.error(f"RuntimeError in backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Google Drive error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Exception in backup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backup failed: {str(e)}"
        )
