# OpenPose Parameters Reference

This document explains all the available parameters for OpenPose pose detection based on the [official OpenPose repository](https://github.com/CMU-Perceptual-Computing-Lab/openpose).

## Core Model Parameters

### `--model-pose`
**Options:** `COCO`, `MPI`, `MPI_4_layers`
**Default:** `COCO`
**Description:** 
- `COCO`: 25 keypoints (most comprehensive, recommended)
- `MPI`: 15 keypoints (faster, less detailed)
- `MPI_4_layers`: 15 keypoints (alternative MPI version)

### `--net-resolution`
**Options:** `368x368`, `656x368`, `1312x736`, custom (e.g., `432x368`)
**Default:** `368x368`
**Description:** Network input resolution. Higher resolutions are more accurate but slower.
- `368x368`: Fast processing, good for real-time
- `656x368`: Balanced accuracy/speed (recommended)
- `1312x736`: High accuracy, slow processing

### `--model-folder`
**Description:** Path to OpenPose models folder. Uses `OPENPOSEPATH` environment variable if not specified.

## Detection Quality Parameters

### `--confidence-threshold`
**Range:** `0.0` to `1.0`
**Default:** `0.1`
**Description:** Minimum confidence threshold for keypoints. Lower values detect more poses but may include false positives.

### `--scale-number`
**Range:** `1` to `4`
**Default:** `1`
**Description:** Number of scales to average. Higher values are more accurate but slower.

### `--scale-gap`
**Range:** `0.15` to `0.3`
**Default:** `0.3`
**Description:** Scale gap between scales. Lower values are more accurate but slower.

## Visualization Parameters

### `--show-confidence`
**Type:** Boolean flag
**Description:** Display confidence scores on keypoints in visualizations.

### `--keypoint-radius`
**Range:** `1+` pixels
**Default:** `4`
**Description:** Radius of keypoint circles in visualization.

### `--connection-thickness`
**Range:** `1+` pixels
**Default:** `2`
**Description:** Thickness of skeleton connection lines.

## Output Parameters

### `--output`
**Description:** Output JSON file path for pose data.

### `--overlay-video`
**Description:** Create overlay video with poses drawn (video inputs only).

### `--overlay-image`
**Description:** Create overlay image with poses drawn (image inputs only).

## Export Options

### `--export-csv`
**Description:** Export pose data in CSV format (Toronto Gait format).

### `--export-json`
**Description:** Export pose data in JSON format (Toronto Gait format).

### `--toronto-gait-format`
**Description:** Export in Toronto Older Adults Gait Archive format (both CSV and JSON).

### `--export-all-formats`
**Description:** Export in all available formats (JSON, CSV, video overlay).

## Frame Processing

### `--extract-frames`
**Description:** Extract individual frame images with pose overlays (video inputs only).

### `--extract-comprehensive-frames`
**Description:** Extract both raw frames and overlay frames to separate directories.

### `--frame-range`
**Format:** `start:end` (e.g., `10:50`)
**Description:** Specific frame range to process.

### `--frames-directory`
**Description:** Directory to save extracted frame images.

## Logging Parameters

### `--log-level`
**Options:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
**Default:** `INFO`
**Description:** Logging verbosity level.

### `--verbose`
**Type:** Boolean flag
**Description:** Enable verbose logging.

### `--log-file`
**Description:** Path to log file (logs to console if not specified).

## Advanced Configuration

### `--overlay-config`
**Description:** JSON file with overlay generation configuration.

### `--frame-extraction-config`
**Description:** JSON file with frame extraction configuration.

## Performance Recommendations

### For Speed (Real-time Processing)
```powershell
--net-resolution 368x368
--model-pose COCO
--scale-number 1
--scale-gap 0.3
--confidence-threshold 0.3
```

### For Accuracy (Research/Analysis)
```powershell
--net-resolution 656x368
--model-pose COCO  
--scale-number 2
--scale-gap 0.25
--confidence-threshold 0.1
```

### For High Accuracy (Offline Processing)
```powershell
--net-resolution 1312x736
--model-pose COCO
--scale-number 3
--scale-gap 0.2
--confidence-threshold 0.05
```

## Toronto Gait Archive Format

When using `--toronto-gait-format`, the system outputs data in the format specified by:
- **Reference:** Toronto Older Adults Gait Archive (Nature Scientific Data, 2022)
- **DOI:** 10.1038/s41597-022-01495-z
- **Features:**
  - Includes ALL video frames (even those without detected poses)
  - One row per frame with all joints as columns
  - Missing joints filled with 0,0,0 values
  - Maintains temporal continuity for gait analysis

## Usage Examples

### Basic Video Processing
```powershell
python src\video2pose.py input.mp4 --output results\pose.json
```

### High-Quality Research Export
```powershell
python src\video2pose.py input.mp4 `
    --output results\pose.json `
    --net-resolution 656x368 `
    --confidence-threshold 0.1 `
    --toronto-gait-format `
    --extract-comprehensive-frames `
    --overlay-video results\overlay.mp4
```

### Complete Analysis Pipeline
```powershell
python src\video2pose.py input.mp4 `
    --output results\pose.json `
    --export-all-formats `
    --overlay-video results\overlay.mp4 `
    --extract-comprehensive-frames `
    --verbose
``` 