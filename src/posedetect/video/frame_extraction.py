"""
Frame Extraction Module

This module provides comprehensive frame extraction capabilities for videos,
including raw frame extraction and overlay frame extraction with pose annotations.
The design follows SOLID principles and provides extensible, configurable solutions.
"""

import cv2
import os
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

from ..models.pose import Pose
from ..core.visualizer import PoseVisualizer

logger = logging.getLogger(__name__)


@dataclass
class FrameExtractionConfig:
    """
    Configuration for frame extraction operations.
    
    This class encapsulates all configuration options for extracting frames
    from videos, supporting both raw frames and overlay frames with poses.
    """
    
    # Output directory configuration
    base_output_directory: str = "outputs"
    directory_name_template: str = "{type}_{video_name}_{timestamp}"
    
    # Frame file configuration
    frame_filename_template: str = "frame_{:05d}.{extension}"
    
    # Raw frame extraction settings
    extract_raw_frames: bool = True
    raw_image_format: str = "jpg"
    raw_image_quality: int = 95
    raw_resize_factor: Optional[float] = None
    
    # Overlay frame extraction settings
    extract_overlay_frames: bool = True
    overlay_image_format: str = "jpg"
    overlay_image_quality: int = 95
    overlay_resize_factor: Optional[float] = None
    
    # Pose visualization settings for overlays
    skeleton_color: Tuple[int, int, int] = (0, 255, 0)    # Green
    joint_color: Tuple[int, int, int] = (255, 0, 0)       # Red
    confidence_threshold: float = 0.1
    line_thickness: int = 2
    joint_radius: int = 4
    show_confidence: bool = True
    show_person_id: bool = True
    font_scale: float = 0.5
    font_color: Tuple[int, int, int] = (255, 255, 255)    # White
    
    # Processing settings
    frame_range: Optional[Tuple[int, int]] = None
    frame_skip: int = 1
    
    # Progress and logging
    enable_progress_callback: bool = True
    log_extraction_details: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if self.raw_image_quality < 0 or self.raw_image_quality > 100:
            raise ValueError("Raw image quality must be between 0 and 100")
        
        if self.overlay_image_quality < 0 or self.overlay_image_quality > 100:
            raise ValueError("Overlay image quality must be between 0 and 100")
        
        if self.raw_image_format.lower() not in ['jpg', 'jpeg', 'png', 'bmp']:
            raise ValueError(f"Unsupported raw image format: {self.raw_image_format}")
        
        if self.overlay_image_format.lower() not in ['jpg', 'jpeg', 'png', 'bmp']:
            raise ValueError(f"Unsupported overlay image format: {self.overlay_image_format}")
        
        if self.frame_range and len(self.frame_range) != 2:
            raise ValueError("Frame range must be a tuple of (start, end)")
        
        if self.frame_range and self.frame_range[0] >= self.frame_range[1]:
            raise ValueError("Frame range start must be less than end")
        
        if self.frame_skip < 1:
            raise ValueError("Frame skip must be at least 1")
    
    def get_directory_name(self, extraction_type: str, video_name: str, timestamp: str) -> str:
        """
        Generate directory name based on template.
        
        Args:
            extraction_type: Type of extraction ('frames' or 'overlay')
            video_name: Name of the video file (without extension)
            timestamp: Timestamp string
            
        Returns:
            Generated directory name
        """
        return self.directory_name_template.format(
            type=extraction_type,
            video_name=video_name,
            timestamp=timestamp
        )
    
    def get_frame_filename(self, frame_number: int, image_format: str) -> str:
        """
        Generate frame filename based on template.
        
        Args:
            frame_number: Frame number (0-based)
            image_format: Image format extension
            
        Returns:
            Generated filename
        """
        return self.frame_filename_template.format(frame_number, extension=image_format)


class IFrameExtractor(ABC):
    """
    Abstract base class for frame extraction implementations.
    
    This ABC defines the contract that all frame extractors must follow,
    enabling different extraction strategies while maintaining consistency.
    """
    
    @abstractmethod
    def extract_frames(
        self,
        video_path: Union[str, Path],
        output_directory: Union[str, Path],
        config: FrameExtractionConfig,
        progress_callback: Optional[callable] = None,
        **kwargs
    ) -> List[Path]:
        """
        Extract frames from video.
        
        Args:
            video_path: Path to input video
            output_directory: Directory to save frames
            config: Frame extraction configuration
            progress_callback: Optional progress callback
            **kwargs: Additional arguments specific to extractor type
            
        Returns:
            List of paths to extracted frame files
        """
        pass


class RawFrameExtractor(IFrameExtractor):
    """
    Extractor for raw video frames without any overlays.
    
    This class handles the extraction of unmodified frames from video files,
    applying only basic transformations like resizing if configured.
    """
    
    def __init__(self):
        """Initialize the raw frame extractor."""
        self.logger = logger.getChild('RawFrameExtractor')
    
    def extract_frames(
        self,
        video_path: Union[str, Path],
        output_directory: Union[str, Path],
        config: FrameExtractionConfig,
        progress_callback: Optional[callable] = None,
        **kwargs
    ) -> List[Path]:
        """
        Extract raw frames from video.
        
        Args:
            video_path: Path to input video
            output_directory: Directory to save frames
            config: Frame extraction configuration
            progress_callback: Optional progress callback
            
        Returns:
            List of paths to extracted frame files
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If video cannot be opened or processed
        """
        video_path = Path(video_path)
        output_directory = Path(output_directory)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Create output directory
        output_directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Extracting raw frames from: {video_path}")
        self.logger.info(f"Output directory: {output_directory}")
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")
        
        extracted_files = []
        
        try:
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Determine frame range
            start_frame = 0 if config.frame_range is None else config.frame_range[0]
            end_frame = total_frames if config.frame_range is None else min(config.frame_range[1], total_frames)
            
            self.logger.info(
                f"Processing frames {start_frame}-{end_frame} "
                f"from video: {width}x{height}, {total_frames} total frames"
            )
            
            frame_count = 0
            extracted_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Check frame range
                if frame_count < start_frame:
                    frame_count += 1
                    continue
                
                if frame_count >= end_frame:
                    break
                
                # Skip frames if configured
                if frame_count % config.frame_skip != 0:
                    frame_count += 1
                    continue
                
                # Apply resize if configured
                if config.raw_resize_factor:
                    new_width = int(width * config.raw_resize_factor)
                    new_height = int(height * config.raw_resize_factor)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # Generate filename
                filename = config.get_frame_filename(frame_count, config.raw_image_format)
                output_path = output_directory / filename
                
                # Save frame
                if self._save_frame(frame, output_path, config.raw_image_format, config.raw_image_quality):
                    extracted_files.append(output_path)
                    extracted_count += 1
                
                # Progress callback
                if progress_callback:
                    progress = (frame_count - start_frame + 1) / (end_frame - start_frame)
                    progress_callback(progress, frame_count, end_frame - start_frame)
                
                frame_count += 1
            
            self.logger.info(f"Extracted {extracted_count} raw frames to: {output_directory}")
            
        finally:
            cap.release()
        
        return extracted_files
    
    def _save_frame(
        self, 
        frame: np.ndarray, 
        output_path: Path, 
        image_format: str, 
        quality: int
    ) -> bool:
        """
        Save a frame to disk.
        
        Args:
            frame: Frame array to save
            output_path: Path to save the frame
            image_format: Image format ('jpg', 'png', etc.)
            quality: Image quality (0-100)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if image_format.lower() in ['jpg', 'jpeg']:
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
                success = cv2.imwrite(str(output_path), frame, encode_params)
            elif image_format.lower() == 'png':
                # PNG quality is compression level (0-9), convert from 0-100 scale
                compression = max(0, min(9, int((100 - quality) / 11)))
                encode_params = [cv2.IMWRITE_PNG_COMPRESSION, compression]
                success = cv2.imwrite(str(output_path), frame, encode_params)
            else:
                success = cv2.imwrite(str(output_path), frame)
            
            if not success:
                self.logger.error(f"Failed to save frame: {output_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error saving frame {output_path}: {e}")
            return False


class OverlayFrameExtractor(IFrameExtractor):
    """
    Extractor for video frames with pose overlays.
    
    This class handles the extraction of frames with pose annotations overlaid,
    using the pose detection results to draw skeletons and joint points.
    """
    
    def __init__(self):
        """Initialize the overlay frame extractor."""
        self.logger = logger.getChild('OverlayFrameExtractor')
        self.visualizer = None
    
    def extract_frames(
        self,
        video_path: Union[str, Path],
        output_directory: Union[str, Path],
        config: FrameExtractionConfig,
        progress_callback: Optional[callable] = None,
        poses: Optional[List[Pose]] = None,
        poses_by_frame: Optional[Dict[int, List[Pose]]] = None,
        **kwargs
    ) -> List[Path]:
        """
        Extract frames with pose overlays.
        
        Args:
            video_path: Path to input video
            output_directory: Directory to save frames
            config: Frame extraction configuration
            progress_callback: Optional progress callback
            poses: List of pose objects (alternative to poses_by_frame)
            poses_by_frame: Dictionary mapping frame numbers to poses
            
        Returns:
            List of paths to extracted frame files
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If no pose data provided
            RuntimeError: If video cannot be opened or processed
        """
        video_path = Path(video_path)
        output_directory = Path(output_directory)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Prepare pose data
        if poses_by_frame is None:
            if poses is None:
                raise ValueError("Either poses or poses_by_frame must be provided")
            poses_by_frame = self._group_poses_by_frame(poses)
        
        # Initialize visualizer with config settings
        self.visualizer = PoseVisualizer(
            keypoint_radius=config.joint_radius,
            connection_thickness=config.line_thickness,
            confidence_threshold=config.confidence_threshold
        )
        
        # Create output directory
        output_directory.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Extracting overlay frames from: {video_path}")
        self.logger.info(f"Output directory: {output_directory}")
        self.logger.info(f"Poses available for {len(poses_by_frame)} frames")
        
        # Open video
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")
        
        extracted_files = []
        
        try:
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # Determine frame range
            start_frame = 0 if config.frame_range is None else config.frame_range[0]
            end_frame = total_frames if config.frame_range is None else min(config.frame_range[1], total_frames)
            
            self.logger.info(
                f"Processing frames {start_frame}-{end_frame} "
                f"from video: {width}x{height}, {total_frames} total frames"
            )
            
            frame_count = 0
            extracted_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Check frame range
                if frame_count < start_frame:
                    frame_count += 1
                    continue
                
                if frame_count >= end_frame:
                    break
                
                # Skip frames if configured
                if frame_count % config.frame_skip != 0:
                    frame_count += 1
                    continue
                
                # Apply resize if configured
                if config.overlay_resize_factor:
                    new_width = int(width * config.overlay_resize_factor)
                    new_height = int(height * config.overlay_resize_factor)
                    frame = cv2.resize(frame, (new_width, new_height))
                
                # Get poses for this frame
                frame_poses = poses_by_frame.get(frame_count, [])
                
                # Draw poses on frame
                overlay_frame = self._draw_poses_on_frame(frame, frame_poses, config)
                
                # Generate filename
                filename = config.get_frame_filename(frame_count, config.overlay_image_format)
                output_path = output_directory / filename
                
                # Save frame
                if self._save_frame(overlay_frame, output_path, config.overlay_image_format, config.overlay_image_quality):
                    extracted_files.append(output_path)
                    extracted_count += 1
                
                # Progress callback
                if progress_callback:
                    progress = (frame_count - start_frame + 1) / (end_frame - start_frame)
                    progress_callback(progress, frame_count, end_frame - start_frame)
                
                frame_count += 1
            
            self.logger.info(f"Extracted {extracted_count} overlay frames to: {output_directory}")
            
        finally:
            cap.release()
        
        return extracted_files
    
    def _group_poses_by_frame(self, poses: List[Pose]) -> Dict[int, List[Pose]]:
        """
        Group poses by frame number.
        
        Args:
            poses: List of poses to group
            
        Returns:
            Dictionary mapping frame numbers to lists of poses
        """
        poses_by_frame = {}
        
        for pose in poses:
            frame_number = getattr(pose, 'frame_number', 0)
            if frame_number not in poses_by_frame:
                poses_by_frame[frame_number] = []
            poses_by_frame[frame_number].append(pose)
        
        self.logger.info(f"Grouped poses into {len(poses_by_frame)} frames")
        return poses_by_frame
    
    def _draw_poses_on_frame(
        self, 
        frame: np.ndarray, 
        poses: List[Pose], 
        config: FrameExtractionConfig
    ) -> np.ndarray:
        """
        Draw poses on a video frame.
        
        Args:
            frame: Input video frame
            poses: List of poses to draw
            config: Configuration with visualization settings
            
        Returns:
            Frame with poses drawn
        """
        # Create a copy to avoid modifying original
        overlay_frame = frame.copy()
        
        for pose in poses:
            # Filter joints by confidence threshold
            valid_joints = [
                joint for joint in pose.joints 
                if joint.keypoint.confidence >= config.confidence_threshold
            ]
            
            if not valid_joints:
                continue
            
            # Draw skeleton connections
            self._draw_skeleton(overlay_frame, valid_joints, config)
            
            # Draw joints
            self._draw_joints(overlay_frame, valid_joints, config)
            
            # Draw person info
            if config.show_person_id or config.show_confidence:
                self._draw_person_info(overlay_frame, pose, valid_joints, config)
        
        return overlay_frame
    
    def _draw_skeleton(
        self, 
        frame: np.ndarray, 
        joints: List, 
        config: FrameExtractionConfig
    ) -> None:
        """Draw skeleton connections between joints."""
        # Define skeleton connections (simplified)
        connections = [
            ('nose', 'left_eye'), ('nose', 'right_eye'),
            ('left_eye', 'left_ear'), ('right_eye', 'right_ear'),
            ('nose', 'left_shoulder'), ('nose', 'right_shoulder'),
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_elbow'), ('left_elbow', 'left_wrist'),
            ('right_shoulder', 'right_elbow'), ('right_elbow', 'right_wrist'),
            ('left_shoulder', 'left_hip'), ('right_shoulder', 'right_hip'),
            ('left_hip', 'right_hip'),
            ('left_hip', 'left_knee'), ('left_knee', 'left_ankle'),
            ('right_hip', 'right_knee'), ('right_knee', 'right_ankle'),
        ]
        
        # Create joint lookup by name
        joint_dict = {joint.name: joint for joint in joints}
        
        for start_name, end_name in connections:
            if start_name in joint_dict and end_name in joint_dict:
                start_joint = joint_dict[start_name]
                end_joint = joint_dict[end_name]
                
                start_point = (int(start_joint.keypoint.x), int(start_joint.keypoint.y))
                end_point = (int(end_joint.keypoint.x), int(end_joint.keypoint.y))
                
                cv2.line(frame, start_point, end_point, config.skeleton_color, config.line_thickness)
    
    def _draw_joints(
        self, 
        frame: np.ndarray, 
        joints: List, 
        config: FrameExtractionConfig
    ) -> None:
        """Draw joint points."""
        for joint in joints:
            center = (int(joint.keypoint.x), int(joint.keypoint.y))
            cv2.circle(frame, center, config.joint_radius, config.joint_color, -1)
    
    def _draw_person_info(
        self, 
        frame: np.ndarray, 
        pose, 
        joints: List, 
        config: FrameExtractionConfig
    ) -> None:
        """Draw person ID and confidence information."""
        if not joints:
            return
        
        # Find a good position for text (near the head/top of pose)
        head_joints = ['nose', 'left_eye', 'right_eye']
        text_joint = None
        
        for joint_name in head_joints:
            for joint in joints:
                if joint.name == joint_name:
                    text_joint = joint
                    break
            if text_joint:
                break
        
        # Fall back to first joint if no head joint found
        if not text_joint:
            text_joint = joints[0]
        
        # Position text above the joint
        text_x = int(text_joint.keypoint.x)
        text_y = int(text_joint.keypoint.y - 10)
        
        # Build text string
        text_parts = []
        if config.show_person_id:
            text_parts.append(f"P{pose.person_id}")
        if config.show_confidence:
            text_parts.append(f"{pose.confidence:.2f}")
        
        if text_parts:
            text = " ".join(text_parts)
            cv2.putText(
                frame, text, (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX, config.font_scale,
                config.font_color, 1, cv2.LINE_AA
            )
    
    def _save_frame(
        self, 
        frame: np.ndarray, 
        output_path: Path, 
        image_format: str, 
        quality: int
    ) -> bool:
        """Save a frame to disk."""
        try:
            if image_format.lower() in ['jpg', 'jpeg']:
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
                success = cv2.imwrite(str(output_path), frame, encode_params)
            elif image_format.lower() == 'png':
                compression = max(0, min(9, int((100 - quality) / 11)))
                encode_params = [cv2.IMWRITE_PNG_COMPRESSION, compression]
                success = cv2.imwrite(str(output_path), frame, encode_params)
            else:
                success = cv2.imwrite(str(output_path), frame)
            
            if not success:
                self.logger.error(f"Failed to save frame: {output_path}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error saving frame {output_path}: {e}")
            return False


class FrameExtractionManager:
    """
    High-level manager for coordinating frame extraction operations.
    
    This class provides a unified interface for extracting both raw frames
    and overlay frames, handling directory management and orchestrating
    the different extraction types.
    """
    
    def __init__(self, config: Optional[FrameExtractionConfig] = None):
        """
        Initialize the frame extraction manager.
        
        Args:
            config: Frame extraction configuration
        """
        self.config = config or FrameExtractionConfig()
        self.raw_extractor = RawFrameExtractor()
        self.overlay_extractor = OverlayFrameExtractor()
        self.logger = logger.getChild('FrameExtractionManager')
    
    def extract_all_frame_types(
        self,
        video_path: Union[str, Path],
        poses: Optional[List[Pose]] = None,
        base_output_directory: Optional[Union[str, Path]] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, List[Path]]:
        """
        Extract both raw frames and overlay frames from a video.
        
        Args:
            video_path: Path to input video
            poses: List of pose objects for overlay frames
            base_output_directory: Base directory for outputs
            progress_callback: Optional progress callback
            
        Returns:
            Dictionary with extraction results:
            {
                'raw_frames': [list of raw frame paths],
                'overlay_frames': [list of overlay frame paths],
                'directories': {
                    'raw': path_to_raw_directory,
                    'overlay': path_to_overlay_directory
                }
            }
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If configuration is invalid
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        # Set up base output directory
        if base_output_directory is None:
            base_output_directory = Path(self.config.base_output_directory)
        else:
            base_output_directory = Path(base_output_directory)
        
        # Generate timestamp and video name
        timestamp = self._generate_timestamp()
        video_name = self._get_video_name(video_path)
        
        # Create output directories
        directories = self._create_output_directories(video_name, timestamp, base_output_directory)
        
        results = {
            'raw_frames': [],
            'overlay_frames': [],
            'directories': directories
        }
        
        # Extract raw frames if configured
        if self.config.extract_raw_frames:
            self.logger.info("Starting raw frame extraction...")
            
            def raw_progress_callback(progress: float, frame: int, total: int):
                if progress_callback:
                    # Adjust progress for raw frame phase (0-50%)
                    adjusted_progress = progress * 0.5
                    progress_callback(adjusted_progress, frame, total, "raw_frames")
            
            try:
                raw_frames = self.raw_extractor.extract_frames(
                    video_path=video_path,
                    output_directory=directories['raw'],
                    config=self.config,
                    progress_callback=raw_progress_callback if self.config.enable_progress_callback else None
                )
                results['raw_frames'] = raw_frames
                self.logger.info(f"Extracted {len(raw_frames)} raw frames")
                
            except Exception as e:
                self.logger.error(f"Raw frame extraction failed: {e}")
                raise
        
        # Extract overlay frames if configured and poses available
        if self.config.extract_overlay_frames and poses:
            self.logger.info("Starting overlay frame extraction...")
            
            def overlay_progress_callback(progress: float, frame: int, total: int):
                if progress_callback:
                    # Adjust progress for overlay frame phase (50-100%)
                    adjusted_progress = 0.5 + (progress * 0.5)
                    progress_callback(adjusted_progress, frame, total, "overlay_frames")
            
            try:
                overlay_frames = self.overlay_extractor.extract_frames(
                    video_path=video_path,
                    output_directory=directories['overlay'],
                    config=self.config,
                    poses=poses,
                    progress_callback=overlay_progress_callback if self.config.enable_progress_callback else None
                )
                results['overlay_frames'] = overlay_frames
                self.logger.info(f"Extracted {len(overlay_frames)} overlay frames")
                
            except Exception as e:
                self.logger.error(f"Overlay frame extraction failed: {e}")
                raise
        
        elif self.config.extract_overlay_frames and not poses:
            self.logger.warning("Overlay frame extraction requested but no poses provided")
        
        return results
    
    def _create_output_directories(
        self, 
        video_name: str, 
        timestamp: str, 
        base_directory: Path
    ) -> Dict[str, Path]:
        """
        Create output directories for frame extraction.
        
        Args:
            video_name: Name of the video (without extension)
            timestamp: Timestamp string
            base_directory: Base output directory
            
        Returns:
            Dictionary mapping extraction types to directory paths
        """
        directories = {}
        
        # Create raw frames directory
        if self.config.extract_raw_frames:
            raw_dir_name = self.config.get_directory_name("frames", video_name, timestamp)
            raw_directory = base_directory / raw_dir_name
            raw_directory.mkdir(parents=True, exist_ok=True)
            directories['raw'] = raw_directory
            self.logger.info(f"Created raw frames directory: {raw_directory}")
        
        # Create overlay frames directory
        if self.config.extract_overlay_frames:
            overlay_dir_name = self.config.get_directory_name("overlay", video_name, timestamp)
            overlay_directory = base_directory / overlay_dir_name
            overlay_directory.mkdir(parents=True, exist_ok=True)
            directories['overlay'] = overlay_directory
            self.logger.info(f"Created overlay frames directory: {overlay_directory}")
        
        return directories
    
    def _get_video_name(self, video_path: Path) -> str:
        """
        Extract video name from path (without extension).
        
        Args:
            video_path: Path to video file
            
        Returns:
            Video name without extension
        """
        return video_path.stem
    
    def _generate_timestamp(self) -> str:
        """
        Generate timestamp string for directory naming.
        
        Returns:
            Timestamp string in format YYYYMMDD_HHMMSS
        """
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def get_extraction_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a summary of extraction results.
        
        Args:
            results: Results from extract_all_frame_types
            
        Returns:
            Summary dictionary with extraction statistics
        """
        summary = {
            'total_raw_frames': len(results.get('raw_frames', [])),
            'total_overlay_frames': len(results.get('overlay_frames', [])),
            'directories_created': len(results.get('directories', {})),
            'extraction_types': list(results.get('directories', {}).keys()),
            'output_directories': {
                k: str(v) for k, v in results.get('directories', {}).items()
            }
        }
        
        return summary 