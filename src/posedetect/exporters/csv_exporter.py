"""
CSV Exporter for Pose Detection Data

This module provides functionality to export pose detection results to CSV format
with different layout options for various analysis needs.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from enum import Enum

from ..models.pose import Pose

logger = logging.getLogger(__name__)


class CSVFormat(Enum):
    """Supported CSV output formats."""
    TORONTO_GAIT = "toronto_gait"  # Toronto Older Adults Gait Archive format


# Mapping from COCO joint names to Toronto Gait Archive naming convention
TORONTO_GAIT_JOINT_MAPPING = {
    "nose": "Nose",
    "left_eye": "LEye", 
    "right_eye": "REye",
    "left_ear": "LEar",
    "right_ear": "REar",
    "left_shoulder": "LShoulder",
    "right_shoulder": "RShoulder",
    "left_elbow": "LElbow",
    "right_elbow": "RElbow",
    "left_wrist": "LWrist",
    "right_wrist": "RWrist",
    "left_hip": "LHip",
    "right_hip": "RHip",
    "left_knee": "LKnee",
    "right_knee": "RKnee",
    "left_ankle": "LAnkle",
    "right_ankle": "RAnkle"
}

# Expected order for Toronto Gait Archive format (COCO order)
TORONTO_GAIT_JOINT_ORDER = [
    "Nose", "LEye", "REye", "LEar", "REar",
    "LShoulder", "RShoulder", "LElbow", "RElbow", 
    "LWrist", "RWrist", "LHip", "RHip",
    "LKnee", "RKnee", "LAnkle", "RAnkle"
]


class CSVExporter:
    """
    Export pose detection data to CSV format.
    
    Exports data in Toronto Older Adults Gait Archive format:
    - One row per frame with all joints as columns in COCO order
    - Missing joints are filled with 0,0,0
    - Includes ALL frames from video, even those without poses
    """
    
    def __init__(self, format_type: CSVFormat = CSVFormat.TORONTO_GAIT):
        """
        Initialize CSV exporter.
        
        Args:
            format_type: The CSV format to use for export
        """
        self.format_type = format_type
        self.logger = logger

    def export_poses(
        self, 
        poses: List[Pose], 
        output_path: Union[str, Path],
        include_metadata: bool = True,
        video_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Export poses to CSV file.
        
        Args:
            poses: List of pose objects to export
            output_path: Path where CSV file will be saved
            include_metadata: Whether to include metadata in the CSV
            video_metadata: Optional video metadata (total_frames, fps) for Toronto Gait format
            
        Raises:
            ValueError: If poses list is empty or invalid
            IOError: If file cannot be written
        """
        if not poses:
            raise ValueError("Cannot export empty poses list")
        
        output_path = Path(output_path)
        
        try:
            if self.format_type == CSVFormat.TORONTO_GAIT:
                self._export_toronto_gait(poses, output_path, include_metadata, video_metadata)
            else:
                raise ValueError(f"Unsupported CSV format: {self.format_type}")
                
            self.logger.info(f"Exported {len(poses)} poses to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export CSV to {output_path}: {e}")
            raise

    def _export_toronto_gait(
        self, 
        poses: List[Pose], 
        output_path: Path,
        include_metadata: bool,
        video_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Export in Toronto Older Adults Gait Archive format.
        
        Format: time,Nose_x,Nose_y,Nose_conf,LEye_x,LEye_y,LEye_conf,...
        One row per frame with all joints as columns in COCO order.
        Missing joints are filled with 0,0,0.
        
        For Toronto Gait format, ALL frames from the video are included,
        even those where no pose was detected.
        """
        # Build header row
        fieldnames = ["time"]
        for joint_name in TORONTO_GAIT_JOINT_ORDER:
            fieldnames.extend([
                f"{joint_name}_x",
                f"{joint_name}_y", 
                f"{joint_name}_conf"
            ])
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
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
            
            # Generate rows for ALL frames (0 to total_frames-1)
            for frame_number in range(total_frames):
                timestamp = frame_number / fps
                
                if frame_number in poses_by_frame:
                    # Frame has detected poses - use the first one (primary person)
                    # For multi-person scenarios, we could create multiple rows or average
                    pose = poses_by_frame[frame_number][0]  # Use first detected person
                    
                    row = {"time": timestamp}
                    
                    # Initialize all joints with 0,0,0
                    for joint_name in TORONTO_GAIT_JOINT_ORDER:
                        row[f"{joint_name}_x"] = 0
                        row[f"{joint_name}_y"] = 0
                        row[f"{joint_name}_conf"] = 0
                    
                    # Fill in available joint data
                    for joint in pose.joints:
                        toronto_name = TORONTO_GAIT_JOINT_MAPPING.get(joint.name)
                        if toronto_name:
                            row[f"{toronto_name}_x"] = joint.keypoint.x
                            row[f"{toronto_name}_y"] = joint.keypoint.y
                            row[f"{toronto_name}_conf"] = joint.keypoint.confidence
                else:
                    # Frame has no detected poses - fill with all zeros
                    row = {"time": timestamp}
                    
                    for joint_name in TORONTO_GAIT_JOINT_ORDER:
                        row[f"{joint_name}_x"] = 0
                        row[f"{joint_name}_y"] = 0
                        row[f"{joint_name}_conf"] = 0
                
                writer.writerow(row)

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

    def _calculate_bounding_box(self, pose: Pose) -> Optional[Dict[str, float]]:
        """
        Calculate bounding box for a pose based on joint positions.
        
        Args:
            pose: Pose object to calculate bounding box for
            
        Returns:
            Dictionary with left, top, right, bottom coordinates or None
        """
        valid_points = [
            (joint.keypoint.x, joint.keypoint.y) 
            for joint in pose.joints 
            if joint.keypoint.confidence > 0
        ]
        
        if not valid_points:
            return None
        
        xs, ys = zip(*valid_points)
        return {
            'left': min(xs),
            'top': min(ys),
            'right': max(xs),
            'bottom': max(ys)
        }

    @staticmethod
    def get_available_formats() -> List[str]:
        """Get list of available CSV format names."""
        return [fmt.value for fmt in CSVFormat]

    def __str__(self) -> str:
        """String representation of the exporter."""
        return f"CSVExporter(format={self.format_type.value})"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"CSVExporter(format_type={self.format_type})" 