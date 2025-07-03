"""
Tests for enhanced OutputManager functionality.

This module contains tests for the enhanced OutputManager that supports
CSV export, video overlay generation, and multi-format export capabilities.
"""

import pytest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
from typing import List

from src.posedetect.models.pose import Pose, Joint, KeyPoint
from src.posedetect.utils.output_manager import OutputManager
from src.posedetect.exporters.csv_exporter import CSVFormat
from src.posedetect.video.overlay_generator import OverlayConfig


class TestEnhancedOutputManager:
    """Test cases for enhanced OutputManager functionality."""
    
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
        ]
        pose2 = Pose(joints=joints2, person_id=1, confidence=0.72)
        pose2.frame_number = 1
        pose2.timestamp = 0.033
        poses.append(pose2)
        
        return poses
    
    @pytest.fixture
    def output_manager(self, sample_poses) -> OutputManager:
        """Create OutputManager with sample data."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_output.json"
            manager = OutputManager(output_path)
            manager.add_poses(sample_poses)
            yield manager
    
    def test_set_input_video_path(self):
        """Test setting input video path for overlay generation."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.json"
            video_path = Path(temp_dir) / "video.mp4"
            video_path.touch()  # Create empty file
            
            manager = OutputManager(output_path)
            manager.set_input_video_path(video_path)
            
            assert manager._input_video_path == video_path
    
    def test_get_summary_alias(self, output_manager):
        """Test that get_summary is an alias for get_results_summary."""
        summary1 = output_manager.get_summary()
        summary2 = output_manager.get_results_summary()
        
        assert summary1 == summary2
        assert 'total_poses' in summary1
        assert summary1['total_poses'] == 2
    
    def test_export_csv_advanced_normalized(self, output_manager):
        """Test advanced CSV export in normalized format."""
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test_normalized.csv"
            
            result_path = output_manager.export_csv_advanced(
                csv_path=csv_path,
                format_type=CSVFormat.TORONTO_GAIT,
                include_metadata=True
            )
            
            assert result_path.exists()
            assert result_path == csv_path
    
    def test_export_csv_advanced_wide(self, output_manager):
        """Test advanced CSV export in wide format."""
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test_wide.csv"
            
            result_path = output_manager.export_csv_advanced(
                csv_path=csv_path,
                format_type=CSVFormat.TORONTO_GAIT,
                include_metadata=False
            )
            
            assert result_path.exists()
    
    def test_export_csv_advanced_summary(self, output_manager):
        """Test advanced CSV export in summary format."""
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test_summary.csv"
            
            result_path = output_manager.export_csv_advanced(
                csv_path=csv_path,
                format_type=CSVFormat.TORONTO_GAIT
            )
            
            assert result_path.exists()
    
    def test_export_csv_advanced_default_path(self, output_manager):
        """Test CSV export with default path generation."""
        result_path = output_manager.export_csv_advanced()
        
        # Should create CSV file with same base name as JSON output
        expected_path = output_manager.output_path.with_suffix('.csv')
        assert result_path.name.endswith('.csv')
    
    def test_export_csv_advanced_no_poses_raises_error(self):
        """Test that CSV export raises error when no poses available."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "empty.json"
            manager = OutputManager(output_path)
            
            with pytest.raises(ValueError, match="No poses available to export"):
                manager.export_csv_advanced()
    
    def test_export_all_csv_formats(self, output_manager):
        """Test exporting CSV format."""
        with TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "test.csv"
            
            exported_path = output_manager.export_csv_advanced(csv_path)
            
            assert exported_path.exists()
            assert exported_path == csv_path
    
    def test_export_all_csv_formats_default_path(self, output_manager):
        """Test exporting CSV format with default path."""
        exported_path = output_manager.export_csv_advanced()
        
        assert exported_path.exists()
    
    @patch('src.posedetect.video.overlay_generator.VideoOverlayGenerator')
    def test_generate_overlay_video(self, mock_generator_class, output_manager):
        """Test video overlay generation."""
        with TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            output_video_path = Path(temp_dir) / "output.mp4"
            video_path.touch()
            
            # Setup mock
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            
            # Set input video path
            output_manager.set_input_video_path(video_path)
            
            result_path = output_manager.generate_overlay_video(
                output_video_path=output_video_path
            )
            
            assert result_path == output_video_path
            mock_generator.generate_overlay_video.assert_called_once()
    
    def test_generate_overlay_video_no_poses_raises_error(self):
        """Test overlay generation with no poses raises error."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "empty.json"
            manager = OutputManager(output_path)
            
            with pytest.raises(ValueError, match="No poses available for overlay generation"):
                manager.generate_overlay_video()
    
    def test_generate_overlay_video_no_input_path_raises_error(self, output_manager):
        """Test overlay generation without input video path raises error."""
        with pytest.raises(ValueError, match="Input video path not set"):
            output_manager.generate_overlay_video()
    
    def test_generate_overlay_video_input_not_found(self, output_manager):
        """Test overlay generation when input video doesn't exist."""
        output_manager.set_input_video_path("non_existent_video.mp4")
        
        with pytest.raises(FileNotFoundError, match="Input video not found"):
            output_manager.generate_overlay_video()
    
    @patch('src.posedetect.video.overlay_generator.VideoOverlayGenerator')
    def test_generate_overlay_video_with_config(self, mock_generator_class, output_manager):
        """Test video overlay generation with custom configuration."""
        with TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            video_path.touch()
            
            # Setup mock
            mock_generator = Mock()
            mock_generator_class.return_value = mock_generator
            
            # Custom config
            config = OverlayConfig(output_codec='XVID')
            
            output_manager.set_input_video_path(video_path)
            output_manager.generate_overlay_video(config=config)
            
            # Check that generator was created with custom config
            mock_generator_class.assert_called_once_with(config)
    
    def test_export_all_formats_json_only(self, output_manager):
        """Test exporting only JSON format."""
        exported_files = output_manager.export_all_formats(
            input_file="test.mp4",
            include_csv=False,
            include_video=False
        )
        
        assert 'standard' in exported_files['json']
        assert len(exported_files['csv']) == 0
        assert exported_files['video'] is None
    
    def test_export_all_formats_with_csv(self, output_manager):
        """Test exporting JSON and CSV formats."""
        exported_files = output_manager.export_all_formats(
            input_file="test.mp4",
            include_csv=True,
            include_video=False
        )
        
        assert 'standard' in exported_files['json']
        assert len(exported_files['csv']) == 1  # Only Toronto Gait format
        assert 'toronto_gait' in exported_files['csv']
        assert exported_files['video'] is None
    
    def test_export_all_formats_video_without_input_path(self, output_manager):
        """Test that video export is skipped when no input path is set."""
        exported_files = output_manager.export_all_formats(
            input_file="test.mp4",
            include_video=True
        )
        
        # Should complete without error, but video should be None
        assert exported_files['video'] is None
    
    def test_export_all_formats_no_poses_raises_error(self):
        """Test that export_all_formats raises error when no poses available."""
        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "empty.json"
            manager = OutputManager(output_path)
            
            with pytest.raises(ValueError, match="No poses available to export"):
                manager.export_all_formats("test.mp4")
    
    def test_get_export_summary(self, output_manager):
        """Test getting export summary information."""
        summary = output_manager.get_export_summary()
        
        assert 'poses_count' in summary
        assert 'output_path' in summary
        assert 'available_csv_formats' in summary
        assert 'video_overlay_supported' in summary
        assert 'results_summary' in summary
        
        assert summary['poses_count'] == 2
        assert summary['video_overlay_supported'] is False  # No input video set
        assert len(summary['available_csv_formats']) == 3
    
    def test_get_export_summary_with_video(self, output_manager):
        """Test export summary when video path is set."""
        with TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "test.mp4"
            video_path.touch()
            
            output_manager.set_input_video_path(video_path)
            summary = output_manager.get_export_summary()
            
            assert summary['video_overlay_supported'] is True
            assert str(video_path) in summary['input_video_path']
    
    def test_export_all_formats_with_progress_callback(self, output_manager):
        """Test export with progress callback for video generation."""
        with TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "input.mp4"
            video_path.touch()
            
            progress_calls = []
            
            def progress_callback(progress, frame, total):
                progress_calls.append((progress, frame, total))
            
            output_manager.set_input_video_path(video_path)
            
            with patch('src.posedetect.video.overlay_generator.VideoOverlayGenerator') as mock_gen:
                mock_gen.return_value.generate_overlay_video = Mock()
                
                output_manager.export_all_formats(
                    input_file="test.mp4",
                    include_video=True,
                    progress_callback=progress_callback
                )
                
                # Check that callback was passed to video generation
                mock_gen.return_value.generate_overlay_video.assert_called()
                call_args = mock_gen.return_value.generate_overlay_video.call_args
                assert 'progress_callback' in call_args.kwargs
    
    def test_processing_metadata_integration(self, output_manager):
        """Test that processing metadata is properly included in exports."""
        metadata = {
            'model_type': 'BODY_25',
            'confidence_threshold': 0.5,
            'processing_time': 12.34
        }
        
        exported_files = output_manager.export_all_formats(
            input_file="test.mp4",
            processing_metadata=metadata,
            include_csv=False,
            include_video=False
        )
        
        # Check that JSON file contains metadata
        with open(exported_files['json'], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert 'metadata' in data
        assert data['metadata']['processing_info'] == metadata 