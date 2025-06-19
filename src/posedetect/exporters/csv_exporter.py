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
    NORMALIZED = "normalized"  # One row per joint detection
    WIDE = "wide"             # One row per frame, joints as columns
    SUMMARY = "summary"       # One row per person per frame


class CSVExporter:
    """
    Export pose detection data to CSV format.
    
    Supports multiple CSV layouts:
    - Normalized: One row per joint detection (best for analysis)
    - Wide: One row per frame with all joints as columns (compact)
    - Summary: One row per person per frame with aggregate stats
    """
    
    def __init__(self, format_type: CSVFormat = CSVFormat.NORMALIZED):
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
        include_metadata: bool = True
    ) -> None:
        """
        Export poses to CSV file.
        
        Args:
            poses: List of pose objects to export
            output_path: Path where CSV file will be saved
            include_metadata: Whether to include metadata in the CSV
            
        Raises:
            ValueError: If poses list is empty or invalid
            IOError: If file cannot be written
        """
        if not poses:
            raise ValueError("Cannot export empty poses list")
        
        output_path = Path(output_path)
        
        try:
            if self.format_type == CSVFormat.NORMALIZED:
                self._export_normalized(poses, output_path, include_metadata)
            elif self.format_type == CSVFormat.WIDE:
                self._export_wide(poses, output_path, include_metadata)
            elif self.format_type == CSVFormat.SUMMARY:
                self._export_summary(poses, output_path, include_metadata)
            else:
                raise ValueError(f"Unsupported CSV format: {self.format_type}")
                
            self.logger.info(f"Exported {len(poses)} poses to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export CSV to {output_path}: {e}")
            raise

    def _export_normalized(
        self, 
        poses: List[Pose], 
        output_path: Path,
        include_metadata: bool
    ) -> None:
        """
        Export in normalized format: one row per joint detection.
        
        Columns: frame_number, timestamp, person_id, joint_name, joint_id, 
                x, y, confidence, pose_confidence
        """
        fieldnames = [
            'frame_number', 'timestamp', 'person_id', 'joint_name', 
            'joint_id', 'x', 'y', 'confidence'
        ]
        
        if include_metadata:
            fieldnames.extend(['pose_confidence', 'total_joints'])
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for pose in poses:
                base_row = {
                    'frame_number': getattr(pose, 'frame_number', ''),
                    'timestamp': getattr(pose, 'timestamp', ''),
                    'person_id': pose.person_id,
                }
                
                if include_metadata:
                    base_row.update({
                        'pose_confidence': pose.confidence,
                        'total_joints': len(pose.joints)
                    })
                
                for joint in pose.joints:
                    row = base_row.copy()
                    row.update({
                        'joint_name': joint.name,
                        'joint_id': joint.joint_id,
                        'x': joint.keypoint.x,
                        'y': joint.keypoint.y,
                        'confidence': joint.keypoint.confidence
                    })
                    writer.writerow(row)

    def _export_wide(
        self, 
        poses: List[Pose], 
        output_path: Path,
        include_metadata: bool
    ) -> None:
        """
        Export in wide format: one row per frame, joints as columns.
        
        Dynamically creates columns based on available joints.
        """
        # Collect all unique joint names across all poses
        all_joint_names = set()
        for pose in poses:
            for joint in pose.joints:
                all_joint_names.add(joint.name)
        
        sorted_joint_names = sorted(all_joint_names)
        
        # Build fieldnames
        fieldnames = ['frame_number', 'timestamp', 'person_id']
        
        if include_metadata:
            fieldnames.extend(['pose_confidence', 'total_joints'])
        
        # Add columns for each joint (x, y, confidence)
        for joint_name in sorted_joint_names:
            fieldnames.extend([
                f'{joint_name}_x',
                f'{joint_name}_y', 
                f'{joint_name}_confidence'
            ])
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for pose in poses:
                row = {
                    'frame_number': getattr(pose, 'frame_number', ''),
                    'timestamp': getattr(pose, 'timestamp', ''),
                    'person_id': pose.person_id,
                }
                
                if include_metadata:
                    row.update({
                        'pose_confidence': pose.confidence,
                        'total_joints': len(pose.joints)
                    })
                
                # Initialize all joint columns with empty values
                for joint_name in sorted_joint_names:
                    row[f'{joint_name}_x'] = ''
                    row[f'{joint_name}_y'] = ''
                    row[f'{joint_name}_confidence'] = ''
                
                # Fill in available joint data
                for joint in pose.joints:
                    joint_name = joint.name
                    row[f'{joint_name}_x'] = joint.keypoint.x
                    row[f'{joint_name}_y'] = joint.keypoint.y
                    row[f'{joint_name}_confidence'] = joint.keypoint.confidence
                
                writer.writerow(row)

    def _export_summary(
        self, 
        poses: List[Pose], 
        output_path: Path,
        include_metadata: bool
    ) -> None:
        """
        Export in summary format: one row per person per frame with stats.
        
        Includes aggregate statistics like average confidence, joint counts, etc.
        """
        fieldnames = [
            'frame_number', 'timestamp', 'person_id', 'total_joints',
            'valid_joints', 'avg_confidence', 'max_confidence', 'min_confidence',
            'pose_confidence'
        ]
        
        if include_metadata:
            # Add bounding box info if available
            fieldnames.extend(['bbox_left', 'bbox_top', 'bbox_right', 'bbox_bottom'])
        
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for pose in poses:
                # Calculate statistics
                confidences = [joint.keypoint.confidence for joint in pose.joints]
                valid_joints = len([c for c in confidences if c > 0])
                
                # Calculate bounding box
                bbox = self._calculate_bounding_box(pose)
                
                row = {
                    'frame_number': getattr(pose, 'frame_number', ''),
                    'timestamp': getattr(pose, 'timestamp', ''),
                    'person_id': pose.person_id,
                    'total_joints': len(pose.joints),
                    'valid_joints': valid_joints,
                    'avg_confidence': sum(confidences) / len(confidences) if confidences else 0,
                    'max_confidence': max(confidences) if confidences else 0,
                    'min_confidence': min(confidences) if confidences else 0,
                    'pose_confidence': pose.confidence
                }
                
                if include_metadata and bbox:
                    row.update({
                        'bbox_left': bbox['left'],
                        'bbox_top': bbox['top'], 
                        'bbox_right': bbox['right'],
                        'bbox_bottom': bbox['bottom']
                    })
                
                writer.writerow(row)

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