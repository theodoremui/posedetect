"""
Pydantic schemas for file-related API operations.
"""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, validator

from app.models.file import FileStatus


class FileBase(BaseModel):
    """Base file schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255, description="File name")


class FileCreate(FileBase):
    """Schema for creating a new file."""
    original_name: str = Field(..., min_length=1, max_length=255, description="Original file name")
    size: int = Field(..., ge=0, description="File size in bytes")
    mime_type: str = Field(..., min_length=1, max_length=100, description="MIME type")
    file_path: str = Field(..., min_length=1, max_length=500, description="File path on disk")
    metadata_: Optional[str] = Field(None, description="File metadata as JSON string")


class FileUpdate(BaseModel):
    """Schema for updating file details."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="New file name")
    status: Optional[FileStatus] = Field(None, description="File processing status")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    metadata_: Optional[str] = Field(None, description="Updated metadata as JSON string")


class FileResponse(BaseModel):
    """Schema for file response data."""
    id: str = Field(..., description="Unique file identifier")
    name: str = Field(..., description="File name")
    original_name: str = Field(..., description="Original file name")
    size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    status: FileStatus = Field(..., description="Processing status")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
    upload_date: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last updated timestamp")
    metadata_: Optional[str] = Field(None, description="File metadata as JSON string")
    
    class Config:
        from_attributes = True


class FileStats(BaseModel):
    """Schema for file statistics."""
    total_files: int = Field(..., description="Total number of files")
    total_size: int = Field(..., description="Total size of all files in bytes")
    files_by_status: dict[str, int] = Field(..., description="File count by status")
    files_by_type: dict[str, int] = Field(..., description="File count by MIME type")
    upload_history: list[dict[str, Any]] = Field(..., description="Upload history data")


class UrlUploadRequest(BaseModel):
    """Schema for URL upload request."""
    url: str = Field(..., min_length=1, description="URL to download file from")
    
    @validator('url')
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v 