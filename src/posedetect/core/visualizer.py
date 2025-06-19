"""
Pose visualization utilities.

This module provides utilities for visualizing pose detection results by
overlaying keypoints and connections on images and video frames.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from loguru import logger

from ..models.pose import Pose, POSE_CONNECTIONS


class PoseVisualizer:
    """
    Handles visualization of pose detection results.
    
    This class provides methods for drawing poses on images and videos
    following the Single Responsibility Principle.
    """
    
    def __init__(self, 
                 keypoint_color: Tuple[int, int, int] = (0, 255, 0),
                 connection_color: Tuple[int, int, int] = (0, 0, 255),
                 keypoint_radius: int = 4,
                 connection_thickness: int = 2,
                 confidence_threshold: float = 0.1):
        """
        Initialize the pose visualizer.
        
        Args:
            keypoint_color: RGB color for keypoints
            connection_color: RGB color for connections
            keypoint_radius: Radius of keypoint circles
            connection_thickness: Thickness of connection lines
            confidence_threshold: Minimum confidence to draw keypoints
        """
        self.keypoint_color = keypoint_color
        self.connection_color = connection_color
        self.keypoint_radius = keypoint_radius
        self.connection_thickness = connection_thickness
        self.confidence_threshold = confidence_threshold
        
        # Colors for different people (when multiple people detected)
        self.person_colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
            (128, 0, 128),  # Purple
            (255, 165, 0),  # Orange
        ]
    
    def draw_pose_on_image(self, 
                          image: np.ndarray, 
                          poses: List[Pose],
                          show_confidence: bool = False) -> np.ndarray:
        """
        Draw poses on an image.
        
        Args:
            image: Input image as numpy array (BGR format)
            poses: List of Pose objects to draw
            show_confidence: Whether to show confidence scores
            
        Returns:
            Image with poses drawn on it
        """
        # Create a copy to avoid modifying the original
        result_image = image.copy()
        
        for pose in poses:
            person_color = self._get_person_color(pose.person_id)
            self._draw_single_pose(result_image, pose, person_color, show_confidence)
        
        return result_image
    
    def _draw_single_pose(self, 
                         image: np.ndarray, 
                         pose: Pose,
                         color: Tuple[int, int, int],
                         show_confidence: bool = False) -> None:
        """
        Draw a single pose on an image.
        
        Args:
            image: Image to draw on (modified in place)
            pose: Pose object to draw
            color: Color to use for this pose
            show_confidence: Whether to show confidence scores
        """
        # Create a mapping of joint_id to keypoint for easy lookup
        joint_map = {joint.joint_id: joint.keypoint for joint in pose.joints}
        
        # Draw connections first (so they appear behind keypoints)
        self._draw_connections(image, joint_map, color)
        
        # Draw keypoints
        for joint in pose.joints:
            if joint.keypoint.confidence >= self.confidence_threshold:
                self._draw_keypoint(
                    image, 
                    joint.keypoint, 
                    color, 
                    joint.name if show_confidence else None,
                    joint.keypoint.confidence if show_confidence else None
                )
    
    def _draw_connections(self, 
                         image: np.ndarray, 
                         joint_map: dict,
                         color: Tuple[int, int, int]) -> None:
        """
        Draw connections between joints.
        
        Args:
            image: Image to draw on
            joint_map: Mapping of joint_id to KeyPoint
            color: Color for connections
        """
        for joint1_id, joint2_id in POSE_CONNECTIONS:
            if joint1_id in joint_map and joint2_id in joint_map:
                kp1 = joint_map[joint1_id]
                kp2 = joint_map[joint2_id]
                
                # Only draw if both keypoints have sufficient confidence
                if (kp1.confidence >= self.confidence_threshold and 
                    kp2.confidence >= self.confidence_threshold):
                    
                    pt1 = (int(kp1.x), int(kp1.y))
                    pt2 = (int(kp2.x), int(kp2.y))
                    
                    cv2.line(image, pt1, pt2, color, self.connection_thickness)
    
    def _draw_keypoint(self, 
                      image: np.ndarray, 
                      keypoint,
                      color: Tuple[int, int, int],
                      joint_name: Optional[str] = None,
                      confidence: Optional[float] = None) -> None:
        """
        Draw a single keypoint on an image.
        
        Args:
            image: Image to draw on
            keypoint: KeyPoint object
            color: Color for the keypoint
            joint_name: Optional joint name to display
            confidence: Optional confidence score to display
        """
        center = (int(keypoint.x), int(keypoint.y))
        
        # Draw keypoint circle
        cv2.circle(image, center, self.keypoint_radius, color, -1)
        cv2.circle(image, center, self.keypoint_radius + 1, (255, 255, 255), 1)
        
        # Draw joint name/confidence if requested
        if joint_name or confidence is not None:
            text_parts = []
            if joint_name:
                text_parts.append(joint_name)
            if confidence is not None:
                text_parts.append(f"{confidence:.2f}")
            
            text = " ".join(text_parts)
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.3
            thickness = 1
            
            # Get text size for background
            (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)
            
            # Draw background rectangle
            bg_pt1 = (center[0] - text_width // 2, center[1] - text_height - 5)
            bg_pt2 = (center[0] + text_width // 2, center[1] - 5)
            cv2.rectangle(image, bg_pt1, bg_pt2, (0, 0, 0), -1)
            
            # Draw text
            text_org = (center[0] - text_width // 2, center[1] - 8)
            cv2.putText(image, text, text_org, font, font_scale, (255, 255, 255), thickness)
    
    def _get_person_color(self, person_id: int) -> Tuple[int, int, int]:
        """
        Get color for a specific person ID.
        
        Args:
            person_id: ID of the person
            
        Returns:
            RGB color tuple
        """
        return self.person_colors[person_id % len(self.person_colors)]
    
    def create_pose_overlay_video(self, 
                                 input_video_path: str,
                                 output_video_path: str,
                                 poses: List[Pose],
                                 show_confidence: bool = False) -> None:
        """
        Create a video with pose overlays.
        
        Args:
            input_video_path: Path to input video
            output_video_path: Path to output video
            poses: List of all poses detected in the video
            show_confidence: Whether to show confidence scores
        """
        # Group poses by frame number
        poses_by_frame = {}
        for pose in poses:
            if pose.frame_number is not None:
                if pose.frame_number not in poses_by_frame:
                    poses_by_frame[pose.frame_number] = []
                poses_by_frame[pose.frame_number].append(pose)
        
        # Open input video
        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open input video: {input_video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Setup output video writer
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        
        logger.info(f"Creating overlay video: {total_frames} frames at {fps} FPS")
        
        try:
            frame_number = 0
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Add pose overlay if poses exist for this frame
                if frame_number in poses_by_frame:
                    frame = self.draw_pose_on_image(
                        frame, 
                        poses_by_frame[frame_number],
                        show_confidence
                    )
                
                out.write(frame)
                frame_number += 1
                
                if frame_number % 30 == 0:
                    logger.info(f"Processed overlay frame {frame_number}/{total_frames}")
        
        finally:
            cap.release()
            out.release()
        
        logger.info(f"Overlay video saved: {output_video_path}")
    
    def save_pose_image(self, 
                       image: np.ndarray,
                       poses: List[Pose],
                       output_path: str,
                       show_confidence: bool = False) -> None:
        """
        Save an image with pose overlay.
        
        Args:
            image: Input image
            poses: List of poses to overlay
            output_path: Path to save the output image
            show_confidence: Whether to show confidence scores
        """
        result_image = self.draw_pose_on_image(image, poses, show_confidence)
        success = cv2.imwrite(output_path, result_image)
        
        if success:
            logger.info(f"Pose image saved: {output_path}")
        else:
            logger.error(f"Failed to save pose image: {output_path}")
            raise RuntimeError(f"Failed to save image: {output_path}") 