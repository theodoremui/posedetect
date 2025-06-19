"""
Video processing utilities for pose detection.

This module provides utilities for reading video files, extracting frames,
and handling video metadata operations.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Iterator, Tuple, Optional, Dict, Any
from loguru import logger


class VideoProcessor:
    """
    Handles video processing operations for pose detection.
    
    This class provides methods for reading video files, extracting frames,
    and managing video metadata following the Single Responsibility Principle.
    """
    
    def __init__(self, video_path: Path):
        """
        Initialize the video processor.
        
        Args:
            video_path: Path to the video file
        """
        self.video_path = video_path
        self.cap: Optional[cv2.VideoCapture] = None
        self._metadata: Optional[Dict[str, Any]] = None
        
    def __enter__(self) -> "VideoProcessor":
        """Context manager entry."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
    
    def open(self) -> None:
        """Open the video file."""
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise ValueError(f"Failed to open video: {self.video_path}")
        logger.info(f"Opened video: {self.video_path}")
    
    def close(self) -> None:
        """Close the video file."""
        if self.cap:
            self.cap.release()
            self.cap = None
            logger.info(f"Closed video: {self.video_path}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get video metadata.
        
        Returns:
            Dictionary containing video metadata
        """
        if not self.cap:
            raise RuntimeError("Video not opened")
        
        if self._metadata is None:
            self._metadata = {
                'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': self.cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'duration': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) / self.cap.get(cv2.CAP_PROP_FPS)
            }
        
        return self._metadata
    
    def get_frame_at_time(self, timestamp: float) -> Optional[np.ndarray]:
        """
        Get frame at specific timestamp.
        
        Args:
            timestamp: Timestamp in seconds
            
        Returns:
            Frame as numpy array or None if failed
        """
        if not self.cap:
            raise RuntimeError("Video not opened")
        
        metadata = self.get_metadata()
        frame_number = int(timestamp * metadata['fps'])
        
        if frame_number >= metadata['frame_count']:
            return None
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ret, frame = self.cap.read()
        
        return frame if ret else None
    
    def iterate_frames(self) -> Iterator[Tuple[int, float, np.ndarray]]:
        """
        Iterate through all frames in the video.
        
        Yields:
            Tuple of (frame_number, timestamp, frame_array)
        """
        if not self.cap:
            raise RuntimeError("Video not opened")
        
        metadata = self.get_metadata()
        frame_number = 0
        
        # Reset to beginning
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                break
            
            timestamp = frame_number / metadata['fps']
            yield frame_number, timestamp, frame
            frame_number += 1
        
        logger.info(f"Processed {frame_number} frames from video")
    
    def get_frame_count(self) -> int:
        """Get total number of frames in the video."""
        return self.get_metadata()['frame_count']
    
    def get_fps(self) -> float:
        """Get frames per second of the video."""
        return self.get_metadata()['fps']
    
    def get_resolution(self) -> Tuple[int, int]:
        """Get video resolution as (width, height)."""
        metadata = self.get_metadata()
        return metadata['width'], metadata['height']
    
    @staticmethod
    def load_image(image_path: Path) -> np.ndarray:
        """
        Load an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Image as numpy array
            
        Raises:
            ValueError: If image cannot be loaded
        """
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")
        
        logger.info(f"Loaded image: {image_path}")
        return image 