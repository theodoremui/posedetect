#!/usr/bin/env python3
"""
MediaPipe-based Pose Detector

A CPU-friendly alternative to OpenPose using Google's MediaPipe library.
This detector provides similar functionality without CUDA dependencies.
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False

from loguru import logger
from ..models.pose import Pose, Joint, KeyPoint
from ..utils.video_processor import VideoProcessor


# MediaPipe pose landmark indices and names
MEDIAPIPE_POSE_LANDMARKS = {
    0: "nose",
    1: "left_eye_inner", 2: "left_eye", 3: "left_eye_outer",
    4: "right_eye_inner", 5: "right_eye", 6: "right_eye_outer",
    7: "left_ear", 8: "right_ear",
    9: "mouth_left", 10: "mouth_right",
    11: "left_shoulder", 12: "right_shoulder",
    13: "left_elbow", 14: "right_elbow",
    15: "left_wrist", 16: "right_wrist",
    17: "left_pinky", 18: "right_pinky",
    19: "left_index", 20: "right_index",
    21: "left_thumb", 22: "right_thumb",
    23: "left_hip", 24: "right_hip",
    25: "left_knee", 26: "right_knee",
    27: "left_ankle", 28: "right_ankle",
    29: "left_heel", 30: "right_heel",
    31: "left_foot_index", 32: "right_foot_index"
}


class MediaPipePoseDetector:
    """
    MediaPipe-based pose detector that provides CPU-friendly pose detection
    without requiring CUDA or OpenPose dependencies.
    """
    
    def __init__(self, 
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5,
                 model_complexity: int = 1):
        """
        Initialize MediaPipe pose detector.
        
        Args:
            min_detection_confidence: Minimum confidence for pose detection
            min_tracking_confidence: Minimum confidence for pose tracking
            model_complexity: Model complexity (0=Lite, 1=Full, 2=Heavy)
        """
        if not MEDIAPIPE_AVAILABLE:
            raise ImportError(
                "MediaPipe is not installed. Install with: pip install mediapipe"
            )
        
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.model_complexity = model_complexity
        
        # Initialize MediaPipe
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        self.pose_detector = None
        self._is_initialized = False
        
        logger.info("MediaPipe pose detector created")
    
    def initialize(self) -> None:
        """Initialize the MediaPipe pose detection model."""
        if self._is_initialized:
            logger.warning("MediaPipe detector already initialized")
            return
        
        try:
            self.pose_detector = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=self.model_complexity,
                enable_segmentation=False,
                min_detection_confidence=self.min_detection_confidence,
                min_tracking_confidence=self.min_tracking_confidence
            )
            
            self._is_initialized = True
            logger.info("MediaPipe pose detector initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize MediaPipe: {e}")
            raise RuntimeError(f"MediaPipe initialization failed: {e}")
    
    def _ensure_initialized(self) -> None:
        """Ensure the detector is initialized."""
        if not self._is_initialized:
            self.initialize()
    
    def detect_poses_in_image(self, image: np.ndarray) -> List[Pose]:
        """
        Detect poses in a single image using MediaPipe.
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            List of detected Pose objects
        """
        self._ensure_initialized()
        
        if self.pose_detector is None:
            raise RuntimeError("MediaPipe detector not properly initialized")
        
        try:
            # Convert BGR to RGB (MediaPipe expects RGB)
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process image
            results = self.pose_detector.process(rgb_image)
            
            poses = []
            if results.pose_landmarks:
                pose = self._convert_mediapipe_output(results.pose_landmarks)
                if pose:
                    poses.append(pose)
            
            logger.debug(f"Detected {len(poses)} poses in image using MediaPipe")
            return poses
            
        except Exception as e:
            logger.error(f"Error detecting poses with MediaPipe: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            return []
    
    def detect_poses_in_video(self, video_path: Path) -> List[Pose]:
        """
        Detect poses in all frames of a video using MediaPipe.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            List of detected Pose objects from all frames
        """
        self._ensure_initialized()
        
        if self.pose_detector is None:
            raise RuntimeError("MediaPipe detector not properly initialized for video processing")
        
        all_poses = []
        frames_processed = 0
        frames_with_errors = 0
        
        try:
            with VideoProcessor(video_path) as video_proc:
                metadata = video_proc.get_metadata()
                logger.info(f"Processing video with MediaPipe: {metadata['frame_count']} frames at {metadata['fps']} FPS")
                
                for frame_number, timestamp, frame in video_proc.iterate_frames():
                    try:
                        frame_poses = self.detect_poses_in_image(frame)
                        
                        # Add frame information to poses
                        for pose in frame_poses:
                            pose.frame_number = frame_number
                            pose.timestamp = timestamp
                        
                        all_poses.extend(frame_poses)
                        frames_processed += 1
                        
                        if frame_number % 30 == 0:  # Log every 30 frames
                            logger.info(f"Processed frame {frame_number}/{metadata['frame_count']} - Poses: {len(frame_poses)}")
                    
                    except Exception as e:
                        logger.warning(f"Error processing frame {frame_number}: {e}")
                        frames_with_errors += 1
                
                logger.info(f"MediaPipe video processing complete:")
                logger.info(f"  - Frames processed: {frames_processed}")
                logger.info(f"  - Frames with errors: {frames_with_errors}")
                logger.info(f"  - Total poses detected: {len(all_poses)}")
                
                if frames_processed == 0:
                    raise RuntimeError(f"No frames were successfully processed from video {video_path}")
                
        except Exception as e:
            logger.error(f"Error processing video with MediaPipe: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise RuntimeError(f"MediaPipe video processing failed: {e}")
        
        return all_poses
    
    def get_pose_with_overlay(self, image: np.ndarray) -> Tuple[List[Pose], np.ndarray]:
        """
        Detect poses and return both poses and image with overlay.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Tuple of (poses, image_with_overlay)
        """
        self._ensure_initialized()
        
        try:
            # Convert BGR to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Process image
            results = self.pose_detector.process(rgb_image)
            
            # Extract poses
            poses = []
            if results.pose_landmarks:
                pose = self._convert_mediapipe_output(results.pose_landmarks)
                if pose:
                    poses.append(pose)
            
            # Draw overlay
            annotated_image = image.copy()
            if results.pose_landmarks:
                self.mp_drawing.draw_landmarks(
                    annotated_image,
                    results.pose_landmarks,
                    self.mp_pose.POSE_CONNECTIONS,
                    landmark_drawing_spec=self.mp_drawing_styles.get_default_pose_landmarks_style()
                )
            
            return poses, annotated_image
            
        except Exception as e:
            logger.error(f"Error detecting poses with overlay using MediaPipe: {e}")
            return [], image
    
    def _convert_mediapipe_output(self, pose_landmarks) -> Optional[Pose]:
        """
        Convert MediaPipe landmarks to Pose object.
        
        Args:
            pose_landmarks: MediaPipe pose landmarks
            
        Returns:
            Pose object or None if no valid landmarks
        """
        joints = []
        total_confidence = 0.0
        valid_joints = 0
        
        for idx, landmark in enumerate(pose_landmarks.landmark):
            # MediaPipe provides normalized coordinates and visibility score
            joint_name = MEDIAPIPE_POSE_LANDMARKS.get(idx, f"landmark_{idx}")
            
            # Use visibility as confidence (MediaPipe doesn't provide explicit confidence)
            confidence = landmark.visibility
            
            # Only include landmarks with reasonable visibility
            if confidence > 0.1:  # Threshold for visibility
                # Convert normalized coordinates to pixel coordinates
                # Note: MediaPipe landmarks are normalized [0,1]
                # We'll need image dimensions to convert properly, but for now store normalized
                keypoint = KeyPoint(
                    x=float(landmark.x),  # Normalized x
                    y=float(landmark.y),  # Normalized y  
                    confidence=float(confidence)
                )
                
                joint = Joint(
                    name=joint_name,
                    keypoint=keypoint,
                    joint_id=idx
                )
                joints.append(joint)
                
                total_confidence += confidence
                valid_joints += 1
        
        # Only create pose if we have sufficient valid joints
        if valid_joints >= 5:  # Require at least 5 visible landmarks
            avg_confidence = total_confidence / valid_joints
            pose = Pose(
                joints=joints,
                person_id=0,  # MediaPipe detects one person per image
                confidence=avg_confidence
            )
            return pose
        
        return None
    
    def cleanup(self) -> None:
        """Clean up MediaPipe resources."""
        if hasattr(self, 'pose_detector') and self.pose_detector:
            try:
                self.pose_detector.close()
                logger.info("MediaPipe detector closed")
            except Exception as e:
                logger.warning(f"Error closing MediaPipe detector: {e}")
        
        self._is_initialized = False
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup() 