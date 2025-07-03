"""
JSON Exporter for Pose Detection Data

This module provides functionality to export pose detection results to JSON format
with different structural options for various analysis needs.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime

from ..models.pose import Pose
from .csv_exporter import TORONTO_GAIT_JOINT_MAPPING, TORONTO_GAIT_JOINT_ORDER

logger = logging.getLogger(__name__)


class JSONFormat(Enum):
    """Supported JSON output formats."""
    TORONTO_GAIT = "toronto_gait"  # Toronto Older Adults Gait Archive format


class JSONExporter:
    """
    Export pose detection data to JSON format.
    
    Exports data in Toronto Older Adults Gait Archive format:
    - Includes ALL frames from video, even those without poses
    - Missing frames get person_id: -1 and all joints set to 0,0,0
    - Maintains temporal continuity for research analysis
    """
    
    def __init__(self, format_type: JSONFormat = JSONFormat.TORONTO_GAIT):
        """
        Initialize JSON exporter.
        
        Args:
            format_type: The JSON format to use for export
        """
        self.format_type = format_type
        self.logger = logger

    def export_poses(
        self, 
        poses: List[Pose], 
        output_path: Union[str, Path],
        metadata: Optional[Dict[str, Any]] = None,
        pretty_print: bool = True,
        video_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Export poses to JSON file.
        
        Args:
            poses: List of pose objects to export
            output_path: Path where JSON file will be saved
            metadata: Optional metadata to include in the JSON
            pretty_print: Whether to format JSON with indentation
            video_metadata: Optional video metadata (total_frames, fps) for Toronto Gait format
            
        Raises:
            ValueError: If poses list is empty or invalid
            IOError: If file cannot be written
        """
        if not poses:
            raise ValueError("Cannot export empty poses list")
        
        output_path = Path(output_path)
        
        try:
            if self.format_type == JSONFormat.TORONTO_GAIT:
                data = self._export_toronto_gait(poses, metadata, video_metadata)
            else:
                raise ValueError(f"Unsupported JSON format: {self.format_type}")
            
            # Write JSON file
            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty_print:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
                
            self.logger.info(f"Exported {len(poses)} poses to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export JSON to {output_path}: {e}")
            raise

    def _export_toronto_gait(
        self, 
        poses: List[Pose], 
        metadata: Optional[Dict[str, Any]],
        video_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Export in Toronto Older Adults Gait Archive JSON format.
        
        For Toronto Gait format, ALL frames from the video are included,
        even those where no pose was detected.
        
        Args:
            poses: List of poses to export
            metadata: Optional metadata
            video_metadata: Optional video metadata (total_frames, fps)
            
        Returns:
            Dictionary with Toronto Gait JSON structure
        """
        # Group poses by frame for lookup
        poses_by_frame = self._group_poses_by_frame(poses)
        
        # Determine total frames and fps from video metadata or poses
        total_frames = 0
        fps = 30.0  # Default fps
        
        if video_metadata:
            total_frames = video_metadata.get('total_frames', 0)
            fps = video_metadata.get('fps', 30.0)
        
        # If no video metadata, use the maximum frame number from poses
        if total_frames == 0 and poses:
            max_frame = max(getattr(pose, 'frame_number', 0) for pose in poses)
            total_frames = max_frame + 1
        
        # Convert to Toronto Gait format - include ALL frames
        frames = []
        for frame_number in range(total_frames):
            timestamp = frame_number / fps
            
            if frame_number in poses_by_frame:
                # Frame has detected poses - use the first one (primary person)
                frame_poses = poses_by_frame[frame_number]
                pose = frame_poses[0]  # Use first detected person
                
                frame_data = {
                    "frame_number": frame_number,
                    "timestamp": timestamp,
                    "person_id": pose.person_id,
                    "keypoints": {}
                }
                
                # Initialize all joints with default values
                for joint_name in TORONTO_GAIT_JOINT_ORDER:
                    frame_data["keypoints"][joint_name] = {
                        "x": 0.0,
                        "y": 0.0,
                        "confidence": 0.0
                    }
                
                # Fill in available joint data
                for joint in pose.joints:
                    toronto_name = TORONTO_GAIT_JOINT_MAPPING.get(joint.name)
                    if toronto_name:
                        frame_data["keypoints"][toronto_name] = {
                            "x": joint.keypoint.x,
                            "y": joint.keypoint.y,
                            "confidence": joint.keypoint.confidence
                        }
            else:
                # Frame has no detected poses - fill with zeros
                frame_data = {
                    "frame_number": frame_number,
                    "timestamp": timestamp,
                    "person_id": -1,  # Indicate no person detected
                    "keypoints": {}
                }
                
                # Initialize all joints with zero values
                for joint_name in TORONTO_GAIT_JOINT_ORDER:
                    frame_data["keypoints"][joint_name] = {
                        "x": 0.0,
                        "y": 0.0,
                        "confidence": 0.0
                    }
            
            frames.append(frame_data)
        
        return {
            "metadata": {
                "format": "toronto_gait",
                "export_time": datetime.now().isoformat(),
                "total_frames": len(frames),
                "joint_format": "COCO_17",
                "joint_order": TORONTO_GAIT_JOINT_ORDER,
                "reference": "Toronto Older Adults Gait Archive (Nature Scientific Data, 2022)",
                "doi": "10.1038/s41597-022-01495-z",
                **(metadata or {}),
                **(video_metadata or {})
            },
            "frames": frames
        }

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
        return poses_by_frame

    @staticmethod
    def get_available_formats() -> List[str]:
        """Get list of available JSON format names."""
        return [fmt.value for fmt in JSONFormat]

    def __str__(self) -> str:
        """String representation of the exporter."""
        return f"JSONExporter(format={self.format_type.value})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"JSONExporter(format_type={self.format_type})" 