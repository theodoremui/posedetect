"""
File management API endpoints.
"""

import logging
from typing import List, Optional
from pathlib import Path
import aiofiles
import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.file import FileModel, FileStatus
from app.services.file_service import FileService
from app.schemas.file import FileResponse, FileCreate, FileUpdate
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Upload a file for processing."""
    try:
        file_service = FileService(db)
        result = await file_service.upload_file(file)
        logger.info(f"File uploaded successfully: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"File upload validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"File upload error: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")


@router.post("/upload-url", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_from_url(
    url: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Upload a file from URL."""
    try:
        file_service = FileService(db)
        result = await file_service.upload_from_url(url)
        logger.info(f"File uploaded from URL successfully: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"URL upload validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except httpx.HTTPError as e:
        logger.error(f"URL download error: {e}")
        raise HTTPException(status_code=400, detail="Failed to download file from URL")
    except Exception as e:
        logger.error(f"URL upload error: {e}")
        raise HTTPException(status_code=500, detail="URL upload failed")


@router.get("/", response_model=List[FileResponse])
async def list_files(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[FileStatus] = None,
    db: AsyncSession = Depends(get_db),
) -> List[FileResponse]:
    """Get list of uploaded files."""
    try:
        file_service = FileService(db)
        files = await file_service.list_files(skip=skip, limit=limit, status_filter=status_filter)
        return files
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve files")


@router.get("/{file_id}", response_model=FileResponse)
async def get_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Get file details by ID."""
    try:
        file_service = FileService(db)
        file = await file_service.get_file(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        return file
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file")


@router.patch("/{file_id}", response_model=FileResponse)
async def update_file(
    file_id: str,
    file_update: FileUpdate,
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Update file details."""
    try:
        file_service = FileService(db)
        file = await file_service.update_file(file_id, file_update)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        logger.info(f"File updated successfully: {file_id}")
        return file
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update file")


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a file."""
    try:
        file_service = FileService(db)
        success = await file_service.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        logger.info(f"File deleted successfully: {file_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete file")


@router.get("/{file_id}/download")
async def download_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Download the original file."""
    try:
        file_service = FileService(db)
        file = await file_service.get_file(file_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_path = Path(file.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        
        return FileResponse(
            path=str(file_path),
            filename=file.original_name,
            media_type=file.mime_type,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to download file")


@router.get("/{file_id}/metadata")
async def get_file_metadata(
    file_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get file metadata."""
    try:
        file_service = FileService(db)
        metadata = await file_service.get_file_metadata(file_id)
        if metadata is None:
            raise HTTPException(status_code=404, detail="File not found")
        return metadata
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving metadata for file {file_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve file metadata") 