"""
File handling utilities for pose detection.

This module provides utilities for validating input files, checking file types,
and handling file operations with proper error handling.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple
from loguru import logger


class FileHandler:
    """
    Handles file operations and validation for pose detection.
    
    This class provides utilities for validating input files, checking supported
    formats, and managing file paths according to the Single Responsibility Principle.
    """
    
    SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
    
    @classmethod
    def validate_input_file(cls, file_path: str) -> Path:
        """
        Validate that the input file exists and is in a supported format.
        
        Args:
            file_path: Path to the input file
            
        Returns:
            Path object of the validated file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        file_extension = path.suffix.lower()
        all_supported = cls.SUPPORTED_IMAGE_FORMATS | cls.SUPPORTED_VIDEO_FORMATS
        
        if file_extension not in all_supported:
            raise ValueError(
                f"Unsupported file format: {file_extension}. "
                f"Supported formats: {', '.join(sorted(all_supported))}"
            )
        
        logger.info(f"Validated input file: {file_path}")
        return path
    
    @classmethod
    def is_image_file(cls, file_path: Path) -> bool:
        """Check if the file is a supported image format."""
        return file_path.suffix.lower() in cls.SUPPORTED_IMAGE_FORMATS
    
    @classmethod
    def is_video_file(cls, file_path: Path) -> bool:
        """Check if the file is a supported video format."""
        return file_path.suffix.lower() in cls.SUPPORTED_VIDEO_FORMATS
    
    @classmethod
    def ensure_output_directory(cls, output_path: str) -> Path:
        """
        Ensure the output directory exists and return the output path.
        
        Args:
            output_path: Path to the output file
            
        Returns:
            Path object of the output file
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory ensured: {path.parent}")
        return path
    
    @classmethod
    def get_file_info(cls, file_path: Path) -> dict:
        """
        Get information about a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file information
        """
        stat = file_path.stat()
        return {
            'name': file_path.name,
            'size': stat.st_size,
            'extension': file_path.suffix.lower(),
            'is_image': cls.is_image_file(file_path),
            'is_video': cls.is_video_file(file_path),
            'absolute_path': str(file_path.absolute())
        } 