"""
Tests for video overlay generation functionality.

This module contains tests for the video overlay generator including
configuration, video processing, and overlay creation.
"""

import pytest
import json
import numpy as np
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch, MagicMock
from typing import List

from src.posedetect.models.pose import Pose, Joint, KeyPoint
from src.posedetect.video.overlay_generator import (
    VideoOverlayGenerator, 
    OverlayConfig
)


class TestOverlayConfig:
    """Test cases for OverlayConfig dataclass."""
    
    def test_default_config(self):
        """Test default overlay configuration."""
        config = OverlayConfig()
        
        assert config.output_codec == 'mp4v'
        assert config.output_fps is None
        assert config.output_quality == 90
        assert config.skeleton_color == (0, 255, 0)
        assert config.joint_color == (255, 0, 0)
        assert config.confidence_threshold == 0.1
        assert config.line_thickness == 2
        assert config.joint_radius == 4
        assert config.show_confidence is True
        assert config.show_person_id is True
    
    def test_custom_config(self):
        """Test custom overlay configuration."""
        config = OverlayConfig(
            output_codec='XVID',
            skeleton_color=(255, 0, 0),
            confidence_threshold=0.5,
            show_confidence=False
        )
        
        assert config.output_codec == 'XVID'
        assert config.skeleton_color == (255, 0, 0)
        assert config.confidence_threshold == 0.5
        assert config.show_confidence is False


class TestVideoOverlayGenerator:
    """Test cases for VideoOverlayGenerator."""
    
    @pytest.fixture
    def sample_poses(self) -> List[Pose]:
        """Create sample pose data for testing."""
        poses = []
        
        # Create pose with multiple joints
        joints = [
            Joint(name="nose", keypoint=KeyPoint(x=100.0, y=50.0, confidence=0.9), joint_id=0),
            Joint(name="left_eye", keypoint=KeyPoint(x=95.0, y=45.0, confidence=0.8), joint_id=1),
            Joint(name="right_eye", keypoint=KeyPoint(x=105.0, y=45.0, confidence=0.85), joint_id=2),
            Joint(name="left_shoulder", keypoint=KeyPoint(x=80.0, y=80.0, confidence=0.7), joint_id=5),
            Joint(name="right_shoulder", keypoint=KeyPoint(x=120.0, y=80.0, confidence=0.75), joint_id=6),
        ]
        pose = Pose(joints=joints, person_id=0, confidence=0.8)
        pose.frame_number = 0
        pose.timestamp = 0.0
        poses.append(pose)
        
        return poses
    
    @pytest.fixture
    def sample_config(self) -> OverlayConfig:
        """Create sample overlay configuration."""
        return OverlayConfig(
            confidence_threshold=0.5,
            line_thickness=3,
            joint_radius=5
        )
    
    def test_generator_initialization(self):
        """Test video overlay generator initialization."""
        # Test with default config
        generator = VideoOverlayGenerator()
        assert generator.config is not None
        assert isinstance(generator.config, OverlayConfig)
        
        # Test with custom config
        custom_config = OverlayConfig(output_codec='XVID')
        generator = VideoOverlayGenerator(custom_config)
        assert generator.config.output_codec == 'XVID'
    
    def test_dict_to_pose_conversion(self, sample_poses):
        """Test conversion from dictionary to Pose object."""
        generator = VideoOverlayGenerator()
        
        # Convert pose to dict and back
        pose_dict = sample_poses[0].to_dict()
        converted_pose = generator._dict_to_pose(pose_dict)
        
        assert converted_pose.person_id == sample_poses[0].person_id
        assert converted_pose.confidence == sample_poses[0].confidence
        assert len(converted_pose.joints) == len(sample_poses[0].joints)
        
        # Check first joint
        original_joint = sample_poses[0].joints[0]
        converted_joint = converted_pose.joints[0]
        assert converted_joint.name == original_joint.name
        assert converted_joint.keypoint.x == original_joint.keypoint.x
        assert converted_joint.keypoint.y == original_joint.keypoint.y
        assert converted_joint.keypoint.confidence == original_joint.keypoint.confidence
    
    def test_load_poses_from_json_file(self, sample_poses):
        """Test loading poses from JSON file."""
        with TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "test_poses.json"
            
            # Create test JSON file
            poses_data = {
                "poses": [pose.to_dict() for pose in sample_poses]
            }
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(poses_data, f)
            
            generator = VideoOverlayGenerator()
            loaded_poses = generator._load_poses_from_file(json_path)
            
            assert len(loaded_poses) == len(sample_poses)
            assert loaded_poses[0].person_id == sample_poses[0].person_id
    
    def test_load_poses_from_list_format(self, sample_poses):
        """Test loading poses from JSON file with list format."""
        with TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "test_poses_list.json"
            
            # Create test JSON file with list format
            poses_data = [pose.to_dict() for pose in sample_poses]
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(poses_data, f)
            
            generator = VideoOverlayGenerator()
            loaded_poses = generator._load_poses_from_file(json_path)
            
            assert len(loaded_poses) == len(sample_poses)
    
    def test_load_poses_file_not_found(self):
        """Test loading poses from non-existent file."""
        generator = VideoOverlayGenerator()
        
        with pytest.raises(FileNotFoundError):
            generator._load_poses_from_file("non_existent_file.json")
    
    def test_load_poses_invalid_json(self):
        """Test loading poses from invalid JSON file."""
        with TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "invalid.json"
            
            # Create invalid JSON file
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write("invalid json content")
            
            generator = VideoOverlayGenerator()
            with pytest.raises(ValueError, match="Invalid pose data file format"):
                generator._load_poses_from_file(json_path)
    
    def test_group_poses_by_frame(self, sample_poses):
        """Test grouping poses by frame number."""
        # Add more poses with different frame numbers
        pose2 = Pose(joints=sample_poses[0].joints, person_id=1, confidence=0.7)
        pose2.frame_number = 0  # Same frame as first pose
        
        pose3 = Pose(joints=sample_poses[0].joints, person_id=0, confidence=0.6)
        pose3.frame_number = 1  # Different frame
        
        all_poses = sample_poses + [pose2, pose3]
        
        generator = VideoOverlayGenerator()
        grouped = generator._group_poses_by_frame(all_poses)
        
        assert len(grouped) == 2  # Two different frames
        assert len(grouped[0]) == 2  # Two poses in frame 0
        assert len(grouped[1]) == 1  # One pose in frame 1
    
    def test_draw_skeleton_connections(self, sample_poses):
        """Test drawing skeleton connections on frame."""
        generator = VideoOverlayGenerator()
        
        # Create mock frame
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # Draw skeleton (this mostly tests that it doesn't crash)
        generator._draw_skeleton(frame, sample_poses[0].joints)
        
        # Frame should be modified (not all zeros)
        assert not np.array_equal(frame, np.zeros((200, 200, 3), dtype=np.uint8))
    
    def test_draw_joints(self, sample_poses):
        """Test drawing joint points on frame."""
        generator = VideoOverlayGenerator()
        
        # Create mock frame
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # Draw joints
        generator._draw_joints(frame, sample_poses[0].joints)
        
        # Frame should be modified
        assert not np.array_equal(frame, np.zeros((200, 200, 3), dtype=np.uint8))
    
    def test_draw_person_info(self, sample_poses):
        """Test drawing person information on frame."""
        config = OverlayConfig(show_person_id=True, show_confidence=True)
        generator = VideoOverlayGenerator(config)
        
        # Create mock frame
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # Draw person info
        generator._draw_person_info(frame, sample_poses[0], sample_poses[0].joints)
        
        # Frame should be modified
        assert not np.array_equal(frame, np.zeros((200, 200, 3), dtype=np.uint8))
    
    def test_draw_poses_on_frame(self, sample_poses):
        """Test drawing complete poses on frame."""
        generator = VideoOverlayGenerator()
        
        # Create mock frame
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        
        # Draw poses
        overlay_frame = generator._draw_poses_on_frame(frame, sample_poses)
        
        # Should return a new frame
        assert overlay_frame.shape == frame.shape
        assert not np.array_equal(overlay_frame, frame)
    
    def test_draw_poses_with_confidence_filter(self, sample_poses):
        """Test drawing poses with confidence threshold filtering."""
        config = OverlayConfig(confidence_threshold=0.9)  # High threshold
        generator = VideoOverlayGenerator(config)
        
        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        overlay_frame = generator._draw_poses_on_frame(frame, sample_poses)
        
        # Should still return a frame (even if minimal drawing due to threshold)
        assert overlay_frame.shape == frame.shape
    
    @patch('cv2.VideoCapture')
    def test_get_video_info(self, mock_cv2_cap):
        """Test getting video information."""
        # Mock video capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            1: 1920,  # width
            2: 1080,  # height
            3: 30.0,  # fps
            4: 100,   # frame count
            5: 12345  # codec
        }.get(prop, 0)
        mock_cv2_cap.return_value = mock_cap
        
        generator = VideoOverlayGenerator()
        
        with TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            video_path.touch()  # Create empty file
            
            info = generator.get_video_info(video_path)
            
            assert info['width'] == 1920
            assert info['height'] == 1080
            assert info['fps'] == 30.0
            assert info['frame_count'] == 100
            assert info['duration'] == 100 / 30.0
    
    def test_get_video_info_file_not_found(self):
        """Test getting video info for non-existent file."""
        generator = VideoOverlayGenerator()
        
        with pytest.raises(FileNotFoundError):
            generator.get_video_info("non_existent_video.mp4")
    
    @patch('cv2.VideoCapture')
    def test_get_video_info_cannot_open(self, mock_cv2_cap):
        """Test getting video info when video cannot be opened."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_cv2_cap.return_value = mock_cap
        
        generator = VideoOverlayGenerator()
        
        with TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test_video.mp4"
            video_path.touch()
            
            with pytest.raises(RuntimeError, match="Could not open video"):
                generator.get_video_info(video_path)
    
    def test_string_representations(self):
        """Test string representations of VideoOverlayGenerator."""
        config = OverlayConfig(output_codec='XVID')
        generator = VideoOverlayGenerator(config)
        
        str_repr = str(generator)
        assert "XVID" in str_repr
        
        repr_str = repr(generator)
        assert "VideoOverlayGenerator" in repr_str
    
    @patch('cv2.VideoCapture')
    @patch('cv2.VideoWriter')
    def test_generate_overlay_video_mock(self, mock_writer, mock_cap, sample_poses):
        """Test overlay video generation with mocked CV2."""
        # Mock video capture
        mock_cap_instance = Mock()
        mock_cap_instance.isOpened.return_value = True
        mock_cap_instance.get.side_effect = lambda prop: {
            1: 640,   # width
            2: 480,   # height  
            3: 30.0,  # fps
            4: 5      # frame count
        }.get(prop, 0)
        
        # Mock frame reading
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_cap_instance.read.side_effect = [
            (True, frame), (True, frame), (True, frame), 
            (True, frame), (True, frame), (False, None)
        ]
        mock_cap.return_value = mock_cap_instance
        
        # Mock video writer
        mock_writer_instance = Mock()
        mock_writer_instance.isOpened.return_value = True
        mock_writer.return_value = mock_writer_instance
        
        generator = VideoOverlayGenerator()
        
        with TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.mp4"
            output_path = Path(temp_dir) / "output.mp4"
            input_path.touch()
            
            # Test with pose list
            generator.generate_overlay_video(
                input_video_path=input_path,
                poses_data=sample_poses,
                output_video_path=output_path
            )
            
            # Verify video writer was called
            mock_writer_instance.write.assert_called()
    
    def test_generate_overlay_video_input_not_found(self, sample_poses):
        """Test overlay generation with non-existent input video."""
        generator = VideoOverlayGenerator()
        
        with pytest.raises(FileNotFoundError, match="Input video not found"):
            generator.generate_overlay_video(
                input_video_path="non_existent.mp4",
                poses_data=sample_poses,
                output_video_path="output.mp4"
            ) 