#!/usr/bin/env python3
"""
Comprehensive Frame Extraction Example

This script demonstrates the comprehensive frame extraction capabilities,
including both raw frame extraction and overlay frame extraction with 
separate organized directories.

Features demonstrated:
- Raw frame extraction (unprocessed video frames)
- Overlay frame extraction (frames with pose annotations)
- Configurable extraction settings
- Progress tracking and logging
- Output directory organization
"""

import sys
import json
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from posedetect.video.frame_extraction import (
    FrameExtractionConfig,
    FrameExtractionManager
)
from posedetect.utils.output_manager import OutputManager
from posedetect.models.pose import Pose, Joint, KeyPoint


def create_sample_frame_config() -> FrameExtractionConfig:
    """
    Create a sample frame extraction configuration.
    
    Returns:
        Configured FrameExtractionConfig instance
    """
    return FrameExtractionConfig(
        # Output configuration
        base_output_directory="outputs",
        directory_name_template="{type}_{video_name}_{timestamp}",
        frame_filename_template="frame_{:05d}.{extension}",
        
        # Raw frame settings
        extract_raw_frames=True,
        raw_image_format="jpg",
        raw_image_quality=95,
        raw_resize_factor=None,  # No resizing
        
        # Overlay frame settings
        extract_overlay_frames=True,
        overlay_image_format="jpg",
        overlay_image_quality=95,
        overlay_resize_factor=None,  # No resizing
        
        # Pose visualization settings
        skeleton_color=(0, 255, 0),      # Green skeleton
        joint_color=(255, 0, 0),         # Red joints
        confidence_threshold=0.1,        # Low threshold to show more poses
        line_thickness=2,
        joint_radius=4,
        show_confidence=True,
        show_person_id=True,
        font_scale=0.5,
        font_color=(255, 255, 255),      # White text
        
        # Processing settings
        frame_range=None,                # Extract all frames
        frame_skip=1,                    # Process every frame
        
        # Progress and logging
        enable_progress_callback=True,
        log_extraction_details=True
    )


def save_config_example(config: FrameExtractionConfig, output_path: str) -> None:
    """
    Save configuration to JSON file for reuse.
    
    Args:
        config: Configuration to save
        output_path: Path to save configuration file
    """
    # Convert config to dictionary (simplified for demonstration)
    config_dict = {
        "base_output_directory": config.base_output_directory,
        "directory_name_template": config.directory_name_template,
        "frame_filename_template": config.frame_filename_template,
        
        "extract_raw_frames": config.extract_raw_frames,
        "raw_image_format": config.raw_image_format,
        "raw_image_quality": config.raw_image_quality,
        "raw_resize_factor": config.raw_resize_factor,
        
        "extract_overlay_frames": config.extract_overlay_frames,
        "overlay_image_format": config.overlay_image_format,
        "overlay_image_quality": config.overlay_image_quality,
        "overlay_resize_factor": config.overlay_resize_factor,
        
        "skeleton_color": config.skeleton_color,
        "joint_color": config.joint_color,
        "confidence_threshold": config.confidence_threshold,
        "line_thickness": config.line_thickness,
        "joint_radius": config.joint_radius,
        "show_confidence": config.show_confidence,
        "show_person_id": config.show_person_id,
        "font_scale": config.font_scale,
        "font_color": config.font_color,
        
        "frame_range": config.frame_range,
        "frame_skip": config.frame_skip,
        "enable_progress_callback": config.enable_progress_callback,
        "log_extraction_details": config.log_extraction_details
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2)
    
    print(f"✅ Configuration saved to: {output_path}")


def example_1_basic_comprehensive_extraction():
    """Example 1: Basic comprehensive frame extraction."""
    print("=== Example 1: Basic Comprehensive Frame Extraction ===")
    
    # Set up paths
    video_path = "data/video.avi"
    poses_json = "outputs/pose_debug_20250619_131354.json"
    
    # Check if files exist
    if not Path(video_path).exists():
        print(f"❌ Video file not found: {video_path}")
        print("Please update the video_path variable to point to your video file")
        return False
    
    if not Path(poses_json).exists():
        print(f"❌ Poses JSON file not found: {poses_json}")
        print("Please update the poses_json variable to point to your poses file")
        return False
    
    # Create configuration
    config = create_sample_frame_config()
    
    # Create frame extraction manager
    manager = FrameExtractionManager(config)
    
    # Load poses from JSON file
    try:
        with open(poses_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to Pose objects (simplified)
        poses = []
        for pose_data in data.get('poses', []):
            joints = []
            for joint_data in pose_data.get('joints', []):
                keypoint = KeyPoint(
                    x=joint_data['keypoint']['x'],
                    y=joint_data['keypoint']['y'],
                    confidence=joint_data['keypoint']['confidence']
                )
                joint = Joint(
                    name=joint_data['name'],
                    keypoint=keypoint,
                    joint_id=joint_data.get('joint_id', 0)
                )
                joints.append(joint)
            
            pose = Pose(
                joints=joints,
                person_id=pose_data.get('person_id', 0),
                confidence=pose_data.get('confidence', 0.0)
            )
            if 'frame_number' in pose_data:
                pose.frame_number = pose_data['frame_number']
            poses.append(pose)
        
        print(f"✅ Loaded {len(poses)} poses from JSON file")
        
    except Exception as e:
        print(f"❌ Error loading poses: {e}")
        return False
    
    # Progress callback
    def progress_callback(progress: float, frame: int, total: int, phase: str = "frames"):
        if int(progress * 100) % 20 == 0:  # Log every 20%
            print(f"  {phase.title()} extraction: {progress:.1%} ({frame}/{total})")
    
    try:
        print(f"🎬 Extracting comprehensive frames from: {video_path}")
        print(f"📊 Using poses from: {poses_json}")
        
        # Extract both raw and overlay frames
        results = manager.extract_all_frame_types(
            video_path=video_path,
            poses=poses,
            progress_callback=progress_callback
        )
        
        # Display results
        summary = results.get('summary', {})
        print(f"\n✅ Comprehensive extraction completed!")
        print(f"   Raw frames: {summary.get('total_raw_frames', 0)}")
        print(f"   Overlay frames: {summary.get('total_overlay_frames', 0)}")
        print(f"   Directories created: {summary.get('directories_created', 0)}")
        
        print(f"\n📁 Output directories:")
        for extraction_type, directory_path in summary.get('output_directories', {}).items():
            print(f"   {extraction_type.title()}: {directory_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        import traceback
        traceback.print_exc()
        return False


def example_2_custom_configuration():
    """Example 2: Custom configuration with specific settings."""
    print("\n=== Example 2: Custom Configuration ===")
    
    # Create custom configuration
    custom_config = FrameExtractionConfig(
        # Only extract raw frames for this example
        extract_raw_frames=True,
        extract_overlay_frames=False,
        
        # PNG format with high quality
        raw_image_format="png",
        raw_image_quality=98,
        
        # Extract only first 25 frames
        frame_range=(0, 25),
        
        # Process every 2nd frame
        frame_skip=2,
        
        # Custom directory naming
        directory_name_template="custom_{type}_{video_name}_{timestamp}",
        frame_filename_template="custom_frame_{:05d}.{extension}"
    )
    
    # Save configuration for reuse
    config_path = "outputs/custom_frame_config.json"
    save_config_example(custom_config, config_path)
    
    print(f"📝 Custom configuration created with:")
    print(f"   - Extract raw frames only")
    print(f"   - PNG format, 98% quality")
    print(f"   - Frame range: 0-25")
    print(f"   - Frame skip: every 2nd frame")
    print(f"   - Custom naming pattern")
    
    return True


def example_3_output_manager_integration():
    """Example 3: Integration with OutputManager."""
    print("\n=== Example 3: OutputManager Integration ===")
    
    # Set up paths
    video_path = "data/video.avi"
    poses_json = "outputs/pose_debug_20250619_131354.json"
    
    if not Path(video_path).exists() or not Path(poses_json).exists():
        print("❌ Required files not found - skipping OutputManager example")
        return False
    
    try:
        # Create output manager
        json_output_path = Path("outputs/comprehensive_example.json")
        manager = OutputManager(json_output_path)
        manager.set_input_video_path(video_path)
        
        # Load poses (simplified for example)
        with open(poses_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        poses = []
        for pose_data in data.get('poses', [])[:50]:  # Limit to first 50 for demo
            joints = []
            for joint_data in pose_data.get('joints', []):
                keypoint = KeyPoint(
                    x=joint_data['keypoint']['x'],
                    y=joint_data['keypoint']['y'],
                    confidence=joint_data['keypoint']['confidence']
                )
                joint = Joint(
                    name=joint_data['name'],
                    keypoint=keypoint,
                    joint_id=joint_data.get('joint_id', 0)
                )
                joints.append(joint)
            
            pose = Pose(
                joints=joints,
                person_id=pose_data.get('person_id', 0),
                confidence=pose_data.get('confidence', 0.0)
            )
            if 'frame_number' in pose_data:
                pose.frame_number = pose_data['frame_number']
            poses.append(pose)
        
        manager.add_poses(poses)
        
        # Create custom frame config for first 25 frames
        frame_config = FrameExtractionConfig(
            base_output_directory="outputs",
            frame_range=(0, 25),
            extract_raw_frames=True,
            extract_overlay_frames=True,
            raw_image_quality=90,
            overlay_image_quality=90
        )
        
        # Progress tracking
        def progress_callback(progress: float, frame: int, total: int, phase: str = "frames"):
            if int(progress * 100) % 25 == 0:  # Log every 25%
                print(f"  OutputManager {phase}: {progress:.1%} ({frame}/{total})")
        
        print(f"🔧 Using OutputManager for comprehensive extraction...")
        print(f"   Processing first 25 frames with poses")
        
        # Generate comprehensive frame extractions
        extraction_results = manager.generate_comprehensive_frame_extractions(
            frame_config=frame_config,
            progress_callback=progress_callback
        )
        
        # Display results
        summary = extraction_results.get('summary', {})
        print(f"✅ OutputManager extraction completed!")
        print(f"   Raw frames: {summary.get('total_raw_frames', 0)}")
        print(f"   Overlay frames: {summary.get('total_overlay_frames', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error with OutputManager integration: {e}")
        return False


def example_4_configuration_variations():
    """Example 4: Different configuration variations."""
    print("\n=== Example 4: Configuration Variations ===")
    
    configurations = {
        "High Quality Raw Only": FrameExtractionConfig(
            extract_raw_frames=True,
            extract_overlay_frames=False,
            raw_image_format="png",
            raw_image_quality=100
        ),
        
        "Fast Overlay Processing": FrameExtractionConfig(
            extract_raw_frames=False,
            extract_overlay_frames=True,
            overlay_image_format="jpg",
            overlay_image_quality=75,
            frame_skip=3,  # Every 3rd frame
            confidence_threshold=0.3  # Higher confidence threshold
        ),
        
        "Balanced Quality": FrameExtractionConfig(
            extract_raw_frames=True,
            extract_overlay_frames=True,
            raw_image_quality=90,
            overlay_image_quality=90,
            frame_skip=2
        ),
        
        "Research Dataset": FrameExtractionConfig(
            extract_raw_frames=True,
            extract_overlay_frames=True,
            raw_image_format="png",
            overlay_image_format="png",
            raw_image_quality=100,
            overlay_image_quality=100,
            frame_skip=1,
            confidence_threshold=0.05,  # Very low threshold
            show_confidence=True,
            show_person_id=True
        )
    }
    
    print("📊 Available configuration variations:")
    for name, config in configurations.items():
        print(f"\n   {name}:")
        print(f"     - Raw frames: {'Yes' if config.extract_raw_frames else 'No'}")
        print(f"     - Overlay frames: {'Yes' if config.extract_overlay_frames else 'No'}")
        if config.extract_raw_frames:
            print(f"     - Raw format: {config.raw_image_format} @ {config.raw_image_quality}%")
        if config.extract_overlay_frames:
            print(f"     - Overlay format: {config.overlay_image_format} @ {config.overlay_image_quality}%")
        print(f"     - Frame skip: {config.frame_skip}")
        if hasattr(config, 'confidence_threshold'):
            print(f"     - Confidence threshold: {config.confidence_threshold}")
    
    # Save configurations for reference
    configs_dir = Path("outputs/config_examples")
    configs_dir.mkdir(exist_ok=True)
    
    for name, config in configurations.items():
        filename = name.lower().replace(" ", "_") + "_config.json"
        config_path = configs_dir / filename
        save_config_example(config, str(config_path))
    
    print(f"\n✅ All configurations saved to: {configs_dir}")
    
    return True


def main():
    """Run all comprehensive frame extraction examples."""
    print("🎬 Comprehensive Frame Extraction Examples")
    print("=" * 60)
    print()
    print("This script demonstrates the comprehensive frame extraction system")
    print("that creates two separate sets of outputs:")
    print("  📁 Raw frames: Unprocessed video frames")
    print("  📁 Overlay frames: Frames with pose annotations")
    print()
    
    # Create outputs directory
    Path("outputs").mkdir(exist_ok=True)
    
    examples = [
        ("Basic Comprehensive Extraction", example_1_basic_comprehensive_extraction),
        ("Custom Configuration", example_2_custom_configuration),
        ("OutputManager Integration", example_3_output_manager_integration),
        ("Configuration Variations", example_4_configuration_variations)
    ]
    
    results = {}
    for name, example_func in examples:
        try:
            results[name] = example_func()
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
            results[name] = False
    
    print("\n" + "=" * 60)
    print("🏁 Example Results Summary")
    print("=" * 60)
    
    for name, success in results.items():
        status = "✅ SUCCESS" if success else "❌ FAILED"
        print(f"{name}: {status}")
    
    successful_examples = sum(1 for success in results.values() if success)
    total_examples = len(results)
    
    print("=" * 60)
    print(f"📊 Summary: {successful_examples}/{total_examples} examples completed successfully")
    
    if successful_examples == total_examples:
        print("🎉 All examples completed successfully!")
        print("\nYou now have:")
        print("1. 📁 Separate directories for raw and overlay frames")
        print("2. ⚙️  Configurable extraction settings")
        print("3. 📈 Progress tracking and logging")
        print("4. 🔧 Integration with OutputManager")
        print("5. 📝 Reusable configuration files")
        print("\nTo use with your own videos:")
        print("- Update video_path and poses_json variables")
        print("- Customize FrameExtractionConfig for your needs")
        print("- Use CLI: --extract-comprehensive-frames")
    else:
        print("⚠️  Some examples failed. Check the error messages above.")
    
    return 0 if successful_examples == total_examples else 1


if __name__ == "__main__":
    sys.exit(main()) 