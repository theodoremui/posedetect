"""
Tests for utility modules.

This module contains comprehensive tests for file handling, video processing,
and output management utilities.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from src.posedetect.utils.file_handler import FileHandler
from src.posedetect.utils.output_manager import OutputManager
from src.posedetect.models.pose import Pose, Joint, KeyPoint


class TestFileHandler:
    """Test cases for FileHandler class."""
    
    def test_supported_formats(self):
        """Test supported file format definitions."""
        # Image formats
        assert '.jpg' in FileHandler.SUPPORTED_IMAGE_FORMATS
        assert '.png' in FileHandler.SUPPORTED_IMAGE_FORMATS
        assert '.bmp' in FileHandler.SUPPORTED_IMAGE_FORMATS
        
        # Video formats
        assert '.mp4' in FileHandler.SUPPORTED_VIDEO_FORMATS
        assert '.avi' in FileHandler.SUPPORTED_VIDEO_FORMATS
        assert '.mov' in FileHandler.SUPPORTED_VIDEO_FORMATS
    
    def test_is_image_file(self):
        """Test image file detection."""
        assert FileHandler.is_image_file(Path("test.jpg"))
        assert FileHandler.is_image_file(Path("test.PNG"))  # Case insensitive
        assert not FileHandler.is_image_file(Path("test.mp4"))
        assert not FileHandler.is_image_file(Path("test.txt"))
    
    def test_is_video_file(self):
        """Test video file detection."""
        assert FileHandler.is_video_file(Path("test.mp4"))
        assert FileHandler.is_video_file(Path("test.AVI"))  # Case insensitive
        assert not FileHandler.is_video_file(Path("test.jpg"))
        assert not FileHandler.is_video_file(Path("test.txt"))
    
    def test_validate_input_file_not_found(self):
        """Test validation with non-existent file."""
        with pytest.raises(FileNotFoundError):
            FileHandler.validate_input_file("non_existent_file.jpg")
    
    def test_validate_input_file_unsupported_format(self):
        """Test validation with unsupported file format."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                FileHandler.validate_input_file(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_validate_input_file_valid(self):
        """Test validation with valid file."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            result = FileHandler.validate_input_file(temp_path)
            assert result == Path(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_ensure_output_directory(self):
        """Test output directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "subdir" / "output.json"
            result = FileHandler.ensure_output_directory(str(output_path))
            
            assert result == output_path
            assert output_path.parent.exists()
    
    def test_get_file_info(self):
        """Test file information extraction."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = Path(temp_file.name)
        
        try:
            info = FileHandler.get_file_info(temp_path)
            assert info['name'] == temp_path.name
            assert info['size'] > 0
            assert info['extension'] == '.jpg'
            assert info['is_image'] is True
            assert info['is_video'] is False
            assert 'absolute_path' in info
        finally:
            temp_path.unlink()


class TestOutputManager:
    """Test cases for OutputManager class."""
    
    def create_sample_poses(self) -> list:
        """Create sample poses for testing."""
        poses = []
        for i in range(3):
            joints = [
                Joint("nose", KeyPoint(100.0 + i, 50.0, 0.9), 0),
                Joint("left_eye", KeyPoint(90.0 + i, 45.0, 0.8), 1),
            ]
            pose = Pose(joints=joints, person_id=i % 2, frame_number=i, timestamp=i * 0.1)
            poses.append(pose)
        return poses
    
    def test_output_manager_initialization(self):
        """Test OutputManager initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.json"
            manager = OutputManager(output_path)
            assert manager.output_path == output_path
            assert len(manager.results) == 0
    
    def test_add_pose(self):
        """Test adding a single pose."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.json"
            manager = OutputManager(output_path)
            poses = self.create_sample_poses()
            
            manager.add_pose(poses[0])
            assert len(manager.results) == 1
            assert manager.results[0] == poses[0]
    
    def test_add_poses(self):
        """Test adding multiple poses."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.json"
            manager = OutputManager(output_path)
            poses = self.create_sample_poses()
            
            manager.add_poses(poses)
            assert len(manager.results) == 3
    
    def test_clear_results(self):
        """Test clearing results."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.json"
            manager = OutputManager(output_path)
            poses = self.create_sample_poses()
            
            manager.add_poses(poses)
            assert len(manager.results) == 3
            
            manager.clear_results()
            assert len(manager.results) == 0
    
    def test_get_results_summary(self):
        """Test results summary generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.json"
            manager = OutputManager(output_path)
            poses = self.create_sample_poses()
            manager.add_poses(poses)
            
            summary = manager.get_results_summary()
            assert summary['total_poses'] == 3
            assert summary['total_frames'] == 3  # frames 0, 1, 2
            assert summary['people_detected'] == 2  # person_id 0 and 1
            assert summary['frames_with_poses'] == 3
    
    def test_get_results_summary_empty(self):
        """Test results summary with no poses."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.json"
            manager = OutputManager(output_path)
            
            summary = manager.get_results_summary()
            assert summary['total_poses'] == 0
            assert summary['total_frames'] == 0
            assert summary['people_detected'] == 0
            assert summary['frames_with_poses'] == 0
    
    def test_save_and_load_json(self):
        """Test JSON save and load functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.json"
            manager = OutputManager(output_path)
            poses = self.create_sample_poses()
            manager.add_poses(poses)
            
            # Save JSON
            manager.save_json("test_input.mp4", {"test": "metadata"})
            assert output_path.exists()
            
            # Load JSON
            new_manager = OutputManager(output_path)
            loaded_poses = new_manager.load_json()
            
            assert len(loaded_poses) == 3
            assert loaded_poses[0].person_id == poses[0].person_id
            assert loaded_poses[0].frame_number == poses[0].frame_number
    
    def test_create_output_data(self):
        """Test output data structure creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.json"
            manager = OutputManager(output_path)
            poses = self.create_sample_poses()
            manager.add_poses(poses)
            
            metadata = {"model": "COCO", "resolution": "368x368"}
            output_data = manager.create_output_data("input.mp4", metadata)
            
            assert "metadata" in output_data
            assert "summary" in output_data
            assert "poses" in output_data
            assert output_data["metadata"]["input_file"] == "input.mp4"
            assert output_data["metadata"]["processing_info"] == metadata
            assert len(output_data["poses"]) == 3
    
    def test_export_csv(self):
        """Test CSV export functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "output.json"
            manager = OutputManager(output_path)
            poses = self.create_sample_poses()
            manager.add_poses(poses)
            
            csv_path = manager.export_csv()
            assert csv_path.exists()
            assert csv_path.suffix == '.csv'
            
            # Check CSV content
            content = csv_path.read_text()
            lines = content.strip().split('\n')
            assert len(lines) > 1  # Header + data
            assert lines[0] == "frame_number,timestamp,person_id,joint_name,x,y,confidence"
    
    def test_load_json_file_not_found(self):
        """Test loading from non-existent JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "non_existent.json"
            manager = OutputManager(output_path)
            
            with pytest.raises(FileNotFoundError):
                manager.load_json()
    
    def test_load_json_invalid_format(self):
        """Test loading invalid JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "invalid.json"
            output_path.write_text("invalid json content")
            manager = OutputManager(output_path)
            
            with pytest.raises(json.JSONDecodeError):
                manager.load_json()


if __name__ == "__main__":
    pytest.main([__file__]) 