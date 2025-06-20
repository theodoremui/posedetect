"""
File model for storing uploaded file information.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
import uuid

from app.core.database import Base


class FileStatus(str, enum.Enum):
    """File processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class FileModel(Base):
    """File model for storing uploaded file information."""
    
    __tablename__ = "files"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    
    # File information
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Status and processing
    status: Mapped[FileStatus] = mapped_column(
        SQLEnum(FileStatus), 
        default=FileStatus.PENDING, 
        nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    upload_date: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # Metadata
    metadata_: Mapped[Optional[str]] = mapped_column("metadata", Text, nullable=True)
    
    # Relationships
    processing_jobs: Mapped[list["ProcessingJobModel"]] = relationship(
        "ProcessingJobModel",
        back_populates="file",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<FileModel(id={self.id}, name={self.name}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "original_name": self.original_name,
            "size": self.size,
            "mime_type": self.mime_type,
            "status": self.status.value,
            "error_message": self.error_message,
            "upload_date": self.upload_date.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata_,
        } 