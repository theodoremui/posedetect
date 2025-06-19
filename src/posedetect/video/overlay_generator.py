"""
Video Overlay Generator

This module generates video overlays by combining original video frames
with pose detection visualizations.
"""

import cv2
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
import numpy as np

from ..models.pose import Pose, Joint, KeyPoint
from ..core.visualizer import PoseVisualizer

logger = logging.getLogger(__name__)


@dataclass
class OverlayConfig:
    """Configuration for video overlay generation."""
    
    # Video output settings
    output_codec: str = 'mp4v'          # Video codec (mp4v, XVID, etc.)
    output_fps: Optional[float] = None   # Output FPS (None = same as input)
    output_quality: int = 90            # Video quality (0-100)
    
    # Visualization settings
    skeleton_color: Tuple[int, int, int] = (0, 255, 0)     # Green skeleton
    joint_color: Tuple[int, int, int] = (255, 0, 0)        # Red joints
    confidence_threshold: float = 0.1   # Minimum confidence to show
    line_thickness: int = 2             # Skeleton line thickness
    joint_radius: int = 4               # Joint circle radius
    
    # Text overlay settings
    show_confidence: bool = True        # Show confidence scores
    show_person_id: bool = True         # Show person IDs
    font_scale: float = 0.5             # Text size
    font_color: Tuple[int, int, int] = (255, 255, 255)  # White text
    
    # Processing settings
    resize_factor: Optional[float] = None  # Resize frames (None = no resize)
    frame_skip: int = 1                 # Process every Nth frame
    
    # Frame extraction settings
    image_format: str = 'jpg'           # Output image format (jpg, png)
    image_quality: int = 95             # Image quality (for jpg)
    frame_filename_template: str = 'frame_{:05d}.jpg'  # Frame filename template


class VideoOverlayGenerator:
    """
    Generate video overlays with pose detection results.
    
    This class takes an original video and pose detection results,
    then creates a new video with pose visualizations overlaid.
    """
    
    def __init__(self, config: Optional[OverlayConfig] = None):
        """
        Initialize the overlay generator.
        
        Args:
            config: Configuration for overlay generation
        """
        self.config = config or OverlayConfig()
        self.visualizer = PoseVisualizer()
        self.logger = logger

    def generate_overlay_video(
        self,
        input_video_path: Union[str, Path],
        poses_data: Union[List[Pose], str, Path],
        output_video_path: Union[str, Path],
        progress_callback: Optional[callable] = None
    ) -> None:
        """
        Generate overlay video from input video and pose data.
        
        Args:
            input_video_path: Path to original video file
            poses_data: Pose data (list of poses or path to JSON file)
            output_video_path: Path for output video file
            progress_callback: Optional callback for progress updates
            
        Raises:
            FileNotFoundError: If input video doesn't exist
            ValueError: If pose data is invalid
            RuntimeError: If video processing fails
        """
        input_video_path = Path(input_video_path)
        output_video_path = Path(output_video_path)
        
        if not input_video_path.exists():
            raise FileNotFoundError(f"Input video not found: {input_video_path}")
        
        # Load pose data if it's a file path
        if isinstance(poses_data, (str, Path)):
            poses_data = self._load_poses_from_file(poses_data)
        
        # Group poses by frame number for efficient lookup
        poses_by_frame = self._group_poses_by_frame(poses_data)
        
        # Process video
        self._process_video(
            input_video_path, 
            output_video_path, 
            poses_by_frame,
            progress_callback
        )

    def generate_frame_overlays(
        self,
        input_video_path: Union[str, Path],
        poses_data: Union[List[Pose], str, Path],
        output_directory: Union[str, Path],
        frame_range: Optional[Tuple[int, int]] = None,
        progress_callback: Optional[callable] = None
    ) -> List[Path]:
        """
        Generate individual frame images with pose overlays.
        
        Args:
            input_video_path: Path to original video file
            poses_data: Pose data (list of poses or path to JSON file)
            output_directory: Directory to save frame images
            frame_range: Optional tuple (start_frame, end_frame) to limit extraction
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of paths to generated frame images
            
        Raises:
            FileNotFoundError: If input video doesn't exist
            ValueError: If pose data is invalid
            RuntimeError: If video processing fails
        """
        input_video_path = Path(input_video_path)
        output_directory = Path(output_directory)
        
        if not input_video_path.exists():
            raise FileNotFoundError(f"Input video not found: {input_video_path}")
        
        # Create output directory
        output_directory.mkdir(parents=True, exist_ok=True)
        
        # Load pose data if it's a file path
        if isinstance(poses_data, (str, Path)):
            poses_data = self._load_poses_from_file(poses_data)
        
        # Group poses by frame number for efficient lookup
        poses_by_frame = self._group_poses_by_frame(poses_data)
        
        # Extract frames with overlays
        return self._extract_frames_with_overlays(
            input_video_path,
            output_directory,
            poses_by_frame,
            frame_range,
            progress_callback
        )

    def _load_poses_from_file(self, file_path: Union[str, Path]) -> List[Pose]:
        """
        Load poses from JSON file.
        
        Args:
            file_path: Path to JSON file containing pose data
            
        Returns:
            List of Pose objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Pose data file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            poses = []
            
            # Handle different JSON formats
            if 'poses' in data:
                poses_data = data['poses']
            elif isinstance(data, list):
                poses_data = data
            else:
                raise ValueError("Invalid JSON format: expected 'poses' key or list")
            
            for pose_data in poses_data:
                pose = self._dict_to_pose(pose_data)
                poses.append(pose)
            
            self.logger.info(f"Loaded {len(poses)} poses from {file_path}")
            return poses
            
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Invalid pose data file format: {e}")

    def _dict_to_pose(self, pose_data: Dict[str, Any]) -> Pose:
        """
        Convert dictionary to Pose object.
        
        Args:
            pose_data: Dictionary containing pose data
            
        Returns:
            Pose object
        """
        joints = []
        
        for joint_data in pose_data.get('joints', []):
            keypoint = KeyPoint(
                x=joint_data['keypoint']['x'],
                y=joint_data['keypoint']['y'],
                confidence=joint_data['keypoint']['confidence']
            )
            
            joint = Joint(
                name=joint_data['name'],
                keypoint=keypoint,
                joint_id=joint_data.get('joint_id', 0)
            )
            joints.append(joint)
        
        pose = Pose(
            joints=joints,
            person_id=pose_data.get('person_id', 0),
            confidence=pose_data.get('confidence', 0.0)
        )
        
        # Add frame information if available
        if 'frame_number' in pose_data:
            pose.frame_number = pose_data['frame_number']
        if 'timestamp' in pose_data:
            pose.timestamp = pose_data['timestamp']
        
        return pose

    def _group_poses_by_frame(self, poses: List[Pose]) -> Dict[int, List[Pose]]:
        """
        Group poses by frame number for efficient lookup.
        
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

    def _extract_frames_with_overlays(
        self,
        input_path: Path,
        output_directory: Path,
        poses_by_frame: Dict[int, List[Pose]],
        frame_range: Optional[Tuple[int, int]] = None,
        progress_callback: Optional[callable] = None
    ) -> List[Path]:
        """
        Extract individual frames with pose overlays.
        
        Args:
            input_path: Input video path
            output_directory: Directory to save frame images
            poses_by_frame: Poses grouped by frame number
            frame_range: Optional frame range (start, end)
            progress_callback: Optional progress callback
            
        Returns:
            List of paths to saved frame images
        """
        # Open input video
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open input video: {input_path}")
        
        generated_files = []
        
        try:
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Apply resize factor if specified
            if self.config.resize_factor:
                width = int(width * self.config.resize_factor)
                height = int(height * self.config.resize_factor)
            
            # Determine frame range
            start_frame = 0 if frame_range is None else frame_range[0]
            end_frame = total_frames if frame_range is None else min(frame_range[1], total_frames)
            
            self.logger.info(f"Extracting frames {start_frame}-{end_frame} from video: {width}x{height}, {total_frames} total frames")
            
            frame_count = 0
            saved_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Check if we're in the desired frame range
                if frame_count < start_frame:
                    frame_count += 1
                    continue
                    
                if frame_count >= end_frame:
                    break
                
                # Skip frames if configured
                if frame_count % self.config.frame_skip != 0:
                    frame_count += 1
                    continue
                
                # Resize frame if configured
                if self.config.resize_factor:
                    frame = cv2.resize(frame, (width, height))
                
                # Get poses for this frame
                frame_poses = poses_by_frame.get(frame_count, [])
                
                # Draw poses on frame
                overlay_frame = self._draw_poses_on_frame(frame, frame_poses)
                
                # Generate filename
                filename = self.config.frame_filename_template.format(frame_count)
                output_path = output_directory / filename
                
                # Save frame image
                if self._save_frame_image(overlay_frame, output_path):
                    generated_files.append(output_path)
                    saved_count += 1
                
                # Update progress
                if progress_callback:
                    progress = (frame_count - start_frame + 1) / (end_frame - start_frame)
                    progress_callback(progress, frame_count + 1, end_frame - start_frame)
                
                frame_count += 1
            
            self.logger.info(f"Extracted {saved_count} frame overlays to {output_directory}")
            
        finally:
            cap.release()
        
        return generated_files

    def _save_frame_image(self, frame: np.ndarray, output_path: Path) -> bool:
        """
        Save a frame as an image file.
        
        Args:
            frame: Frame to save
            output_path: Path to save the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.config.image_format.lower() == 'jpg':
                # Set JPEG quality
                encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.config.image_quality]
                success = cv2.imwrite(str(output_path), frame, encode_params)
            elif self.config.image_format.lower() == 'png':
                # Set PNG compression
                encode_params = [cv2.IMWRITE_PNG_COMPRESSION, 3]
                success = cv2.imwrite(str(output_path), frame, encode_params)
            else:
                # Default save
                success = cv2.imwrite(str(output_path), frame)
            
            if not success:
                self.logger.error(f"Failed to save frame image: {output_path}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving frame image {output_path}: {e}")
            return False

    def _process_video(
        self,
        input_path: Path,
        output_path: Path,
        poses_by_frame: Dict[int, List[Pose]],
        progress_callback: Optional[callable] = None
    ) -> None:
        """
        Process video and generate overlay.
        
        Args:
            input_path: Input video path
            output_path: Output video path
            poses_by_frame: Poses grouped by frame number
            progress_callback: Optional progress callback
        """
        # Open input video
        cap = cv2.VideoCapture(str(input_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open input video: {input_path}")
        
        try:
            # Get video properties
            fps = self.config.output_fps or cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Apply resize factor if specified
            if self.config.resize_factor:
                width = int(width * self.config.resize_factor)
                height = int(height * self.config.resize_factor)
            
            self.logger.info(f"Processing video: {width}x{height} @ {fps}fps, {total_frames} frames")
            
            # Setup output video writer
            fourcc = cv2.VideoWriter_fourcc(*self.config.output_codec)
            out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
            
            if not out.isOpened():
                raise RuntimeError(f"Could not create output video: {output_path}")
            
            try:
                frame_count = 0
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Skip frames if configured
                    if frame_count % self.config.frame_skip != 0:
                        frame_count += 1
                        continue
                    
                    # Resize frame if configured
                    if self.config.resize_factor:
                        frame = cv2.resize(frame, (width, height))
                    
                    # Get poses for this frame
                    frame_poses = poses_by_frame.get(frame_count, [])
                    
                    # Draw poses on frame
                    overlay_frame = self._draw_poses_on_frame(frame, frame_poses)
                    
                    # Write frame to output video
                    out.write(overlay_frame)
                    
                    # Update progress
                    if progress_callback:
                        progress = (frame_count + 1) / total_frames
                        progress_callback(progress, frame_count + 1, total_frames)
                    
                    frame_count += 1
                
                self.logger.info(f"Generated overlay video with {frame_count} frames")
                
            finally:
                out.release()
                
        finally:
            cap.release()

    def _draw_poses_on_frame(self, frame: np.ndarray, poses: List[Pose]) -> np.ndarray:
        """
        Draw poses on a video frame.
        
        Args:
            frame: Input video frame
            poses: List of poses to draw
            
        Returns:
            Frame with poses drawn
        """
        # Create a copy to avoid modifying original
        overlay_frame = frame.copy()
        
        for pose in poses:
            # Filter joints by confidence threshold
            valid_joints = [
                joint for joint in pose.joints 
                if joint.keypoint.confidence >= self.config.confidence_threshold
            ]
            
            if not valid_joints:
                continue
            
            # Draw skeleton connections
            self._draw_skeleton(overlay_frame, valid_joints)
            
            # Draw joints
            self._draw_joints(overlay_frame, valid_joints)
            
            # Draw person info
            if self.config.show_person_id or self.config.show_confidence:
                self._draw_person_info(overlay_frame, pose, valid_joints)
        
        return overlay_frame

    def _draw_skeleton(self, frame: np.ndarray, joints: List[Joint]) -> None:
        """
        Draw skeleton connections between joints.
        
        Args:
            frame: Frame to draw on
            joints: List of joints to connect
        """
        # Define skeleton connections (joint name pairs)
        # This is a simplified skeleton - you can expand this
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
                
                start_point = (
                    int(start_joint.keypoint.x),
                    int(start_joint.keypoint.y)
                )
                end_point = (
                    int(end_joint.keypoint.x),
                    int(end_joint.keypoint.y)
                )
                
                cv2.line(
                    frame, 
                    start_point, 
                    end_point, 
                    self.config.skeleton_color,
                    self.config.line_thickness
                )

    def _draw_joints(self, frame: np.ndarray, joints: List[Joint]) -> None:
        """
        Draw joint points.
        
        Args:
            frame: Frame to draw on
            joints: List of joints to draw
        """
        for joint in joints:
            center = (
                int(joint.keypoint.x),
                int(joint.keypoint.y)
            )
            
            cv2.circle(
                frame,
                center,
                self.config.joint_radius,
                self.config.joint_color,
                -1  # Filled circle
            )

    def _draw_person_info(
        self, 
        frame: np.ndarray, 
        pose: Pose, 
        joints: List[Joint]
    ) -> None:
        """
        Draw person ID and confidence information.
        
        Args:
            frame: Frame to draw on
            pose: Pose object
            joints: List of valid joints
        """
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
        if self.config.show_person_id:
            text_parts.append(f"P{pose.person_id}")
        if self.config.show_confidence:
            text_parts.append(f"{pose.confidence:.2f}")
        
        if text_parts:
            text = " ".join(text_parts)
            cv2.putText(
                frame,
                text,
                (text_x, text_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                self.config.font_scale,
                self.config.font_color,
                1,
                cv2.LINE_AA
            )

    def get_video_info(self, video_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get information about a video file.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video information
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            RuntimeError: If video cannot be opened
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Could not open video: {video_path}")
        
        try:
            return {
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
                'codec': int(cap.get(cv2.CAP_PROP_FOURCC))
            }
        finally:
            cap.release()

    def __str__(self) -> str:
        """String representation."""
        return f"VideoOverlayGenerator(codec={self.config.output_codec})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"VideoOverlayGenerator(config={self.config})" 