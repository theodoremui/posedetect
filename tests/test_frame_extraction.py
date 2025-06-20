"""
Tests for frame extraction functionality.

This module provides comprehensive tests for the frame extraction system,
including configuration, extractors, and the manager class.
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import cv2

from posedetect.video.frame_extraction import (
    FrameExtractionConfig,
    RawFrameExtractor,
    OverlayFrameExtractor,
    FrameExtractionManager
)
from posedetect.models.pose import Pose, Joint, KeyPoint


class TestFrameExtractionConfig:
    """Test cases for FrameExtractionConfig."""

    def test_default_config(self):
        """Test default configuration values."""
        config = FrameExtractionConfig()
        
        assert config.base_output_directory == "outputs"
        assert config.extract_raw_frames is True
        assert config.extract_overlay_frames is True
        assert config.raw_image_format == "jpg"
        assert config.overlay_image_format == "jpg"
        assert config.raw_image_quality == 95
        assert config.overlay_image_quality == 95
        assert config.confidence_threshold == 0.1
        assert config.frame_range is None
        assert config.frame_skip == 1

    def test_custom_config(self):
        """Test custom configuration values."""
        config = FrameExtractionConfig(
            base_output_directory="/custom/output",
            extract_raw_frames=False,
            raw_image_format="png",
            raw_image_quality=80,
            confidence_threshold=0.3,
            frame_range=(10, 50),
            frame_skip=2
        )
        
        assert config.base_output_directory == "/custom/output"
        assert config.extract_raw_frames is False
        assert config.raw_image_format == "png"
        assert config.raw_image_quality == 80
        assert config.confidence_threshold == 0.3
        assert config.frame_range == (10, 50)
        assert config.frame_skip == 2

    def test_config_validation_invalid_quality(self):
        """Test configuration validation for invalid quality values."""
        with pytest.raises(ValueError, match="Raw image quality must be between 0 and 100"):
            FrameExtractionConfig(raw_image_quality=150)
        
        with pytest.raises(ValueError, match="Overlay image quality must be between 0 and 100"):
            FrameExtractionConfig(overlay_image_quality=-10)

    def test_config_validation_invalid_format(self):
        """Test configuration validation for invalid image formats."""
        with pytest.raises(ValueError, match="Unsupported raw image format"):
            FrameExtractionConfig(raw_image_format="xyz")

    def test_config_validation_invalid_frame_range(self):
        """Test configuration validation for invalid frame ranges."""
        with pytest.raises(ValueError, match="Frame range must be a tuple"):
            FrameExtractionConfig(frame_range=(10,))
        
        with pytest.raises(ValueError, match="Frame range start must be less than end"):
            FrameExtractionConfig(frame_range=(50, 10))

    def test_config_validation_invalid_frame_skip(self):
        """Test configuration validation for invalid frame skip."""
        with pytest.raises(ValueError, match="Frame skip must be at least 1"):
            FrameExtractionConfig(frame_skip=0)

    def test_get_directory_name(self):
        """Test directory name generation."""
        config = FrameExtractionConfig()
        
        directory_name = config.get_directory_name("frames", "test_video", "20250619_140530")
        assert directory_name == "frames_test_video_20250619_140530"
        
        directory_name = config.get_directory_name("overlay", "my_video", "20250619_140530")
        assert directory_name == "overlay_my_video_20250619_140530"

    def test_get_frame_filename(self):
        """Test frame filename generation."""
        config = FrameExtractionConfig()
        
        filename = config.get_frame_filename(0, "jpg")
        assert filename == "frame_00000.jpg"
        
        filename = config.get_frame_filename(123, "png")
        assert filename == "frame_00123.png"


class TestRawFrameExtractor:
    """Test cases for RawFrameExtractor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = RawFrameExtractor()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = FrameExtractionConfig(
            raw_image_format="jpg",
            raw_image_quality=90
        )

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_extract_frames_file_not_found(self):
        """Test extraction with non-existent video file."""
        non_existent_video = self.temp_dir / "non_existent.mp4"
        output_dir = self.temp_dir / "output"
        
        with pytest.raises(FileNotFoundError, match="Video file not found"):
            self.extractor.extract_frames(non_existent_video, output_dir, self.config)

    @patch('cv2.VideoCapture')
    def test_extract_frames_video_open_failure(self, mock_video_capture):
        """Test extraction when video cannot be opened."""
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap
        
        # Create a dummy video file
        video_path = self.temp_dir / "test.mp4"
        video_path.touch()
        output_dir = self.temp_dir / "output"
        
        with pytest.raises(RuntimeError, match="Could not open video"):
            self.extractor.extract_frames(video_path, output_dir, self.config)

    @patch('cv2.VideoCapture')
    @patch('cv2.imwrite')
    def test_extract_frames_success(self, mock_imwrite, mock_video_capture):
        """Test successful frame extraction."""
        # Mock video capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 5,
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480
        }.get(prop, 0)
        
        # Mock frames
        mock_frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(5)]
        mock_cap.read.side_effect = [(True, frame) for frame in mock_frames] + [(False, None)]
        mock_video_capture.return_value = mock_cap
        
        # Mock successful image writing
        mock_imwrite.return_value = True
        
        # Create dummy video file
        video_path = self.temp_dir / "test.mp4"
        video_path.touch()
        output_dir = self.temp_dir / "output"
        
        # Extract frames
        extracted_files = self.extractor.extract_frames(video_path, output_dir, self.config)
        
        # Verify results
        assert len(extracted_files) == 5
        assert output_dir.exists()
        
        # Verify file names
        expected_names = [f"frame_{i:05d}.jpg" for i in range(5)]
        for i, file_path in enumerate(extracted_files):
            assert file_path.name == expected_names[i]

    @patch('cv2.VideoCapture')
    @patch('cv2.imwrite')
    def test_extract_frames_with_range(self, mock_imwrite, mock_video_capture):
        """Test frame extraction with specified range."""
        # Mock video capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 10,
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480
        }.get(prop, 0)
        
        # Mock frames
        mock_frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(10)]
        mock_cap.read.side_effect = [(True, frame) for frame in mock_frames] + [(False, None)]
        mock_video_capture.return_value = mock_cap
        
        # Mock successful image writing
        mock_imwrite.return_value = True
        
        # Create dummy video file
        video_path = self.temp_dir / "test.mp4"
        video_path.touch()
        output_dir = self.temp_dir / "output"
        
        # Set frame range
        config_with_range = FrameExtractionConfig(
            frame_range=(2, 6),
            raw_image_format="jpg"
        )
        
        # Extract frames
        extracted_files = self.extractor.extract_frames(video_path, output_dir, config_with_range)
        
        # Verify results - should extract frames 2, 3, 4, 5
        assert len(extracted_files) == 4

    def test_save_frame_jpg(self):
        """Test saving frame as JPEG."""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        output_path = self.temp_dir / "test_frame.jpg"
        
        with patch('cv2.imwrite') as mock_imwrite:
            mock_imwrite.return_value = True
            
            result = self.extractor._save_frame(frame, output_path, "jpg", 90)
            
            assert result is True
            mock_imwrite.assert_called_once()
            args, kwargs = mock_imwrite.call_args
            assert args[0] == str(output_path)
            assert np.array_equal(args[1], frame)
            assert args[2] == [cv2.IMWRITE_JPEG_QUALITY, 90]

    def test_save_frame_png(self):
        """Test saving frame as PNG."""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        output_path = self.temp_dir / "test_frame.png"
        
        with patch('cv2.imwrite') as mock_imwrite:
            mock_imwrite.return_value = True
            
            result = self.extractor._save_frame(frame, output_path, "png", 90)
            
            assert result is True
            mock_imwrite.assert_called_once()
            args, kwargs = mock_imwrite.call_args
            assert args[0] == str(output_path)
            assert np.array_equal(args[1], frame)
            # PNG compression should be calculated from quality
            expected_compression = max(0, min(9, int((100 - 90) / 11)))
            assert args[2] == [cv2.IMWRITE_PNG_COMPRESSION, expected_compression]


class TestOverlayFrameExtractor:
    """Test cases for OverlayFrameExtractor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = OverlayFrameExtractor()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = FrameExtractionConfig()
        
        # Create sample poses
        self.poses = self._create_sample_poses()

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _create_sample_poses(self):
        """Create sample poses for testing."""
        poses = []
        
        for frame in range(3):
            joints = []
            joint_names = ['nose', 'left_shoulder', 'right_shoulder']
            
            for i, joint_name in enumerate(joint_names):
                keypoint = KeyPoint(
                    x=100 + i * 50,
                    y=100 + frame * 10,
                    confidence=0.8
                )
                joint = Joint(
                    name=joint_name,
                    keypoint=keypoint,
                    joint_id=i
                )
                joints.append(joint)
            
            pose = Pose(
                joints=joints,
                person_id=0,
                confidence=0.8
            )
            pose.frame_number = frame
            poses.append(pose)
        
        return poses

    def test_group_poses_by_frame(self):
        """Test grouping poses by frame number."""
        poses_by_frame = self.extractor._group_poses_by_frame(self.poses)
        
        assert len(poses_by_frame) == 3
        assert 0 in poses_by_frame
        assert 1 in poses_by_frame
        assert 2 in poses_by_frame
        
        for frame_num in range(3):
            assert len(poses_by_frame[frame_num]) == 1
            assert poses_by_frame[frame_num][0].frame_number == frame_num

    def test_extract_frames_no_poses(self):
        """Test extraction when no pose data is provided."""
        video_path = self.temp_dir / "test.mp4"
        video_path.touch()
        output_dir = self.temp_dir / "output"
        
        with pytest.raises(ValueError, match="Either poses or poses_by_frame must be provided"):
            self.extractor.extract_frames(video_path, output_dir, self.config)

    @patch('cv2.VideoCapture')
    @patch('cv2.imwrite')
    def test_extract_frames_with_poses(self, mock_imwrite, mock_video_capture):
        """Test successful overlay frame extraction."""
        # Mock video capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_COUNT: 3,
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480
        }.get(prop, 0)
        
        # Mock frames
        mock_frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(3)]
        mock_cap.read.side_effect = [(True, frame) for frame in mock_frames] + [(False, None)]
        mock_video_capture.return_value = mock_cap
        
        # Mock successful image writing
        mock_imwrite.return_value = True
        
        # Create dummy video file
        video_path = self.temp_dir / "test.mp4"
        video_path.touch()
        output_dir = self.temp_dir / "output"
        
        # Extract frames with poses
        extracted_files = self.extractor.extract_frames(
            video_path, output_dir, self.config, poses=self.poses
        )
        
        # Verify results
        assert len(extracted_files) == 3
        assert output_dir.exists()

    def test_draw_poses_on_frame(self):
        """Test drawing poses on a frame."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Draw poses on frame
        result_frame = self.extractor._draw_poses_on_frame(frame, [self.poses[0]], self.config)
        
        # Verify frame was modified (should not be all zeros after drawing)
        assert not np.array_equal(frame, result_frame)
        assert result_frame.shape == frame.shape


class TestFrameExtractionManager:
    """Test cases for FrameExtractionManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config = FrameExtractionConfig(
            base_output_directory=str(self.temp_dir)
        )
        self.manager = FrameExtractionManager(self.config)
        self.poses = self._create_sample_poses()

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _create_sample_poses(self):
        """Create sample poses for testing."""
        joints = [
            Joint(
                name="nose",
                keypoint=KeyPoint(x=100, y=100, confidence=0.8),
                joint_id=0
            )
        ]
        
        pose = Pose(joints=joints, person_id=0, confidence=0.8)
        pose.frame_number = 0
        return [pose]

    def test_get_video_name(self):
        """Test video name extraction."""
        video_path = Path("/path/to/test_video.mp4")
        video_name = self.manager._get_video_name(video_path)
        assert video_name == "test_video"

    def test_generate_timestamp(self):
        """Test timestamp generation."""
        timestamp = self.manager._generate_timestamp()
        assert len(timestamp) == 15  # YYYYMMDD_HHMMSS format
        assert '_' in timestamp

    def test_create_output_directories(self):
        """Test output directory creation."""
        directories = self.manager._create_output_directories(
            "test_video", "20250619_140530", self.temp_dir
        )
        
        assert "raw" in directories
        assert "overlay" in directories
        
        raw_dir = directories["raw"]
        overlay_dir = directories["overlay"]
        
        assert raw_dir.exists()
        assert overlay_dir.exists()
        assert "frames_test_video_20250619_140530" in str(raw_dir)
        assert "overlay_test_video_20250619_140530" in str(overlay_dir)

    def test_extract_all_frame_types_file_not_found(self):
        """Test extraction with non-existent video file."""
        non_existent_video = self.temp_dir / "non_existent.mp4"
        
        with pytest.raises(FileNotFoundError, match="Video file not found"):
            self.manager.extract_all_frame_types(non_existent_video, self.poses)

    @patch.object(RawFrameExtractor, 'extract_frames')
    @patch.object(OverlayFrameExtractor, 'extract_frames')
    def test_extract_all_frame_types_success(self, mock_overlay_extract, mock_raw_extract):
        """Test successful extraction of all frame types."""
        # Mock successful extractions
        mock_raw_files = [Path("frame_00000.jpg"), Path("frame_00001.jpg")]
        mock_overlay_files = [Path("frame_00000.jpg"), Path("frame_00001.jpg")]
        
        mock_raw_extract.return_value = mock_raw_files
        mock_overlay_extract.return_value = mock_overlay_files
        
        # Create dummy video file
        video_path = self.temp_dir / "test.mp4"
        video_path.touch()
        
        # Extract frames
        results = self.manager.extract_all_frame_types(video_path, self.poses)
        
        # Verify results structure
        assert "raw_frames" in results
        assert "overlay_frames" in results
        assert "directories" in results
        
        assert len(results["raw_frames"]) == 2
        assert len(results["overlay_frames"]) == 2
        assert "raw" in results["directories"]
        assert "overlay" in results["directories"]

    def test_get_extraction_summary(self):
        """Test extraction summary generation."""
        # Mock results
        results = {
            "raw_frames": [Path("frame_00000.jpg"), Path("frame_00001.jpg")],
            "overlay_frames": [Path("frame_00000.jpg")],
            "directories": {
                "raw": Path("/path/to/raw"),
                "overlay": Path("/path/to/overlay")
            }
        }
        
        summary = self.manager.get_extraction_summary(results)
        
        assert summary["total_raw_frames"] == 2
        assert summary["total_overlay_frames"] == 1
        assert summary["directories_created"] == 2
        assert summary["extraction_types"] == ["raw", "overlay"]
        assert "/path/to/raw" in summary["output_directories"]["raw"]
        assert "/path/to/overlay" in summary["output_directories"]["overlay"]


class TestIntegration:
    """Integration tests for frame extraction functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_config_to_json_serialization(self):
        """Test that configuration can be serialized to JSON."""
        config = FrameExtractionConfig(
            base_output_directory=str(self.temp_dir),
            raw_image_quality=85,
            overlay_image_quality=90,
            frame_range=(10, 50),
            skeleton_color=(255, 0, 0),
            joint_color=(0, 255, 0)
        )
        
        # Convert to dict (simulating JSON serialization)
        config_dict = {
            "base_output_directory": config.base_output_directory,
            "raw_image_quality": config.raw_image_quality,
            "overlay_image_quality": config.overlay_image_quality,
            "frame_range": config.frame_range,
            "skeleton_color": config.skeleton_color,
            "joint_color": config.joint_color
        }
        
        # Serialize to JSON and back
        json_str = json.dumps(config_dict)
        loaded_dict = json.loads(json_str)
        
        # Verify values
        assert loaded_dict["base_output_directory"] == str(self.temp_dir)
        assert loaded_dict["raw_image_quality"] == 85
        assert loaded_dict["overlay_image_quality"] == 90
        assert loaded_dict["frame_range"] == [10, 50]  # JSON converts tuples to lists
        assert loaded_dict["skeleton_color"] == [255, 0, 0]

    def test_end_to_end_workflow_simulation(self):
        """Test end-to-end workflow simulation (without actual video processing)."""
        # Create configuration
        config = FrameExtractionConfig(
            base_output_directory=str(self.temp_dir),
            extract_raw_frames=True,
            extract_overlay_frames=True
        )
        
        # Create manager
        manager = FrameExtractionManager(config)
        
        # Test directory creation
        directories = manager._create_output_directories(
            "test_video", "20250619_140530", self.temp_dir
        )
        
        # Verify directories were created
        assert directories["raw"].exists()
        assert directories["overlay"].exists()
        
        # Test summary generation with mock results
        mock_results = {
            "raw_frames": [Path("frame_00000.jpg"), Path("frame_00001.jpg")],
            "overlay_frames": [Path("frame_00000.jpg"), Path("frame_00001.jpg")],
            "directories": directories
        }
        
        summary = manager.get_extraction_summary(mock_results)
        
        assert summary["total_raw_frames"] == 2
        assert summary["total_overlay_frames"] == 2
        assert summary["directories_created"] == 2 