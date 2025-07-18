"""
Tests for pose detection exporters.

This module contains comprehensive tests for the various export formats
including CSV export functionality.
"""

import pytest
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from src.posedetect.models.pose import Pose, Joint, KeyPoint
from src.posedetect.exporters.csv_exporter import CSVExporter, CSVFormat


class TestCSVExporter:
    """Test cases for CSV export functionality."""
    
    @pytest.fixture
    def sample_poses(self) -> List[Pose]:
        """Create sample pose data for testing."""
        poses = []
        
        # Create pose 1
        joints1 = [
            Joint(name="nose", keypoint=KeyPoint(x=100.0, y=50.0, confidence=0.9), joint_id=0),
            Joint(name="left_eye", keypoint=KeyPoint(x=95.0, y=45.0, confidence=0.8), joint_id=1),
            Joint(name="right_eye", keypoint=KeyPoint(x=105.0, y=45.0, confidence=0.85), joint_id=2),
        ]
        pose1 = Pose(joints=joints1, person_id=0, confidence=0.85)
        pose1.frame_number = 0
        pose1.timestamp = 0.0
        poses.append(pose1)
        
        # Create pose 2
        joints2 = [
            Joint(name="nose", keypoint=KeyPoint(x=200.0, y=60.0, confidence=0.75), joint_id=0),
            Joint(name="left_shoulder", keypoint=KeyPoint(x=180.0, y=80.0, confidence=0.7), joint_id=5),
            Joint(name="right_shoulder", keypoint=KeyPoint(x=220.0, y=80.0, confidence=0.72), joint_id=6),
        ]
        pose2 = Pose(joints=joints2, person_id=1, confidence=0.72)
        pose2.frame_number = 1
        pose2.timestamp = 0.033
        poses.append(pose2)
        
        return poses
    
    def test_csv_exporter_initialization(self):
        """Test CSV exporter initialization."""
        # Test default initialization
        exporter = CSVExporter()
        assert exporter.format_type == CSVFormat.TORONTO_GAIT
        
        # Test with specific format
        exporter = CSVExporter(CSVFormat.TORONTO_GAIT)
        assert exporter.format_type == CSVFormat.TORONTO_GAIT
    
    def test_toronto_gait_format_export(self, sample_poses):
        """Test Toronto Gait CSV format export."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_toronto_gait.csv"
            
            exporter = CSVExporter(CSVFormat.TORONTO_GAIT)
            exporter.export_poses(sample_poses, output_path)
            
            assert output_path.exists()
            
            # Read and verify CSV content
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Toronto Gait format has one row per frame with all joints as columns
            assert len(rows) >= 1
            
            # Check column structure includes time and joint coordinates
            fieldnames = reader.fieldnames
            assert 'time' in fieldnames
            assert 'Nose_x' in fieldnames
            assert 'Nose_y' in fieldnames
            assert 'Nose_conf' in fieldnames
    
    def test_export_without_metadata(self, sample_poses):
        """Test CSV export without metadata."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_no_metadata.csv"
            
            exporter = CSVExporter(CSVFormat.TORONTO_GAIT)
            exporter.export_poses(sample_poses, output_path, include_metadata=False)
            
            # Read and verify CSV content
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
            
            # Should not include metadata columns
            assert 'pose_confidence' not in fieldnames
            assert 'total_joints' not in fieldnames
    
    def test_export_empty_poses_raises_error(self):
        """Test that exporting empty poses raises ValueError."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_empty.csv"
            
            exporter = CSVExporter()
            with pytest.raises(ValueError, match="Cannot export empty poses list"):
                exporter.export_poses([], output_path)
    
    def test_bounding_box_calculation(self, sample_poses):
        """Test bounding box calculation for poses."""
        exporter = CSVExporter()
        
        # Test with valid pose
        pose = sample_poses[0]
        bbox = exporter._calculate_bounding_box(pose)
        
        assert bbox is not None
        assert bbox['left'] == 95.0  # leftmost x
        assert bbox['right'] == 105.0  # rightmost x
        assert bbox['top'] == 45.0  # topmost y
        assert bbox['bottom'] == 50.0  # bottommost y
        
        # Test with pose having no valid joints
        empty_joints = [
            Joint(name="nose", keypoint=KeyPoint(x=0, y=0, confidence=0), joint_id=0)
        ]
        empty_pose = Pose(joints=empty_joints, person_id=0, confidence=0)
        bbox = exporter._calculate_bounding_box(empty_pose)
        assert bbox is None
    
    def test_get_available_formats(self):
        """Test getting list of available CSV formats."""
        formats = CSVExporter.get_available_formats()
        assert isinstance(formats, list)
        assert "toronto_gait" in formats
    
    def test_string_representations(self):
        """Test string representations of CSVExporter."""
        exporter = CSVExporter(CSVFormat.TORONTO_GAIT)
        
        str_repr = str(exporter)
        assert "toronto_gait" in str_repr
        
        repr_str = repr(exporter)
        assert "CSVExporter" in repr_str
        assert "TORONTO_GAIT" in repr_str
    
    def test_export_with_missing_frame_info(self):
        """Test CSV export when poses are missing frame information."""
        # Create pose without frame info
        joints = [
            Joint(name="nose", keypoint=KeyPoint(x=100.0, y=50.0, confidence=0.9), joint_id=0)
        ]
        pose = Pose(joints=joints, person_id=0, confidence=0.85)
        # Don't set frame_number or timestamp
        
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_missing_info.csv"
            
            exporter = CSVExporter(CSVFormat.TORONTO_GAIT)
            exporter.export_poses([pose], output_path)
            
            # Read and verify CSV content
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                row = next(reader)
            
            # Should handle missing frame info gracefully
            assert row['frame_number'] == ''
            assert row['timestamp'] == ''
    
    def test_export_with_unicode_joint_names(self):
        """Test CSV export with unicode characters in joint names."""
        joints = [
            Joint(name="nariz", keypoint=KeyPoint(x=100.0, y=50.0, confidence=0.9), joint_id=0),
            Joint(name="ojo_izquierdo", keypoint=KeyPoint(x=95.0, y=45.0, confidence=0.8), joint_id=1),
        ]
        pose = Pose(joints=joints, person_id=0, confidence=0.85)
        
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_unicode.csv"
            
            exporter = CSVExporter(CSVFormat.TORONTO_GAIT)
            exporter.export_poses([pose], output_path)
            
            assert output_path.exists()
            
            # Read and verify CSV content
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 2
            assert rows[0]['joint_name'] == 'nariz'
            assert rows[1]['joint_name'] == 'ojo_izquierdo' 