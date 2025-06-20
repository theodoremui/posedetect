"""
Video Processing Package

This package provides video processing functionality for pose detection:
- Video overlay generation
- Frame extraction and processing
- Raw frame and overlay frame extraction
- Video format conversions
"""

from .overlay_generator import VideoOverlayGenerator, OverlayConfig
from .frame_extraction import (
    FrameExtractionConfig,
    FrameExtractionManager,
    RawFrameExtractor,
    OverlayFrameExtractor
)

__all__ = [
    'VideoOverlayGenerator', 
    'OverlayConfig',
    'FrameExtractionConfig',
    'FrameExtractionManager',
    'RawFrameExtractor',
    'OverlayFrameExtractor'
] 