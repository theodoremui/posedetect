"""
Tests for Toronto Gait Archive export functionality.

This module contains tests for the Toronto Older Adults Gait Archive format
export functionality for both CSV and JSON formats.
"""

import pytest
import csv
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from src.posedetect.models.pose import Pose, Joint, KeyPoint
from src.posedetect.exporters.csv_exporter import CSVExporter, CSVFormat, TORONTO_GAIT_JOINT_ORDER
from src.posedetect.exporters.json_exporter import JSONExporter, JSONFormat


class TestTorontoGaitCSVExport:
    """Test cases for Toronto Gait Archive CSV export functionality."""
    
    @pytest.fixture
    def sample_poses(self) -> List[Pose]:
        """Create sample pose data for testing."""
        poses = []
        
        # Create pose 1 with typical COCO joints
        joints1 = [
            Joint(name="nose", keypoint=KeyPoint(x=320.5, y=240.3, confidence=0.9), joint_id=0),
            Joint(name="left_eye", keypoint=KeyPoint(x=315.0, y=235.0, confidence=0.8), joint_id=1),
            Joint(name="right_eye", keypoint=KeyPoint(x=325.0, y=235.0, confidence=0.85), joint_id=2),
            Joint(name="left_ear", keypoint=KeyPoint(x=310.0, y=240.0, confidence=0.75), joint_id=3),
            Joint(name="right_ear", keypoint=KeyPoint(x=330.0, y=240.0, confidence=0.8), joint_id=4),
            Joint(name="left_shoulder", keypoint=KeyPoint(x=300.0, y=280.0, confidence=0.9), joint_id=5),
            Joint(name="right_shoulder", keypoint=KeyPoint(x=340.0, y=280.0, confidence=0.88), joint_id=6),
            Joint(name="left_elbow", keypoint=KeyPoint(x=280.0, y=320.0, confidence=0.85), joint_id=7),
            Joint(name="right_elbow", keypoint=KeyPoint(x=360.0, y=320.0, confidence=0.87), joint_id=8),
            Joint(name="left_wrist", keypoint=KeyPoint(x=260.0, y=360.0, confidence=0.8), joint_id=9),
            Joint(name="right_wrist", keypoint=KeyPoint(x=380.0, y=360.0, confidence=0.82), joint_id=10),
            Joint(name="left_hip", keypoint=KeyPoint(x=305.0, y=400.0, confidence=0.9), joint_id=11),
            Joint(name="right_hip", keypoint=KeyPoint(x=335.0, y=400.0, confidence=0.92), joint_id=12),
            Joint(name="left_knee", keypoint=KeyPoint(x=300.0, y=480.0, confidence=0.85), joint_id=13),
            Joint(name="right_knee", keypoint=KeyPoint(x=340.0, y=480.0, confidence=0.88), joint_id=14),
            Joint(name="left_ankle", keypoint=KeyPoint(x=295.0, y=560.0, confidence=0.8), joint_id=15),
            Joint(name="right_ankle", keypoint=KeyPoint(x=345.0, y=560.0, confidence=0.83), joint_id=16),
        ]
        pose1 = Pose(joints=joints1, person_id=0, confidence=0.85)
        pose1.frame_number = 0
        pose1.timestamp = 0.0
        poses.append(pose1)
        
        # Create pose 2 with different values
        joints2 = [
            Joint(name="nose", keypoint=KeyPoint(x=325.0, y=245.0, confidence=0.88), joint_id=0),
            Joint(name="left_eye", keypoint=KeyPoint(x=320.0, y=240.0, confidence=0.82), joint_id=1),
            Joint(name="right_eye", keypoint=KeyPoint(x=330.0, y=240.0, confidence=0.8), joint_id=2),
            # Note: missing some joints to test zero-filling
            Joint(name="left_shoulder", keypoint=KeyPoint(x=305.0, y=285.0, confidence=0.88), joint_id=5),
            Joint(name="right_shoulder", keypoint=KeyPoint(x=345.0, y=285.0, confidence=0.9), joint_id=6),
        ]
        pose2 = Pose(joints=joints2, person_id=1, confidence=0.82)
        pose2.frame_number = 1
        pose2.timestamp = 0.033
        poses.append(pose2)
        
        return poses
    
    def test_toronto_gait_csv_export(self, sample_poses):
        """Test basic Toronto Gait CSV export functionality."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "toronto_gait_test.csv"
            
            exporter = CSVExporter(CSVFormat.TORONTO_GAIT)
            exporter.export_poses(sample_poses, output_path)
            
            # Verify file exists
            assert output_path.exists()
            
            # Read and verify CSV content
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Should have 2 rows (one per pose)
            assert len(rows) == 2
            
            # Check header format
            fieldnames = reader.fieldnames
            assert fieldnames[0] == "time"
            
            # Check that all Toronto joints are present in header
            for joint_name in TORONTO_GAIT_JOINT_ORDER:
                assert f"{joint_name}_x" in fieldnames
                assert f"{joint_name}_y" in fieldnames
                assert f"{joint_name}_conf" in fieldnames
    
    def test_toronto_gait_csv_joint_mapping(self, sample_poses):
        """Test that COCO joint names are correctly mapped to Toronto format."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "toronto_mapping_test.csv"
            
            exporter = CSVExporter(CSVFormat.TORONTO_GAIT)
            exporter.export_poses(sample_poses, output_path)
            
            # Read CSV content
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                first_row = next(reader)
            
            # Check that nose joint was correctly mapped
            assert float(first_row['Nose_x']) == 320.5
            assert float(first_row['Nose_y']) == 240.3
            assert float(first_row['Nose_conf']) == 0.9
            
            # Check that left eye was correctly mapped
            assert float(first_row['LEye_x']) == 315.0
            assert float(first_row['LEye_y']) == 235.0
            assert float(first_row['LEye_conf']) == 0.8
            
            # Check that right shoulder was correctly mapped
            assert float(first_row['RShoulder_x']) == 340.0
            assert float(first_row['RShoulder_y']) == 280.0
            assert float(first_row['RShoulder_conf']) == 0.88
    
    def test_toronto_gait_csv_missing_joints(self, sample_poses):
        """Test that missing joints are filled with zeros."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "toronto_missing_test.csv"
            
            exporter = CSVExporter(CSVFormat.TORONTO_GAIT)
            exporter.export_poses(sample_poses, output_path)
            
            # Read CSV content - check second pose which has missing joints
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                next(reader)  # Skip first row
                second_row = next(reader)
            
            # Check that missing joints are zero-filled
            # Second pose is missing ears, elbows, wrists, hips, knees, ankles
            assert float(second_row['LEar_x']) == 0.0
            assert float(second_row['LEar_y']) == 0.0
            assert float(second_row['LEar_conf']) == 0.0
            
            assert float(second_row['RElbow_x']) == 0.0
            assert float(second_row['RElbow_y']) == 0.0
            assert float(second_row['RElbow_conf']) == 0.0
    
    def test_toronto_gait_csv_timestamps(self, sample_poses):
        """Test that timestamps are correctly exported."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "toronto_timestamps_test.csv"
            
            exporter = CSVExporter(CSVFormat.TORONTO_GAIT)
            exporter.export_poses(sample_poses, output_path)
            
            # Read CSV content
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Check timestamps
            assert float(rows[0]['time']) == 0.0
            assert float(rows[1]['time']) == 0.033


class TestTorontoGaitJSONExport:
    """Test cases for Toronto Gait Archive JSON export functionality."""
    
    @pytest.fixture
    def sample_poses(self) -> List[Pose]:
        """Create sample pose data for testing."""
        poses = []
        
        # Create pose with all COCO joints
        joints = [
            Joint(name="nose", keypoint=KeyPoint(x=320.5, y=240.3, confidence=0.9), joint_id=0),
            Joint(name="left_eye", keypoint=KeyPoint(x=315.0, y=235.0, confidence=0.8), joint_id=1),
            Joint(name="right_eye", keypoint=KeyPoint(x=325.0, y=235.0, confidence=0.85), joint_id=2),
            Joint(name="left_shoulder", keypoint=KeyPoint(x=300.0, y=280.0, confidence=0.9), joint_id=5),
            Joint(name="right_shoulder", keypoint=KeyPoint(x=340.0, y=280.0, confidence=0.88), joint_id=6),
        ]
        pose = Pose(joints=joints, person_id=0, confidence=0.85)
        pose.frame_number = 0
        pose.timestamp = 0.0
        poses.append(pose)
        
        return poses
    
    def test_toronto_gait_json_export(self, sample_poses):
        """Test basic Toronto Gait JSON export functionality."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "toronto_gait_test.json"
            
            exporter = JSONExporter(JSONFormat.TORONTO_GAIT)
            exporter.export_poses(sample_poses, output_path)
            
            # Verify file exists
            assert output_path.exists()
            
            # Read and verify JSON content
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check structure
            assert 'metadata' in data
            assert 'frames' in data
            
            # Check metadata
            metadata = data['metadata']
            assert metadata['format'] == 'toronto_gait'
            assert metadata['joint_format'] == 'COCO_17'
            assert metadata['joint_order'] == TORONTO_GAIT_JOINT_ORDER
            assert metadata['reference'] == "Toronto Older Adults Gait Archive (Nature Scientific Data, 2022)"
            assert metadata['doi'] == "10.1038/s41597-022-01495-z"
            
            # Check frames
            frames = data['frames']
            assert len(frames) == 1
            
            frame = frames[0]
            assert frame['frame_number'] == 0
            assert frame['timestamp'] == 0.0
            assert frame['person_id'] == 0
            assert 'keypoints' in frame
    
    def test_toronto_gait_json_keypoints_structure(self, sample_poses):
        """Test the keypoints structure in Toronto Gait JSON format."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "toronto_keypoints_test.json"
            
            exporter = JSONExporter(JSONFormat.TORONTO_GAIT)
            exporter.export_poses(sample_poses, output_path)
            
            # Read JSON content
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            keypoints = data['frames'][0]['keypoints']
            
            # Check that all Toronto joints are present
            for joint_name in TORONTO_GAIT_JOINT_ORDER:
                assert joint_name in keypoints
                assert 'x' in keypoints[joint_name]
                assert 'y' in keypoints[joint_name]
                assert 'confidence' in keypoints[joint_name]
            
            # Check specific values for detected joints
            assert keypoints['Nose']['x'] == 320.5
            assert keypoints['Nose']['y'] == 240.3
            assert keypoints['Nose']['confidence'] == 0.9
            
            assert keypoints['LEye']['x'] == 315.0
            assert keypoints['LEye']['y'] == 235.0
            assert keypoints['LEye']['confidence'] == 0.8
            
            # Check that missing joints are zero-filled
            assert keypoints['LEar']['x'] == 0.0
            assert keypoints['LEar']['y'] == 0.0
            assert keypoints['LEar']['confidence'] == 0.0
    
    def test_toronto_gait_json_multiple_frames(self):
        """Test Toronto Gait JSON export with multiple frames."""
        poses = []
        
        # Create poses for multiple frames
        for frame in range(3):
            joints = [
                Joint(name="nose", keypoint=KeyPoint(x=320.0 + frame, y=240.0 + frame, confidence=0.9), joint_id=0),
                Joint(name="left_shoulder", keypoint=KeyPoint(x=300.0 + frame, y=280.0 + frame, confidence=0.85), joint_id=5),
            ]
            pose = Pose(joints=joints, person_id=0, confidence=0.8)
            pose.frame_number = frame
            pose.timestamp = frame * 0.033
            poses.append(pose)
        
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "toronto_multiframe_test.json"
            
            exporter = JSONExporter(JSONFormat.TORONTO_GAIT)
            exporter.export_poses(poses, output_path)
            
            # Read JSON content
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            frames = data['frames']
            assert len(frames) == 3
            
            # Check frame progression
            for i, frame in enumerate(frames):
                assert frame['frame_number'] == i
                assert frame['timestamp'] == i * 0.033
                assert frame['keypoints']['Nose']['x'] == 320.0 + i
                assert frame['keypoints']['Nose']['y'] == 240.0 + i


class TestTorontoGaitIntegration:
    """Integration tests for Toronto Gait Archive export functionality."""
    
    def test_csv_json_consistency(self):
        """Test that CSV and JSON exports produce consistent data."""
        # Create sample pose data
        joints = [
            Joint(name="nose", keypoint=KeyPoint(x=100.0, y=50.0, confidence=0.9), joint_id=0),
            Joint(name="left_eye", keypoint=KeyPoint(x=95.0, y=45.0, confidence=0.8), joint_id=1),
            Joint(name="right_shoulder", keypoint=KeyPoint(x=120.0, y=80.0, confidence=0.75), joint_id=6),
        ]
        pose = Pose(joints=joints, person_id=0, confidence=0.85)
        pose.frame_number = 0
        pose.timestamp = 1.5
        poses = [pose]
        
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "consistency_test.csv"
            json_path = Path(temp_dir) / "consistency_test.json"
            
            # Export to both formats
            csv_exporter = CSVExporter(CSVFormat.TORONTO_GAIT)
            csv_exporter.export_poses(poses, csv_path)
            
            json_exporter = JSONExporter(JSONFormat.TORONTO_GAIT)
            json_exporter.export_poses(poses, json_path)
            
            # Read CSV data
            with open(csv_path, 'r', encoding='utf-8') as f:
                csv_reader = csv.DictReader(f)
                csv_row = next(csv_reader)
            
            # Read JSON data
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            json_frame = json_data['frames'][0]
            
            # Compare timestamps
            assert float(csv_row['time']) == json_frame['timestamp']
            
            # Compare keypoint data
            assert float(csv_row['Nose_x']) == json_frame['keypoints']['Nose']['x']
            assert float(csv_row['Nose_y']) == json_frame['keypoints']['Nose']['y']
            assert float(csv_row['Nose_conf']) == json_frame['keypoints']['Nose']['confidence']
            
            assert float(csv_row['LEye_x']) == json_frame['keypoints']['LEye']['x']
            assert float(csv_row['LEye_y']) == json_frame['keypoints']['LEye']['y']
            assert float(csv_row['LEye_conf']) == json_frame['keypoints']['LEye']['confidence']
            
            # Check missing joints are zero in both formats
            assert float(csv_row['REye_x']) == json_frame['keypoints']['REye']['x'] == 0.0
            assert float(csv_row['REye_y']) == json_frame['keypoints']['REye']['y'] == 0.0
            assert float(csv_row['REye_conf']) == json_frame['keypoints']['REye']['confidence'] == 0.0
    
    def test_format_availability(self):
        """Test that Toronto Gait format is available in format lists."""
        # Test CSV format availability
        csv_formats = CSVExporter.get_available_formats()
        assert 'toronto_gait' in csv_formats
        
        # Test JSON format availability
        json_formats = JSONExporter.get_available_formats()
        assert 'toronto_gait' in json_formats
    
    def test_empty_poses_handling(self):
        """Test handling of empty poses list."""
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "empty_test.csv"
            json_path = Path(temp_dir) / "empty_test.json"
            
            csv_exporter = CSVExporter(CSVFormat.TORONTO_GAIT)
            json_exporter = JSONExporter(JSONFormat.TORONTO_GAIT)
            
            # Should raise ValueError for empty poses
            with pytest.raises(ValueError, match="Cannot export empty poses list"):
                csv_exporter.export_poses([], csv_path)
            
            with pytest.raises(ValueError, match="Cannot export empty poses list"):
                json_exporter.export_poses([], json_path) 