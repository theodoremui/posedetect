# Pose Filtering Functionality

This document explains the pose filtering system that automatically removes frames and data points where no valid poses are detected during video processing.

## Overview

The pose filtering system ensures that only frames with valid pose detections are included in:
- CSV exports (all formats)
- JSON exports  
- Individual frame extractions (both raw and overlay frames)
- Video overlay generation

## How It Works

### 1. Pose Validation

A pose is considered **valid** if it meets the following criteria:
- Has at least one joint with confidence >= threshold (default: 0.1)
- The minimum valid joints requirement is met (default: 1 joint)

### 2. Frame Filtering

Frames are automatically filtered during processing:
- **Raw frame extraction**: Only extracts frames that contain valid poses
- **Overlay frame extraction**: Only creates overlays for frames with valid poses
- **CSV/JSON export**: Only includes data from frames with valid poses

### 3. Automatic Application

The filtering is applied automatically in both:
- **Video processing**: `process_video()` function
- **Image processing**: `process_image()` function (for consistency)

## Configuration

### Confidence Threshold

The confidence threshold for joint validity is controlled by the `--confidence-threshold` command line argument:

```bash
# Use higher threshold (more strict filtering)
python src/video2pose.py input.mp4 --confidence-threshold 0.3

# Use lower threshold (less strict filtering)  
python src/video2pose.py input.mp4 --confidence-threshold 0.05
```

### Minimum Valid Joints

Currently set to 1 joint minimum. This can be modified in the filtering functions if needed.

## Output Examples

### Before Filtering
```
Original video: 1000 frames
Detected poses: 500 poses across 300 frames
Output: 1000 raw frames + 300 overlay frames + CSV with 500 rows
```

### After Filtering
```
Original video: 1000 frames  
Detected poses: 500 poses across 300 frames
Valid poses: 400 poses across 200 frames (after filtering)
Output: 200 raw frames + 200 overlay frames + CSV with 400 rows
```

## Logging

The system provides detailed logging of filtering results:

```
INFO - Pose filtering results:
INFO -   Original poses: 500
INFO -   Valid poses: 400  
INFO -   Removed poses: 100
INFO -   Filtered out: 20.0% of poses

INFO - Pose filtering completed:
INFO -   Retained 400 poses from 500 total
INFO -   Retained 200 frames from 300 total
INFO -   Frame retention rate: 66.7%
```

## API Reference

### Core Functions

#### `has_valid_pose(pose, confidence_threshold=0.1, min_valid_joints=1)`
Check if a single pose has valid detections.

**Parameters:**
- `pose`: Pose object to validate
- `confidence_threshold`: Minimum confidence for valid joint (default: 0.1)
- `min_valid_joints`: Minimum number of valid joints required (default: 1)

**Returns:** `bool` - True if pose is valid

#### `filter_poses_by_validity(poses, confidence_threshold=0.1, min_valid_joints=1)`
Filter a list of poses to keep only valid ones.

**Parameters:**
- `poses`: List of Pose objects to filter
- `confidence_threshold`: Minimum confidence for valid joint (default: 0.1)  
- `min_valid_joints`: Minimum number of valid joints required (default: 1)

**Returns:** `List[Pose]` - Filtered list containing only valid poses

#### `get_frames_with_valid_poses(poses, confidence_threshold=0.1, min_valid_joints=1)`
Get set of frame numbers that contain valid poses.

**Parameters:**
- `poses`: List of Pose objects to analyze
- `confidence_threshold`: Minimum confidence for valid joint (default: 0.1)
- `min_valid_joints`: Minimum number of valid joints required (default: 1)

**Returns:** `Set[int]` - Set of frame numbers with valid poses

### Usage Examples

```python
from src.posedetect.utils.pose_filter import (
    has_valid_pose, 
    filter_poses_by_validity,
    get_frames_with_valid_poses
)

# Check if a pose is valid
if has_valid_pose(pose, confidence_threshold=0.2):
    print("Pose has valid detections")

# Filter poses
valid_poses = filter_poses_by_validity(
    all_poses, 
    confidence_threshold=0.1,
    min_valid_joints=2
)

# Get valid frame numbers
valid_frames = get_frames_with_valid_poses(poses)
print(f"Valid frames: {valid_frames}")
```

## Benefits

1. **Cleaner Data**: Only includes meaningful pose detections
2. **Reduced Storage**: Fewer output files and smaller CSV/JSON files
3. **Better Analysis**: Easier to work with data that contains actual poses
4. **Automatic**: No manual intervention required
5. **Configurable**: Threshold can be adjusted based on use case

## Integration

The filtering system is fully integrated into the existing workflow:

- Works with all existing command-line options
- Compatible with all CSV export formats
- Works with both comprehensive and selective frame extraction
- Maintains all existing functionality while adding filtering

## Technical Details

The filtering system:
- Uses the existing confidence threshold from command line arguments
- Applies filtering before data reaches OutputManager
- Modifies frame extraction to skip invalid frames
- Provides detailed statistics and logging
- Is thoroughly tested with unit tests 