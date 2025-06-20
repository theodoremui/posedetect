"""
Configuration settings for the PoseDetect API server.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    DEBUG: bool = Field(default=True, env="DEBUG")
    HOST: str = Field(default="127.0.0.1", env="HOST")
    PORT: int = Field(default=8000, env="PORT")
    
    # CORS Settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        env="ALLOWED_ORIGINS"
    )
    
    # Database Settings
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./posedetect.db",
        env="DATABASE_URL"
    )
    
    # File Storage Settings
    BASE_DIR: Path = Field(default=Path(__file__).parent.parent.parent.parent)
    UPLOAD_DIR: Path = Field(default=None)
    OUTPUT_DIR: Path = Field(default=None)
    TEMP_DIR: Path = Field(default=None)
    
    MAX_FILE_SIZE: int = Field(default=500 * 1024 * 1024, env="MAX_FILE_SIZE")  # 500MB
    ALLOWED_FILE_TYPES: List[str] = Field(
        default=[
            "video/mp4", "video/avi", "video/mov", "video/mkv", "video/webm",
            "image/jpeg", "image/jpg", "image/png", "image/gif", "image/bmp", "image/webp"
        ],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Video2Pose CLI Settings
    VIDEO2POSE_SCRIPT: Path = Field(default=None)
    VIDEO2POSE_TIMEOUT: int = Field(default=3600, env="VIDEO2POSE_TIMEOUT")  # 1 hour
    
    # Background Task Settings
    MAX_CONCURRENT_JOBS: int = Field(default=2, env="MAX_CONCURRENT_JOBS")
    JOB_CLEANUP_INTERVAL: int = Field(default=300, env="JOB_CLEANUP_INTERVAL")  # 5 minutes
    
    # Security Settings
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE: Optional[str] = Field(default=None, env="LOG_FILE")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Set default paths relative to base directory
        if self.UPLOAD_DIR is None:
            self.UPLOAD_DIR = self.BASE_DIR / "uploads"
        
        if self.OUTPUT_DIR is None:
            self.OUTPUT_DIR = self.BASE_DIR / "outputs"
        
        if self.TEMP_DIR is None:
            self.TEMP_DIR = self.BASE_DIR / "temp"
        
        if self.VIDEO2POSE_SCRIPT is None:
            self.VIDEO2POSE_SCRIPT = self.BASE_DIR / "src" / "video2pose.py"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings() 