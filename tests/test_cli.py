"""
Tests for command-line interface.

This module contains tests for the CLI argument parsing and validation
functionality.
"""

import pytest
import tempfile
import argparse
from pathlib import Path
from unittest.mock import Mock, patch

from src.posedetect.cli.main import (
    create_argument_parser,
    validate_arguments,
    main
)


class TestArgumentParser:
    """Test cases for argument parser creation and parsing."""
    
    def test_create_argument_parser(self):
        """Test argument parser creation."""
        parser = create_argument_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert "Extract OpenPose joint positions" in parser.description
    
    def test_required_input_argument(self):
        """Test required input argument."""
        parser = create_argument_parser()
        
        # Should fail without input
        with pytest.raises(SystemExit):
            parser.parse_args([])
        
        # Should succeed with input
        args = parser.parse_args(["test.mp4"])
        assert args.input == "test.mp4"
    
    def test_default_output_argument(self):
        """Test default output argument."""
        parser = create_argument_parser()
        args = parser.parse_args(["test.mp4"])
        assert args.output == "outputs/pose.json"
    
    def test_custom_output_argument(self):
        """Test custom output argument."""
        parser = create_argument_parser()
        args = parser.parse_args(["test.mp4", "--output", "custom.json"])
        assert args.output == "custom.json"
        
        # Test short form
        args = parser.parse_args(["test.mp4", "-o", "short.json"])
        assert args.output == "short.json"
    
    def test_openpose_configuration_arguments(self):
        """Test OpenPose configuration arguments."""
        parser = create_argument_parser()
        args = parser.parse_args([
            "test.mp4",
            "--net-resolution", "656x368",
            "--model-pose", "MPI",
            "--scale-number", "2",
            "--scale-gap", "0.25"
        ])
        
        assert args.net_resolution == "656x368"
        assert args.model_pose == "MPI"
        assert args.scale_number == 2
        assert args.scale_gap == 0.25
    
    def test_visualization_arguments(self):
        """Test visualization configuration arguments."""
        parser = create_argument_parser()
        args = parser.parse_args([
            "test.mp4",
            "--confidence-threshold", "0.5",
            "--show-confidence",
            "--keypoint-radius", "6",
            "--connection-thickness", "3"
        ])
        
        assert args.confidence_threshold == 0.5
        assert args.show_confidence is True
        assert args.keypoint_radius == 6
        assert args.connection_thickness == 3
    
    def test_logging_arguments(self):
        """Test logging configuration arguments."""
        parser = create_argument_parser()
        args = parser.parse_args([
            "test.mp4",
            "--log-level", "DEBUG",
            "--log-file", "app.log",
            "--verbose"
        ])
        
        assert args.log_level == "DEBUG"
        assert args.log_file == "app.log"
        assert args.verbose is True
    
    def test_overlay_arguments(self):
        """Test overlay output arguments."""
        parser = create_argument_parser()
        args = parser.parse_args([
            "test.mp4",
            "--overlay-video", "overlay.mp4",
            "--overlay-image", "overlay.jpg"
        ])
        
        assert args.overlay_video == "overlay.mp4"
        assert args.overlay_image == "overlay.jpg"
    
    def test_export_arguments(self):
        """Test export options."""
        parser = create_argument_parser()
        args = parser.parse_args(["test.mp4", "--export-csv"])
        assert args.export_csv is True
    
    def test_model_pose_choices(self):
        """Test model pose choice validation."""
        parser = create_argument_parser()
        
        # Valid choice
        args = parser.parse_args(["test.mp4", "--model-pose", "COCO"])
        assert args.model_pose == "COCO"
        
        # Invalid choice should raise SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args(["test.mp4", "--model-pose", "INVALID"])


class TestArgumentValidation:
    """Test cases for argument validation."""
    
    def create_temp_image_file(self) -> Path:
        """Create a temporary image file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file.write(b"fake image content")
            return Path(temp_file.name)
    
    def create_temp_video_file(self) -> Path:
        """Create a temporary video file for testing."""
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_file.write(b"fake video content")
            return Path(temp_file.name)
    
    def test_validate_existing_image_file(self):
        """Test validation with existing image file."""
        temp_image = self.create_temp_image_file()
        try:
            args = argparse.Namespace(
                input=str(temp_image),
                confidence_threshold=0.5,
                keypoint_radius=4,
                connection_thickness=2,
                overlay_video=None,
                overlay_image=None
            )
            
            validate_arguments(args)
            assert hasattr(args, 'input_path')
            assert args.input_path == temp_image
        finally:
            temp_image.unlink()
    
    def test_validate_existing_video_file(self):
        """Test validation with existing video file."""
        temp_video = self.create_temp_video_file()
        try:
            args = argparse.Namespace(
                input=str(temp_video),
                confidence_threshold=0.5,
                keypoint_radius=4,
                connection_thickness=2,
                overlay_video=None,
                overlay_image=None
            )
            
            validate_arguments(args)
            assert hasattr(args, 'input_path')
            assert args.input_path == temp_video
        finally:
            temp_video.unlink()
    
    def test_validate_non_existent_file(self):
        """Test validation with non-existent file."""
        args = argparse.Namespace(
            input="non_existent_file.jpg",
            confidence_threshold=0.5,
            keypoint_radius=4,
            connection_thickness=2,
            overlay_video=None,
            overlay_image=None
        )
        
        with pytest.raises(ValueError, match="Input file error"):
            validate_arguments(args)
    
    def test_validate_confidence_threshold_bounds(self):
        """Test confidence threshold validation."""
        temp_image = self.create_temp_image_file()
        try:
            # Valid threshold
            args = argparse.Namespace(
                input=str(temp_image),
                confidence_threshold=0.5,
                keypoint_radius=4,
                connection_thickness=2,
                overlay_video=None,
                overlay_image=None
            )
            validate_arguments(args)  # Should not raise
            
            # Invalid threshold (too low)
            args.confidence_threshold = -0.1
            with pytest.raises(ValueError, match="Confidence threshold must be between"):
                validate_arguments(args)
            
            # Invalid threshold (too high)
            args.confidence_threshold = 1.1
            with pytest.raises(ValueError, match="Confidence threshold must be between"):
                validate_arguments(args)
        finally:
            temp_image.unlink()
    
    def test_validate_visualization_parameters(self):
        """Test visualization parameter validation."""
        temp_image = self.create_temp_image_file()
        try:
            args = argparse.Namespace(
                input=str(temp_image),
                confidence_threshold=0.5,
                keypoint_radius=0,  # Invalid
                connection_thickness=2,
                overlay_video=None,
                overlay_image=None
            )
            
            with pytest.raises(ValueError, match="Keypoint radius must be at least 1"):
                validate_arguments(args)
            
            args.keypoint_radius = 4
            args.connection_thickness = 0  # Invalid
            
            with pytest.raises(ValueError, match="Connection thickness must be at least 1"):
                validate_arguments(args)
        finally:
            temp_image.unlink()
    
    def test_validate_overlay_options_for_image(self):
        """Test overlay option validation for image inputs."""
        temp_image = self.create_temp_image_file()
        try:
            args = argparse.Namespace(
                input=str(temp_image),
                confidence_threshold=0.5,
                keypoint_radius=4,
                connection_thickness=2,
                overlay_video="output.mp4",  # Invalid for image
                overlay_image=None
            )
            
            with pytest.raises(ValueError, match="--overlay-video can only be used with video inputs"):
                validate_arguments(args)
        finally:
            temp_image.unlink()
    
    def test_validate_overlay_options_for_video(self):
        """Test overlay option validation for video inputs."""
        temp_video = self.create_temp_video_file()
        try:
            args = argparse.Namespace(
                input=str(temp_video),
                confidence_threshold=0.5,
                keypoint_radius=4,
                connection_thickness=2,
                overlay_video=None,
                overlay_image="output.jpg"  # Invalid for video
            )
            
            with pytest.raises(ValueError, match="--overlay-image can only be used with image inputs"):
                validate_arguments(args)
        finally:
            temp_video.unlink()


class TestMainFunction:
    """Test cases for the main function."""
    
    @patch('src.posedetect.cli.main.setup_logging')
    @patch('src.posedetect.cli.main.process_image')
    @patch('src.posedetect.cli.main.FileHandler.validate_input_file')
    @patch('src.posedetect.cli.main.FileHandler.is_image_file')
    def test_main_with_image_input(self, mock_is_image, mock_validate, mock_process, mock_logging):
        """Test main function with image input."""
        # Setup mocks
        mock_validate.return_value = Path("test.jpg")
        mock_is_image.return_value = True
        
        with patch('sys.argv', ['video2pose', 'test.jpg']):
            result = main()
        
        assert result == 0
        mock_process.assert_called_once()
        mock_logging.assert_called_once()
    
    @patch('src.posedetect.cli.main.setup_logging')
    @patch('src.posedetect.cli.main.process_video')
    @patch('src.posedetect.cli.main.FileHandler.validate_input_file')
    @patch('src.posedetect.cli.main.FileHandler.is_image_file')
    @patch('src.posedetect.cli.main.FileHandler.is_video_file')
    def test_main_with_video_input(self, mock_is_video, mock_is_image, mock_validate, mock_process, mock_logging):
        """Test main function with video input."""
        # Setup mocks
        mock_validate.return_value = Path("test.mp4")
        mock_is_image.return_value = False
        mock_is_video.return_value = True
        
        with patch('sys.argv', ['video2pose', 'test.mp4']):
            result = main()
        
        assert result == 0
        mock_process.assert_called_once()
        mock_logging.assert_called_once()
    
    @patch('src.posedetect.cli.main.setup_logging')
    @patch('src.posedetect.cli.main.FileHandler.validate_input_file')
    def test_main_with_validation_error(self, mock_validate, mock_logging):
        """Test main function with validation error."""
        mock_validate.side_effect = FileNotFoundError("File not found")
        
        with patch('sys.argv', ['video2pose', 'non_existent.jpg']):
            result = main()
        
        assert result == 1  # Error exit code
    
    def test_main_with_keyboard_interrupt(self):
        """Test main function with keyboard interrupt."""
        with patch('src.posedetect.cli.main.validate_arguments', side_effect=KeyboardInterrupt):
            with patch('sys.argv', ['video2pose', 'test.jpg']):
                result = main()
        
        assert result == 1  # Error exit code


if __name__ == "__main__":
    pytest.main([__file__]) 