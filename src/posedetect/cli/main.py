"""
Main command-line interface for pose detection.

This module provides the main entry point for the pose detection application
with comprehensive argument parsing and error handling.
"""

import argparse
import sys
import os
import json
from pathlib import Path
from typing import Optional
from datetime import datetime
from loguru import logger

from ..core.detector import PoseDetector
from ..core.visualizer import PoseVisualizer
from ..utils.file_handler import FileHandler
from ..utils.video_processor import VideoProcessor
from ..utils.output_manager import OutputManager
from ..utils.logging_config import setup_logging
from ..exporters.csv_exporter import CSVFormat
from ..exporters.json_exporter import JSONFormat
from ..video.overlay_generator import OverlayConfig
from ..video.frame_extraction import FrameExtractionConfig


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Extract OpenPose joint positions from video or image files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.mp4 --output results/poses.json
  %(prog)s image.jpg --output poses.json --visualize
  %(prog)s video.avi --output data/poses.json --overlay-video results/overlay.mp4
  %(prog)s input.mp4 --net-resolution 656x368 --confidence-threshold 0.5
        """
    )
    
    # Required arguments
    parser.add_argument(
        "input",
        type=str,
        nargs="?",  # Make input optional
        help="Input video or image file path"
    )
    
    # Output arguments
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="outputs/pose.json",
        help="Output JSON file path (default: %(default)s)"
    )
    
    parser.add_argument(
        "--overlay-video",
        type=str,
        help="Create an overlay video with poses drawn (for video inputs only)"
    )
    
    parser.add_argument(
        "--overlay-image",
        type=str,
        help="Create an overlay image with poses drawn (for image inputs only)"
    )
    
    # OpenPose configuration
    parser.add_argument(
        "--model-folder",
        type=str,
        help="OpenPose models folder path (uses OPENPOSEPATH if not specified)"
    )
    
    parser.add_argument(
        "--net-resolution",
        type=str,
        default="368x368",
        help="Network input resolution (default: %(default)s)"
    )
    
    parser.add_argument(
        "--model-pose",
        type=str,
        choices=["COCO", "MPI", "MPI_4_layers"],
        default="COCO",
        help="Pose model to use (default: %(default)s)"
    )
    
    parser.add_argument(
        "--scale-number",
        type=int,
        default=1,
        help="Number of scales to average (default: %(default)d)"
    )
    
    parser.add_argument(
        "--scale-gap",
        type=float,
        default=0.3,
        help="Scale gap between scales (default: %(default)f)"
    )
    
    # Visualization options
    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=0.1,
        help="Minimum confidence threshold for keypoints (default: %(default)f)"
    )
    
    parser.add_argument(
        "--show-confidence",
        action="store_true",
        help="Show confidence scores in visualizations"
    )
    
    parser.add_argument(
        "--keypoint-radius",
        type=int,
        default=4,
        help="Radius of keypoint circles in visualization (default: %(default)d)"
    )
    
    parser.add_argument(
        "--connection-thickness",
        type=int,
        default=2,
        help="Thickness of connection lines in visualization (default: %(default)d)"
    )
    
    # Logging and debugging
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: %(default)s)"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Log to file (in addition to console)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--debug-openpose",
        action="store_true",
        help="Run OpenPose diagnostics and exit"
    )
    

    
    # Export options
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export CSV data (Toronto Gait format)"
    )
    
    parser.add_argument(
        "--export-json",
        action="store_true",
        help="Export JSON data (Toronto Gait format)"
    )
    
    parser.add_argument(
        "--toronto-gait-format",
        action="store_true",
        help="Export in Toronto Older Adults Gait Archive format (both CSV and JSON)"
    )
    
    parser.add_argument(
        "--export-all-formats",
        action="store_true",
        help="Export in all available formats (JSON, CSV, video overlay if applicable)"
    )
    
    parser.add_argument(
        "--overlay-config",
        type=str,
        help="JSON file with overlay generation configuration"
    )
    
    parser.add_argument(
        "--extract-frames",
        action="store_true",
        help="Extract individual frame images with pose overlays (for video inputs only)"
    )
    
    parser.add_argument(
        "--frame-range",
        type=str,
        help="Frame range to extract (format: start:end, e.g., 10:50)"
    )
    
    parser.add_argument(
        "--frames-directory",
        type=str,
        help="Directory to save extracted frame images (default: {output_name}_frames)"
    )
    
    parser.add_argument(
        "--extract-comprehensive-frames",
        action="store_true",
        help="Extract both raw frames and overlay frames to separate directories (for video inputs only)"
    )
    
    parser.add_argument(
        "--frame-extraction-config",
        type=str,
        help="JSON file with frame extraction configuration"
    )
    
    return parser


def load_overlay_config(config_path: Optional[str]) -> Optional[OverlayConfig]:
    """
    Load overlay configuration from JSON file.
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        OverlayConfig object or None if no config provided
        
    Raises:
        ValueError: If config file is invalid
    """
    if not config_path:
        return None
    
    config_file = Path(config_path)
    if not config_file.exists():
        raise ValueError(f"Overlay config file not found: {config_path}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Convert dict to OverlayConfig (simple approach)
        # In a real implementation, you might want more sophisticated conversion
        return OverlayConfig(**config_data)
        
    except (json.JSONDecodeError, TypeError) as e:
        raise ValueError(f"Invalid overlay config file: {e}")


def load_frame_extraction_config(config_path: Optional[str]) -> Optional[FrameExtractionConfig]:
    """
    Load frame extraction configuration from JSON file.
    
    Args:
        config_path: Path to JSON configuration file
        
    Returns:
        FrameExtractionConfig object or None if no config provided
        
    Raises:
        ValueError: If config file is invalid
    """
    if not config_path:
        return None
    
    config_file = Path(config_path)
    if not config_file.exists():
        raise ValueError(f"Frame extraction config file not found: {config_path}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        # Convert dict to FrameExtractionConfig
        return FrameExtractionConfig(**config_data)
        
    except (json.JSONDecodeError, TypeError) as e:
        raise ValueError(f"Invalid frame extraction config file: {e}")


def should_export_toronto_gait(args: argparse.Namespace) -> bool:
    """
    Check if Toronto Gait format should be exported based on arguments.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        True if Toronto Gait format should be exported
    """
    return (getattr(args, 'toronto_gait_format', False) or
            getattr(args, 'export_csv', False) or
            getattr(args, 'export_json', False) or
            getattr(args, 'export_all_formats', False))


def parse_frame_range(frame_range_str: str) -> Optional[tuple]:
    """
    Parse frame range string into tuple.
    
    Args:
        frame_range_str: Frame range string (e.g., "10:50", "0:100")
        
    Returns:
        Tuple (start_frame, end_frame) or None if invalid
        
    Examples:
        "10:50" -> (10, 50)
        "0:100" -> (0, 100)
    """
    if not frame_range_str:
        return None
    
    try:
        if ':' not in frame_range_str:
            raise ValueError("Frame range must contain ':' separator")
        
        start_str, end_str = frame_range_str.split(':', 1)
        start_frame = int(start_str.strip())
        end_frame = int(end_str.strip())
        
        if start_frame < 0 or end_frame < 0:
            raise ValueError("Frame numbers must be non-negative")
        
        if start_frame >= end_frame:
            raise ValueError("Start frame must be less than end frame")
        
        return (start_frame, end_frame)
        
    except ValueError as e:
        raise ValueError(f"Invalid frame range '{frame_range_str}': {e}")


def generate_timestamped_output_path(base_output_path: str, extension: str = None) -> Path:
    """
    Generate output path with timestamp appended.
    
    Args:
        base_output_path: Base output path (may include extension)
        extension: Optional extension to override (e.g., ".csv", ".mp4")
        
    Returns:
        Path with timestamp appended before extension
        
    Examples:
        "outputs/pose.json" -> "outputs/pose_20250619_140530.json"
        "outputs/pose", ".csv" -> "outputs/pose_20250619_140530.csv"
    """
    base_path = Path(base_output_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if extension:
        # Use provided extension
        stem = base_path.stem
        output_path = base_path.parent / f"{stem}_{timestamp}{extension}"
    else:
        # Use existing extension
        stem = base_path.stem
        suffix = base_path.suffix
        output_path = base_path.parent / f"{stem}_{timestamp}{suffix}"
    
    return output_path


def validate_arguments(args: argparse.Namespace) -> None:
    """
    Validate command-line arguments.
    
    Args:
        args: Parsed arguments
        
    Raises:
        ValueError: If arguments are invalid
    """
    # Skip validation if in debug mode
    if getattr(args, 'debug_openpose', False):
        return
        
    # Validate input file is provided
    if not args.input:
        raise ValueError("Input file is required (unless using --debug-openpose)")
    
    # Validate input file
    try:
        input_path = FileHandler.validate_input_file(args.input)
        args.input_path = input_path
    except (FileNotFoundError, ValueError) as e:
        raise ValueError(f"Input file error: {e}")
    
    # Validate overlay options based on input type
    if FileHandler.is_image_file(input_path):
        if args.overlay_video:
            raise ValueError("--overlay-video can only be used with video inputs")
        if args.extract_frames:
            raise ValueError("--extract-frames can only be used with video inputs")
        if getattr(args, 'extract_comprehensive_frames', False):
            raise ValueError("--extract-comprehensive-frames can only be used with video inputs")
    elif FileHandler.is_video_file(input_path):
        if args.overlay_image:
            raise ValueError("--overlay-image can only be used with image inputs")
    
    # Validate confidence threshold
    if not 0.0 <= args.confidence_threshold <= 1.0:
        raise ValueError("Confidence threshold must be between 0.0 and 1.0")
    
    # Validate visualization parameters
    if args.keypoint_radius < 1:
        raise ValueError("Keypoint radius must be at least 1")
    
    if args.connection_thickness < 1:
        raise ValueError("Connection thickness must be at least 1")
    
    # Validate frame range if provided
    if hasattr(args, 'frame_range') and args.frame_range:
        try:
            parse_frame_range(args.frame_range)
        except ValueError as e:
            raise ValueError(f"Frame range validation failed: {e}")


def process_image(args: argparse.Namespace) -> None:
    """
    Process a single image file.
    
    Args:
        args: Parsed command-line arguments
    """
    logger.info(f"Processing image: {args.input_path}")
    
    # Load image
    image = VideoProcessor.load_image(args.input_path)
    logger.info(f"Image loaded: {image.shape[1]}x{image.shape[0]} pixels")
    
    # Initialize OpenPose detector
    detector = PoseDetector(
        model_folder=args.model_folder,
        net_resolution=args.net_resolution,
        model_pose=args.model_pose,
        scale_number=args.scale_number,
        scale_gap=args.scale_gap
    )
    
    # Detect poses
    with detector:
        poses = detector.detect_poses_in_image(image)
        logger.info(f"Detected {len(poses)} poses in image using OpenPose")
    
    # Filter poses to remove any invalid detections
    from ..utils.pose_filter import filter_poses_by_validity, get_filtering_summary
    
    original_poses = poses.copy()  # Keep reference for summary
    filtered_poses = filter_poses_by_validity(
        poses, 
        confidence_threshold=args.confidence_threshold,
        min_valid_joints=1  # Require at least 1 valid joint
    )
    
    # Log filtering summary for images
    if len(original_poses) != len(filtered_poses):
        filtering_summary = get_filtering_summary(original_poses, filtered_poses)
        logger.info(f"Image pose filtering: {filtering_summary['filtered_poses']} valid poses from {filtering_summary['original_poses']} detected")
    
    # Generate timestamped output paths
    base_output_path = FileHandler.ensure_output_directory(args.output)
    json_output_path = generate_timestamped_output_path(str(base_output_path))
    csv_output_path = generate_timestamped_output_path(str(base_output_path), ".csv")
    
    output_manager = OutputManager(json_output_path)
    output_manager.add_poses(filtered_poses)  # Use filtered poses
    
    processing_metadata = {
        'input_type': 'image',
        'image_resolution': f"{image.shape[1]}x{image.shape[0]}",
        'model_pose': args.model_pose,
        'net_resolution': args.net_resolution,
        'confidence_threshold': args.confidence_threshold
    }
    
    # Load overlay configuration if provided
    overlay_config = load_overlay_config(args.overlay_config)
    
    # Export in all formats if requested
    if args.export_all_formats:
        exported_files = output_manager.export_all_formats(
            input_file=str(args.input_path),
            processing_metadata=processing_metadata,
            include_csv=True,
            include_json=True,
            include_video=False,  # Images don't generate overlay videos
            overlay_config=overlay_config
        )
        logger.info(f"Exported to multiple formats: {list(exported_files.keys())}")
    else:
        # Handle export requests - since only Toronto Gait format exists, just ensure files are exported
        if should_export_toronto_gait(args):
            logger.info("Exporting in Toronto Older Adults Gait Archive format")
        
        # Always export JSON and CSV by default (Toronto Gait format)
        output_manager.save_json(str(args.input_path), processing_metadata)
        output_manager.export_csv_advanced(csv_path=csv_output_path, format_type=CSVFormat.TORONTO_GAIT)
    
    # Create overlay image if requested
    if args.overlay_image:
        visualizer = PoseVisualizer(
            keypoint_radius=args.keypoint_radius,
            connection_thickness=args.connection_thickness,
            confidence_threshold=args.confidence_threshold
        )
        visualizer.save_pose_image(
            image, poses, args.overlay_image, args.show_confidence
        )


def process_video(args: argparse.Namespace) -> None:
    """
    Process a video file.
    
    Args:
        args: Parsed command-line arguments
    """
    logger.info(f"Processing video: {args.input_path}")
    
    # Initialize OpenPose detector
    detector = PoseDetector(
        model_folder=args.model_folder,
        net_resolution=args.net_resolution,
        model_pose=args.model_pose,
        scale_number=args.scale_number,
        scale_gap=args.scale_gap
    )
    
    # Process video
    with detector:
        poses = detector.detect_poses_in_video(args.input_path)
        logger.info(f"Detected {len(poses)} total poses in video using OpenPose")
    
    # Filter poses to remove frames with no valid pose detections
    from ..utils.pose_filter import filter_poses_by_validity, get_filtering_summary
    
    original_poses = poses.copy()  # Keep reference for summary
    filtered_poses = filter_poses_by_validity(
        poses, 
        confidence_threshold=args.confidence_threshold,
        min_valid_joints=1  # Require at least 1 valid joint
    )
    
    # Log filtering summary
    filtering_summary = get_filtering_summary(original_poses, filtered_poses)
    logger.info(f"Pose filtering completed:")
    logger.info(f"  Retained {filtering_summary['filtered_poses']} poses from {filtering_summary['original_poses']} total")
    logger.info(f"  Retained {filtering_summary['filtered_frames']} frames from {filtering_summary['original_frames']} total")
    logger.info(f"  Frame retention rate: {filtering_summary['frame_retention_rate']:.1f}%")
    
    # Get video metadata for processing info
    with VideoProcessor(args.input_path) as video_proc:
        metadata = video_proc.get_metadata()
    
    # Generate timestamped output paths
    base_output_path = FileHandler.ensure_output_directory(args.output)
    json_output_path = generate_timestamped_output_path(str(base_output_path))
    csv_output_path = generate_timestamped_output_path(str(base_output_path), ".csv")
    
    output_manager = OutputManager(json_output_path)
    output_manager.add_poses(filtered_poses)  # Use filtered poses
    output_manager.set_input_video_path(args.input_path)  # Set for video overlay generation
    
    processing_metadata = {
        'input_type': 'video',
        'video_metadata': metadata,
        'model_pose': args.model_pose,
        'net_resolution': args.net_resolution,
        'confidence_threshold': args.confidence_threshold
    }
    
    # Load overlay configuration if provided
    overlay_config = load_overlay_config(args.overlay_config)
    
    # Parse frame range if specified for all operations
    frame_range = None
    if hasattr(args, 'frame_range') and args.frame_range:
        frame_range = parse_frame_range(args.frame_range)
    
    # Load frame extraction configuration if provided
    frame_config = None
    if hasattr(args, 'frame_extraction_config') and args.frame_extraction_config:
        frame_config = load_frame_extraction_config(args.frame_extraction_config)
    
    # Handle export requests - since only Toronto Gait format exists, just ensure files are exported
    if should_export_toronto_gait(args):
        logger.info("Exporting in Toronto Older Adults Gait Archive format")
    
    # Always export JSON and CSV by default (Toronto Gait format)
    output_manager.save_json(str(args.input_path), processing_metadata)
    output_manager.export_csv_advanced(csv_path=csv_output_path, format_type=CSVFormat.TORONTO_GAIT)
    
    # ALWAYS extract both raw frames and overlay frames for video inputs
    logger.info("Extracting raw frames and overlay frames (automatic for all video inputs)...")
    
    def comprehensive_progress_callback(progress: float, frame: int, total: int, phase: str = "frames"):
        logger.info(f"{phase.title()} extraction progress: {progress:.1%} ({frame}/{total})")
    
    try:
        comprehensive_results = output_manager.generate_comprehensive_frame_extractions(
            frame_config=frame_config,
            progress_callback=comprehensive_progress_callback
        )
        
        summary = comprehensive_results.get('summary', {})
        logger.info(f"Frame extraction complete:")
        logger.info(f"  Raw frames: {summary.get('total_raw_frames', 0)}")
        logger.info(f"  Overlay frames: {summary.get('total_overlay_frames', 0)}")
        
        for extraction_type, directory_path in summary.get('output_directories', {}).items():
            logger.info(f"  {extraction_type.title()} directory: {directory_path}")
    
    except Exception as e:
        logger.warning(f"Frame extraction failed (continuing with other outputs): {e}")
    
    # Export in all formats if requested
    if args.export_all_formats:
        # Define progress callback for video overlay
        def progress_callback(progress: float, frame: int, total: int):
            logger.info(f"Video overlay progress: {progress:.1%} ({frame}/{total})")
        
        exported_files = output_manager.export_all_formats(
            input_file=str(args.input_path),
            processing_metadata=processing_metadata,
            include_csv=True,
            include_json=True,
            include_video=True,  # Enable video overlay for videos
            include_frames=getattr(args, 'extract_frames', False),
            include_comprehensive_frames=False,  # Already done above
            overlay_config=overlay_config,
            frame_config=frame_config,
            frame_range=frame_range,
            progress_callback=progress_callback
        )
        logger.info(f"Exported to multiple formats: {list(exported_files.keys())}")
    
    # Create overlay video if requested using new system
    if args.overlay_video:
        logger.info(f"Creating overlay video: {args.overlay_video}")
        
        def progress_callback(progress: float, frame: int, total: int):
            logger.info(f"Video overlay progress: {progress:.1%} ({frame}/{total})")
        
        # Generate timestamped overlay video path
        overlay_video_path = generate_timestamped_output_path(args.overlay_video, ".mp4")
        
        overlay_path = output_manager.generate_overlay_video(
            output_video_path=overlay_video_path,
            config=overlay_config,
            progress_callback=progress_callback
        )
        logger.info(f"Overlay video saved: {overlay_path}")
    
    # Extract additional individual frame images if specifically requested
    if getattr(args, 'extract_frames', False):
        logger.info("Extracting additional individual frame overlay images...")
        
        # Determine output directory for frames
        frames_directory = None
        if hasattr(args, 'frames_directory') and args.frames_directory:
            frames_directory = Path(args.frames_directory)
        
        def frame_progress_callback(progress: float, frame: int, total: int):
            logger.info(f"Additional frame extraction progress: {progress:.1%} ({frame}/{total})")
        
        frame_files = output_manager.generate_frame_overlays(
            output_frames_directory=frames_directory,
            config=overlay_config,
            frame_range=frame_range,
            progress_callback=frame_progress_callback
        )
        logger.info(f"Extracted {len(frame_files)} additional frame overlay images")


def main() -> int:
    """
    Main entry point for the pose detection application.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_argument_parser()
    
    try:
        args = parser.parse_args()
        
        # Setup logging
        log_file = Path(args.log_file) if args.log_file else None
        setup_logging(args.log_level, log_file, args.verbose)
        
        # Handle debug mode
        if args.debug_openpose:
            return run_openpose_diagnostics()
        
        logger.info("Starting pose detection application")
        logger.info(f"Input file: {args.input}")
        logger.info(f"Output file: {args.output}")
        
        # Validate arguments
        validate_arguments(args)
        
        # Process based on input type
        if FileHandler.is_image_file(args.input_path):
            process_image(args)
        elif FileHandler.is_video_file(args.input_path):
            process_video(args)
        else:
            raise ValueError("Input file type not supported")
        
        logger.info("Pose detection completed successfully")
        return 0
        
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        return 1
    except EnvironmentError as e:
        # OpenPose-related environment errors
        logger.error(f"Environment Error: {e}")
        logger.error("This appears to be an OpenPose configuration issue.")
        logger.error("Try running with --debug-openpose to diagnose the problem:")
        logger.error(f"  python {sys.argv[0]} --debug-openpose")
        return 2
    except Exception as e:
        logger.error(f"Error: {e}")
        if hasattr(args, 'log_level') and args.log_level == "DEBUG":
            logger.exception("Full traceback:")
        return 1


def run_openpose_diagnostics() -> int:
    """
    Run OpenPose diagnostics to help troubleshoot installation issues.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger.info("Running OpenPose diagnostics...")
    
    # Import and run the diagnostic tool
    try:
        import os
        import sys
        from pathlib import Path
        
        # Add tools directory to path
        tools_dir = Path(__file__).parent.parent.parent.parent / "tools"
        if tools_dir.exists():
            sys.path.insert(0, str(tools_dir))
            
            # Import and run diagnostic
            from diagnose_openpose import main as diagnose_main
            return diagnose_main()
        else:
            # Inline diagnostic if tools directory not found
            return run_inline_diagnostics()
            
    except ImportError as e:
        logger.error(f"Could not import diagnostic tools: {e}")
        return run_inline_diagnostics()


def run_inline_diagnostics() -> int:
    """
    Run basic inline OpenPose diagnostics.
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger.info("Running basic OpenPose diagnostics...")
    
    # Check OPENPOSEPATH
    openpose_path = os.environ.get('OPENPOSEPATH')
    if not openpose_path:
        logger.error("❌ OPENPOSEPATH environment variable is not set!")
        logger.error("Please set OPENPOSEPATH to your OpenPose installation directory")
        return 1
    
    logger.info(f"✅ OPENPOSEPATH is set: {openpose_path}")
    
    # Check if directory exists
    if not os.path.exists(openpose_path):
        logger.error(f"❌ OPENPOSEPATH directory does not exist: {openpose_path}")
        return 1
    
    logger.info("✅ OPENPOSEPATH directory exists")
    
    # Check for python directory
    python_dir = os.path.join(openpose_path, 'python')
    if os.path.exists(python_dir):
        logger.info("✅ Found python/ directory")
        
        # List contents
        try:
            contents = os.listdir(python_dir)
            logger.info(f"Python directory contents: {', '.join(contents)}")
        except PermissionError:
            logger.warning("⚠️  Permission denied to list python directory contents")
    else:
        logger.error("❌ Python directory not found")
    
    # Try to test OpenPose import
    try:
        detector = PoseDetector()
        detector.initialize()
        logger.info("✅ OpenPose initialization successful!")
        return 0
    except Exception as e:
        logger.error(f"❌ OpenPose initialization failed: {e}")
        logger.error("This indicates OpenPose Python bindings are not properly installed.")
        logger.error("Please check the OpenPose installation documentation.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 