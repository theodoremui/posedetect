#!/usr/bin/env python3
"""
Example: Frame Extraction with Pose Overlays

This script demonstrates how to extract individual frames from a video
with pose overlays applied to each frame.
"""

import os
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from posedetect.video.overlay_generator import VideoOverlayGenerator, OverlayConfig
from posedetect.utils.output_manager import OutputManager


def main():
    """Demonstrate frame extraction functionality."""
    
    # Example 1: Basic frame extraction
    print("=== Example 1: Basic Frame Extraction ===")
    
    # Set up paths
    video_path = "data/video.avi"  # Your video file
    poses_json = "outputs/pose_debug_20250619_131354.json"  # Your poses JSON
    output_frames_dir = "outputs/extracted_frames"
    
    # Check if files exist
    if not Path(video_path).exists():
        print(f"❌ Video file not found: {video_path}")
        print("Please update the video_path variable to point to your video file")
        return
    
    if not Path(poses_json).exists():
        print(f"❌ Poses JSON file not found: {poses_json}")
        print("Please update the poses_json variable to point to your poses file")
        return
    
    # Configure overlay settings
    config = OverlayConfig(
        skeleton_color=(0, 255, 0),      # Green skeleton
        joint_color=(255, 0, 0),         # Red joints
        confidence_threshold=0.1,        # Low threshold to show more poses
        line_thickness=2,                # Skeleton line thickness
        joint_radius=4,                  # Joint circle size
        show_confidence=True,            # Show confidence scores
        show_person_id=True,             # Show person IDs
        image_format='jpg',              # Output format
        image_quality=95,                # High quality
        frame_filename_template='frame_{:05d}.jpg'  # Filename pattern
    )
    
    # Create overlay generator
    generator = VideoOverlayGenerator(config)
    
    # Progress callback
    def progress_callback(progress: float, frame: int, total: int):
        print(f"Progress: {progress:.1%} ({frame}/{total} frames)")
    
    try:
        # Extract all frames with pose overlays
        print(f"Extracting frames from: {video_path}")
        print(f"Using poses from: {poses_json}")
        print(f"Output directory: {output_frames_dir}")
        
        frame_files = generator.generate_frame_overlays(
            input_video_path=video_path,
            poses_data=poses_json,
            output_directory=output_frames_dir,
            progress_callback=progress_callback
        )
        
        print(f"✅ Successfully extracted {len(frame_files)} frames!")
        print(f"Frames saved to: {output_frames_dir}")
        
        # Show first few filenames
        if frame_files:
            print("\nFirst few generated files:")
            for i, frame_file in enumerate(frame_files[:5]):
                print(f"  {frame_file.name}")
            if len(frame_files) > 5:
                print(f"  ... and {len(frame_files) - 5} more")
                
    except Exception as e:
        print(f"❌ Error extracting frames: {e}")
        return
    
    # Example 2: Extract specific frame range
    print("\n=== Example 2: Extract Specific Frame Range ===")
    
    range_output_dir = "outputs/frames_10_to_50"
    
    try:
        # Extract frames 10-50 only
        print(f"Extracting frames 10-50 to: {range_output_dir}")
        
        range_frame_files = generator.generate_frame_overlays(
            input_video_path=video_path,
            poses_data=poses_json,
            output_directory=range_output_dir,
            frame_range=(10, 50),  # Only frames 10-50
            progress_callback=progress_callback
        )
        
        print(f"✅ Successfully extracted {len(range_frame_files)} frames from range 10-50!")
        
    except Exception as e:
        print(f"❌ Error extracting frame range: {e}")
    
    # Example 3: Using OutputManager for integrated workflow
    print("\n=== Example 3: Using OutputManager ===")
    
    try:
        # Create output manager
        json_output_path = Path("outputs/pose_example.json")
        manager = OutputManager(json_output_path)
        
        # Set input video for overlay generation
        manager.set_input_video_path(video_path)
        
        # Load existing poses (in real usage, you'd add poses from detection)
        if Path(poses_json).exists():
            import json
            with open(poses_json, 'r') as f:
                data = json.load(f)
            
            # Convert to Pose objects (simplified for example)
            from posedetect.models.pose import Pose, Joint, KeyPoint
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
                # Add frame info
                if 'frame_number' in pose_data:
                    pose.frame_number = pose_data['frame_number']
                poses.append(pose)
            
            manager.add_poses(poses)
            
            # Generate frame overlays using the manager
            manager_output_dir = "outputs/manager_frames"
            
            print(f"Using OutputManager to extract frames to: {manager_output_dir}")
            
            manager_frame_files = manager.generate_frame_overlays(
                output_frames_directory=Path(manager_output_dir),
                config=config,
                frame_range=(0, 25),  # First 25 frames
                progress_callback=progress_callback
            )
            
            print(f"✅ OutputManager extracted {len(manager_frame_files)} frames!")
            
    except Exception as e:
        print(f"❌ Error with OutputManager: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Frame Extraction Examples Complete ===")
    print("You can now:")
    print("1. View the extracted frame images")
    print("2. Use them for presentations or analysis")
    print("3. Create custom frame ranges for specific analysis")
    print("4. Adjust overlay settings for different visualization needs")


if __name__ == "__main__":
    main() 