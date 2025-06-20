"""
Processing job model for tracking background processing tasks.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Text, Float, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
import uuid

from app.core.database import Base


class JobStatus(str, enum.Enum):
    """Processing job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class ProcessingJobModel(Base):
    """Processing job model for tracking background processing tasks."""
    
    __tablename__ = "processing_jobs"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    
    # Foreign key to file
    file_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("files.id", ondelete="CASCADE"), 
        nullable=False
    )
    
    # Job information
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus), 
        default=JobStatus.PENDING, 
        nullable=False
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Processing configuration
    config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    command: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Results and error handling
    result_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result_files: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of output files
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_traceback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Process information
    process_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    return_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow, 
        nullable=False
    )
    
    # Performance metrics
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cpu_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_usage: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Relationships
    file: Mapped["FileModel"] = relationship(
        "FileModel",
        back_populates="processing_jobs"
    )
    
    def __repr__(self) -> str:
        return f"<ProcessingJobModel(id={self.id}, file_id={self.file_id}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "file_id": self.file_id,
            "status": self.status.value,
            "progress": self.progress,
            "config": self.config,
            "result_data": self.result_data,
            "result_files": self.result_files,
            "error_message": self.error_message,
            "process_id": self.process_id,
            "return_code": self.return_code,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
        }
    
    @property
    def is_active(self) -> bool:
        """Check if job is currently active (pending or processing)."""
        return self.status in (JobStatus.PENDING, JobStatus.PROCESSING)
    
    @property
    def is_finished(self) -> bool:
        """Check if job is finished (completed, error, or cancelled)."""
        return self.status in (JobStatus.COMPLETED, JobStatus.ERROR, JobStatus.CANCELLED) 