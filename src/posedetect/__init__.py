"""
PoseDetect: OpenPose-based pose detection for videos and images.

This package provides a comprehensive solution for extracting human pose
information from video and image files using OpenPose.
"""

__version__ = "0.1.0"
__author__ = "PoseDetect Team"

from .core.detector import PoseDetector
from .models.pose import Pose, Joint, KeyPoint

__all__ = ["PoseDetector", "Pose", "Joint", "KeyPoint"] 