#!/usr/bin/env python3
"""
Example Usage of Enhanced Pose Detection System

This script demonstrates the CSV export and video overlay functionality
added to the pose detection system.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from posedetect.exporters.csv_exporter import CSVExporter, CSVFormat
from posedetect.video.overlay_generator import VideoOverlayGenerator, OverlayConfig
from posedetect.utils.output_manager import OutputManager
from posedetect.models.pose import Pose, Joint, KeyPoint


def create_sample_poses():
    """Create sample pose data for demonstration."""
    poses = []
    
    # Create pose 1
    joints1 = [
        Joint(name="nose", keypoint=KeyPoint(x=100.0, y=50.0, confidence=0.9), joint_id=0),
        Joint(name="left_eye", keypoint=KeyPoint(x=95.0, y=45.0, confidence=0.8), joint_id=1),
        Joint(name="right_eye", keypoint=KeyPoint(x=105.0, y=45.0, confidence=0.85), joint_id=2),
        Joint(name="left_shoulder", keypoint=KeyPoint(x=80.0, y=80.0, confidence=0.7), joint_id=5),
        Joint(name="right_shoulder", keypoint=KeyPoint(x=120.0, y=80.0, confidence=0.75), joint_id=6),
    ]
    pose1 = Pose(joints=joints1, person_id=0, confidence=0.85)
    pose1.frame_number = 0
    pose1.timestamp = 0.0
    poses.append(pose1)
    
    # Create pose 2
    joints2 = [
        Joint(name="nose", keypoint=KeyPoint(x=200.0, y=60.0, confidence=0.75), joint_id=0),
        Joint(name="left_shoulder", keypoint=KeyPoint(x=180.0, y=80.0, confidence=0.7), joint_id=5),
        Joint(name="right_shoulder", keypoint=KeyPoint(x=220.0, y=80.0, confidence=0.72), joint_id=6),
    ]
    pose2 = Pose(joints=joints2, person_id=1, confidence=0.72)
    pose2.frame_number = 1
    pose2.timestamp = 0.033
    poses.append(pose2)
    
    return poses


def demonstrate_csv_export():
    """Demonstrate CSV export functionality."""
    print("🔄 Demonstrating CSV Export Functionality")
    print("=" * 50)
    
    poses = create_sample_poses()
    
    # Demonstrate different CSV formats
    formats_to_test = [
        (CSVFormat.NORMALIZED, "Normalized format - one row per joint"),
        (CSVFormat.WIDE, "Wide format - one row per pose, joints as columns"),
        (CSVFormat.SUMMARY, "Summary format - aggregate statistics per pose")
    ]
    
    for csv_format, description in formats_to_test:
        print(f"\n📊 {description}")
        exporter = CSVExporter(csv_format)
        output_path = Path(f"example_output_{csv_format.value}.csv")
        
        try:
            exporter.export_poses(poses, output_path, include_metadata=True)
            print(f"✅ Successfully exported to: {output_path}")
            
            # Show first few lines of the CSV
            with open(output_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:4]  # Show header + 3 data lines
                print("📄 Sample content:")
                for line in lines:
                    print(f"   {line.strip()}")
                if len(lines) < len(poses) * 2:  # Rough estimate
                    print("   ... (more rows)")
                    
        except Exception as e:
            print(f"❌ Export failed: {e}")
        
        print()


def demonstrate_output_manager():
    """Demonstrate enhanced OutputManager functionality."""
    print("🔄 Demonstrating Enhanced Output Manager")
    print("=" * 50)
    
    poses = create_sample_poses()
    output_path = Path("example_output_manager.json")
    
    # Create output manager and add poses
    manager = OutputManager(output_path)
    manager.add_poses(poses)
    
    # Get export summary
    summary = manager.get_export_summary()
    print("📋 Export Summary:")
    print(f"   Poses count: {summary['poses_count']}")
    print(f"   Available CSV formats: {summary['available_csv_formats']}")
    print(f"   Video overlay supported: {summary['video_overlay_supported']}")
    
    # Export all CSV formats
    print("\n📊 Exporting all CSV formats...")
    try:
        csv_files = manager.export_all_csv_formats()
        print(f"✅ Successfully exported {len(csv_files)} CSV formats:")
        for format_name, file_path in csv_files.items():
            print(f"   - {format_name}: {file_path}")
    except Exception as e:
        print(f"❌ CSV export failed: {e}")
    
    # Export JSON
    print("\n📄 Exporting JSON...")
    try:
        manager.save_json("example_input.mp4", {"example": "metadata"})
        print(f"✅ Successfully exported JSON to: {output_path}")
    except Exception as e:
        print(f"❌ JSON export failed: {e}")


def demonstrate_overlay_config():
    """Demonstrate overlay configuration options."""
    print("🔄 Demonstrating Overlay Configuration")
    print("=" * 50)
    
    # Default configuration
    default_config = OverlayConfig()
    print("🎨 Default Overlay Configuration:")
    print(f"   Codec: {default_config.output_codec}")
    print(f"   Skeleton color: {default_config.skeleton_color}")
    print(f"   Joint color: {default_config.joint_color}")
    print(f"   Confidence threshold: {default_config.confidence_threshold}")
    print(f"   Line thickness: {default_config.line_thickness}")
    print(f"   Joint radius: {default_config.joint_radius}")
    
    # Custom configuration
    custom_config = OverlayConfig(
        output_codec='XVID',
        skeleton_color=(255, 0, 0),  # Red skeleton
        joint_color=(0, 255, 0),     # Green joints
        confidence_threshold=0.5,
        line_thickness=3,
        joint_radius=6,
        show_confidence=True,
        show_person_id=True,
        font_scale=0.7
    )
    
    print("\n🎨 Custom Overlay Configuration:")
    print(f"   Codec: {custom_config.output_codec}")
    print(f"   Skeleton color: {custom_config.skeleton_color}")
    print(f"   Joint color: {custom_config.joint_color}")
    print(f"   Confidence threshold: {custom_config.confidence_threshold}")
    print(f"   Line thickness: {custom_config.line_thickness}")
    print(f"   Joint radius: {custom_config.joint_radius}")


def main():
    """Main demonstration function."""
    print("🎯 Enhanced Pose Detection System - Usage Examples")
    print("=" * 60)
    
    try:
        demonstrate_csv_export()
        demonstrate_output_manager()
        demonstrate_overlay_config()
        
        print("\n🎉 All demonstrations completed successfully!")
        print("\n📚 Usage Summary:")
        print("=" * 30)
        print("1. CSV Export: Use CSVExporter with different formats")
        print("2. Output Manager: Coordinate multi-format exports")
        print("3. Video Overlay: Configure visualization with OverlayConfig")
        print("4. CLI: Use --export-all-formats for complete export")
        
        print("\n💡 Next Steps:")
        print("- Run: python -m src.posedetect.cli.main --help")
        print("- Try: --export-csv --csv-format all")
        print("- Try: --export-all-formats for complete export")
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 