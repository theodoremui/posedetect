"""
Test suite for enhanced video processing functionality.

This module tests the enhanced video processing features that automatically
create raw frames and overlay frames directories for video inputs, following
the removal of MediaPipe dependencies.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import cv2
import numpy as np

from src.posedetect.cli.main import process_video, validate_arguments
from src.posedetect.models.pose import Pose, Joint, KeyPoint
from src.posedetect.utils.output_manager import OutputManager
from src.posedetect.video.frame_extraction import FrameExtractionConfig, FrameExtractionManager


class TestEnhancedVideoProcessing:
    """Test enhanced video processing functionality."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_video_path(self, temp_dir):
        """Create a mock video file path."""
        video_path = temp_dir / "test_video.mp4"
        video_path.touch()
        return video_path
    
    @pytest.fixture
    def sample_poses(self):
        """Create sample pose data for testing."""
        poses = []
        for frame_num in range(5):
            keypoint = KeyPoint(x=100.0 + frame_num, y=200.0 + frame_num, confidence=0.8)
            joint = Joint(name="nose", keypoint=keypoint, joint_id=0)
            pose = Pose(
                joints=[joint],
                person_id=0,
                frame_number=frame_num,
                timestamp=frame_num * 0.033,  # 30fps
                confidence=0.8
            )
            poses.append(pose)
        return poses
    
    @pytest.fixture
    def mock_args(self, mock_video_path, temp_dir):
        """Create mock command line arguments."""
        args = Mock()
        args.input_path = mock_video_path
        args.output = str(temp_dir / "outputs" / "pose.json")
        args.model_folder = None
        args.net_resolution = "368x368"
        args.model_pose = "COCO"
        args.scale_number = 1
        args.scale_gap = 0.3
        args.confidence_threshold = 0.1
        args.export_csv = False
        args.csv_format = "normalized"
        args.export_all_formats = False
        args.overlay_config = None
        args.frame_range = None
        args.frame_extraction_config = None
        args.overlay_video = None
        args.extract_frames = False
        return args

    def test_mediapipe_removal_from_cli(self):
        """Test that MediaPipe options are no longer available in CLI."""
        from src.posedetect.cli.main import create_argument_parser
        
        parser = create_argument_parser()
        
        # Test that parser doesn't have --detector argument anymore
        with pytest.raises(SystemExit):
            parser.parse_args(["test.mp4", "--detector", "mediapipe"])
    
    def test_mediapipe_import_removal(self):
        """Test that MediaPipe imports have been removed."""
        
        # Test that mediapipe_detector module no longer exists
        with pytest.raises(ImportError):
            from src.posedetect.core.mediapipe_detector import MediaPipePoseDetector
    
    @patch('src.posedetect.core.detector.PoseDetector')
    @patch('src.posedetect.utils.video_processor.VideoProcessor')
    @patch('src.posedetect.utils.output_manager.OutputManager')
    def test_video_processing_uses_only_openpose(self, mock_output_manager, mock_video_processor, mock_detector, mock_args):
        """Test that video processing only uses OpenPose detector."""
        
        # Setup mocks
        mock_detector_instance = Mock()
        mock_detector.return_value = mock_detector_instance
        mock_detector_instance.__enter__ = Mock(return_value=mock_detector_instance)
        mock_detector_instance.__exit__ = Mock(return_value=None)
        mock_detector_instance.detect_poses_in_video.return_value = []
        
        mock_video_proc = Mock()
        mock_video_processor.return_value.__enter__ = Mock(return_value=mock_video_proc)
        mock_video_processor.return_value.__exit__ = Mock(return_value=None)
        mock_video_proc.get_metadata.return_value = {"frame_count": 100, "fps": 30}
        
        mock_output_mgr = Mock()
        mock_output_manager.return_value = mock_output_mgr
        mock_output_mgr.generate_comprehensive_frame_extractions.return_value = {
            'summary': {'total_raw_frames': 100, 'total_overlay_frames': 100, 'output_directories': {}}
        }
        
        # Call process_video
        process_video(mock_args)
        
        # Verify OpenPose detector was used
        mock_detector.assert_called_once_with(
            model_folder=None,
            net_resolution="368x368",
            model_pose="COCO",
            scale_number=1,
            scale_gap=0.3
        )
        
        # Verify no MediaPipe references
        mock_detector_instance.detect_poses_in_video.assert_called_once_with(mock_args.input_path)

    @patch('src.posedetect.core.detector.PoseDetector')
    @patch('src.posedetect.utils.video_processor.VideoProcessor')
    @patch('src.posedetect.utils.output_manager.OutputManager')
    def test_automatic_frame_extraction(self, mock_output_manager, mock_video_processor, mock_detector, mock_args, sample_poses):
        """Test that frame extraction happens automatically for video inputs."""
        
        # Setup mocks
        mock_detector_instance = Mock()
        mock_detector.return_value = mock_detector_instance
        mock_detector_instance.__enter__ = Mock(return_value=mock_detector_instance)
        mock_detector_instance.__exit__ = Mock(return_value=None)
        mock_detector_instance.detect_poses_in_video.return_value = sample_poses
        
        mock_video_proc = Mock()
        mock_video_processor.return_value.__enter__ = Mock(return_value=mock_video_proc)
        mock_video_processor.return_value.__exit__ = Mock(return_value=None)
        mock_video_proc.get_metadata.return_value = {"frame_count": 5, "fps": 30}
        
        mock_output_mgr = Mock()
        mock_output_manager.return_value = mock_output_mgr
        mock_output_mgr.generate_comprehensive_frame_extractions.return_value = {
            'summary': {
                'total_raw_frames': 5, 
                'total_overlay_frames': 5, 
                'output_directories': {
                    'frames': '/path/to/frames',
                    'overlay': '/path/to/overlay'
                }
            }
        }
        
        # Call process_video
        process_video(mock_args)
        
        # Verify comprehensive frame extraction was called
        mock_output_mgr.generate_comprehensive_frame_extractions.assert_called_once()
        
        # Verify poses were added to output manager
        mock_output_mgr.add_poses.assert_called_once_with(sample_poses)

    def test_frame_extraction_config_defaults(self):
        """Test that frame extraction configuration has proper defaults."""
        config = FrameExtractionConfig()
        
        assert config.base_output_directory == "outputs"
        assert config.extract_raw_frames is True
        assert config.extract_overlay_frames is True
        assert config.raw_image_format == "jpg"
        assert config.overlay_image_format == "jpg"
        assert config.directory_name_template == "{type}_{video_name}_{timestamp}"

    def test_frame_extraction_manager_creates_timestamped_directories(self, temp_dir, sample_poses):
        """Test that frame extraction manager creates properly timestamped directories."""
        
        # Create a test video file
        video_path = temp_dir / "test_video.mp4"
        video_path.touch()
        
        # Create frame extraction config with temp directory
        config = FrameExtractionConfig(
            base_output_directory=str(temp_dir),
            frame_skip=5  # Skip most frames for faster testing
        )
        
        manager = FrameExtractionManager(config)
        
        # Mock the video processing parts
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap_instance = Mock()
            mock_cap.return_value = mock_cap_instance
            mock_cap_instance.isOpened.return_value = True
            mock_cap_instance.get.side_effect = lambda prop: {
                cv2.CAP_PROP_FRAME_COUNT: 5,
                cv2.CAP_PROP_FRAME_WIDTH: 640,
                cv2.CAP_PROP_FRAME_HEIGHT: 480
            }.get(prop, 0)
            mock_cap_instance.read.side_effect = [(True, np.zeros((480, 640, 3), dtype=np.uint8))] * 5 + [(False, None)]
            
            with patch('cv2.imwrite') as mock_imwrite:
                mock_imwrite.return_value = True
                
                # Extract frames
                results = manager.extract_all_frame_types(
                    video_path=video_path,
                    poses=sample_poses,
                    base_output_directory=temp_dir
                )
        
        # Verify that results contain expected directory structure
        assert 'summary' in results
        summary = results['summary']
        assert 'output_directories' in summary
        
        # Check that directory names follow the expected pattern
        directories = summary['output_directories']
        for dir_type, dir_path in directories.items():
            assert dir_type in ['frames', 'overlay']
            # Directory should contain video name and timestamp
            assert 'test_video' in str(dir_path)

    def test_validate_arguments_rejects_mediapipe_references(self, temp_dir):
        """Test that argument validation no longer references MediaPipe."""
        from src.posedetect.cli.main import validate_arguments
        
        # Create a mock video file
        video_path = temp_dir / "test.mp4"
        video_path.touch()
        
        # Create mock args without detector field (since it was removed)
        args = Mock()
        args.input = str(video_path)
        args.input_path = video_path
        args.overlay_video = None
        args.overlay_image = None
        args.extract_frames = False
        args.extract_comprehensive_frames = False
        args.confidence_threshold = 0.5
        args.keypoint_radius = 4
        args.connection_thickness = 2
        args.frame_range = None
        
        # Should not raise any errors
        validate_arguments(args)

    @patch('src.posedetect.utils.file_handler.FileHandler.is_video_file')
    @patch('src.posedetect.utils.file_handler.FileHandler.validate_input_file')
    def test_video_specific_frame_extraction_validation(self, mock_validate, mock_is_video, temp_dir):
        """Test that frame extraction options are properly validated for video files."""
        
        # Setup mocks
        video_path = temp_dir / "test.mp4"
        mock_validate.return_value = video_path
        mock_is_video.return_value = True
        
        args = Mock()
        args.input = str(video_path)
        args.overlay_video = None
        args.overlay_image = None
        args.extract_frames = True  # Should be allowed for videos
        args.extract_comprehensive_frames = True  # Should be allowed for videos
        args.confidence_threshold = 0.5
        args.keypoint_radius = 4
        args.connection_thickness = 2
        args.frame_range = None
        args.debug_openpose = False
        
        # Should not raise errors for video files
        validate_arguments(args)

    def test_output_manager_comprehensive_frame_extraction_integration(self, temp_dir, sample_poses):
        """Test integration between OutputManager and comprehensive frame extraction."""
        
        # Create output manager with temp path
        json_path = temp_dir / "poses.json"
        output_manager = OutputManager(json_path)
        output_manager.add_poses(sample_poses)
        
        # Create mock video file
        video_path = temp_dir / "test_video.mp4"
        video_path.touch()
        output_manager.set_input_video_path(video_path)
        
        # Test with mocked video processing
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap_instance = Mock()
            mock_cap.return_value = mock_cap_instance
            mock_cap_instance.isOpened.return_value = True
            mock_cap_instance.get.side_effect = lambda prop: {
                cv2.CAP_PROP_FRAME_COUNT: 5,
                cv2.CAP_PROP_FRAME_WIDTH: 640,
                cv2.CAP_PROP_FRAME_HEIGHT: 480
            }.get(prop, 0)
            mock_cap_instance.read.side_effect = [(True, np.zeros((480, 640, 3), dtype=np.uint8))] * 5 + [(False, None)]
            
            with patch('cv2.imwrite') as mock_imwrite:
                mock_imwrite.return_value = True
                
                # Call comprehensive frame extraction
                results = output_manager.generate_comprehensive_frame_extractions()
        
        # Verify results structure
        assert 'summary' in results
        assert 'total_raw_frames' in results['summary']
        assert 'total_overlay_frames' in results['summary']
        assert 'output_directories' in results['summary']

    def test_error_handling_in_frame_extraction(self, temp_dir, sample_poses, mock_args):
        """Test that frame extraction errors are handled gracefully."""
        
        # Create invalid video path
        invalid_video_path = temp_dir / "nonexistent.mp4"
        mock_args.input_path = invalid_video_path
        
        with patch('src.posedetect.core.detector.PoseDetector') as mock_detector:
            mock_detector_instance = Mock()
            mock_detector.return_value = mock_detector_instance
            mock_detector_instance.__enter__ = Mock(return_value=mock_detector_instance)
            mock_detector_instance.__exit__ = Mock(return_value=None)
            mock_detector_instance.detect_poses_in_video.return_value = sample_poses
            
            with patch('src.posedetect.utils.video_processor.VideoProcessor') as mock_video_processor:
                mock_video_proc = Mock()
                mock_video_processor.return_value.__enter__ = Mock(return_value=mock_video_proc)
                mock_video_processor.return_value.__exit__ = Mock(return_value=None)
                mock_video_proc.get_metadata.return_value = {"frame_count": 5, "fps": 30}
                
                with patch('src.posedetect.utils.output_manager.OutputManager') as mock_output_manager:
                    mock_output_mgr = Mock()
                    mock_output_manager.return_value = mock_output_mgr
                    
                    # Make frame extraction raise an error
                    mock_output_mgr.generate_comprehensive_frame_extractions.side_effect = Exception("Frame extraction failed")
                    
                    # Should not raise exception - should handle gracefully
                    process_video(mock_args)
                    
                    # Verify that other operations still completed
                    mock_output_mgr.save_json.assert_called_once()
                    mock_output_mgr.export_csv_advanced.assert_called_once()


class TestFrameExtractionConfiguration:
    """Test frame extraction configuration and validation."""
    
    def test_frame_extraction_config_validation(self):
        """Test frame extraction configuration validation."""
        
        # Test valid configuration
        config = FrameExtractionConfig(
            raw_image_quality=95,
            overlay_image_quality=90,
            raw_image_format="jpg",
            overlay_image_format="png",
            frame_skip=2
        )
        # Should not raise any exceptions
        
        # Test invalid quality values
        with pytest.raises(ValueError):
            FrameExtractionConfig(raw_image_quality=150)
        
        with pytest.raises(ValueError):
            FrameExtractionConfig(overlay_image_quality=-10)
        
        # Test invalid image formats
        with pytest.raises(ValueError):
            FrameExtractionConfig(raw_image_format="invalid")
        
        # Test invalid frame range
        with pytest.raises(ValueError):
            FrameExtractionConfig(frame_range=(10, 5))  # start > end
        
        # Test invalid frame skip
        with pytest.raises(ValueError):
            FrameExtractionConfig(frame_skip=0)

    def test_frame_extraction_directory_naming(self):
        """Test frame extraction directory naming patterns."""
        config = FrameExtractionConfig()
        
        # Test directory name generation
        dir_name = config.get_directory_name("frames", "test_video", "20250619_140530")
        assert dir_name == "frames_test_video_20250619_140530"
        
        dir_name = config.get_directory_name("overlay", "another_video", "20250619_140531")
        assert dir_name == "overlay_another_video_20250619_140531"

    def test_frame_filename_generation(self):
        """Test frame filename generation."""
        config = FrameExtractionConfig()
        
        # Test frame filename generation
        filename = config.get_frame_filename(0, "jpg")
        assert filename == "frame_00000.jpg"
        
        filename = config.get_frame_filename(123, "png")
        assert filename == "frame_00123.png"
        
        filename = config.get_frame_filename(99999, "jpg")
        assert filename == "frame_99999.jpg"


if __name__ == "__main__":
    pytest.main([__file__]) 