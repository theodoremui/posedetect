# OpenPose PowerShell Scripts

This folder contains PowerShell scripts for running OpenPose pose detection with all available parameters based on the [official OpenPose repository](https://github.com/CMU-Perceptual-Computing-Lab/openpose).

## Quick Start

### 1. Simple Usage
For quick testing with default settings:
```powershell
.\run-simple.ps1
```

### 2. Full Configuration
For complete control over all parameters:
```powershell
.\run.ps1
```

## Files Included

| File | Description |
|------|-------------|
| `run-simple.ps1` | Quick start script with essential parameters only |
| `run.ps1` | Comprehensive script with all OpenPose parameters |
| `OPENPOSE_PARAMETERS.md` | Complete documentation of all parameters |

## Before Running

### 1. Install Dependencies
Ensure you have OpenPose installed and the `OPENPOSEPATH` environment variable set:
```powershell
# Set OpenPose path (example)
$env:OPENPOSEPATH = "C:\path\to\openpose"
```

### 2. Prepare Input Data
Place your video files in the `data\videos\` directory:
```
data/
  videos/
    video.avi
    another_video.mp4
```

### 3. Create Output Directory
```powershell
mkdir outputs -Force
```

## Customizing Parameters

### Simple Script (`run-simple.ps1`)
Edit these variables at the top of the file:
```powershell
$INPUT = ".\data\videos\your_video.avi"
$OUTPUT = ".\outputs\pose.json"
$CONFIDENCE = 0.3           # 0.0-1.0
$RESOLUTION = "656x368"     # "368x368", "656x368", "1312x736"
$MODEL = "COCO"             # "COCO", "MPI", "MPI_4_layers"
```

### Full Script (`run.ps1`)
The comprehensive script has organized sections for easy modification:

**Model Parameters:**
```powershell
$MODEL_POSE = "COCO"        # COCO (25 keypoints), MPI (15 keypoints)
$NET_RESOLUTION = "656x368" # Higher = more accurate but slower
$SCALE_NUMBER = 1           # 1-4, higher = more accurate but slower
$CONFIDENCE_THRESHOLD = 0.3 # 0.0-1.0, lower = more detections
```

**Export Options:**
```powershell
$EXPORT_CSV = $true                    # Export Toronto Gait CSV
$EXPORT_JSON = $true                   # Export Toronto Gait JSON
$TORONTO_GAIT_FORMAT = $true           # Research standard format
$EXTRACT_COMPREHENSIVE_FRAMES = $true  # Extract frame images
```

## Output Files

The scripts will generate:

### Standard Outputs
- **JSON file:** Pose keypoints in Toronto Gait format
- **CSV file:** Pose data in research-compatible format
- **Overlay video:** Video with pose visualizations drawn

### Frame Extraction (if enabled)
- **Raw frames:** Original video frames as images
- **Overlay frames:** Frames with pose overlays drawn

### Directory Structure
```
outputs/
  openpose-video-results/
    pose_20241219_143022.json      # Timestamped JSON
    pose_20241219_143022.csv       # Timestamped CSV
    overlay.mp4                    # Overlay video
    pose_20241219_143022_raw/      # Raw frame images
    pose_20241219_143022_overlay/  # Overlay frame images
```

## Performance Tuning

### For Speed (Real-time)
```powershell
$NET_RESOLUTION = "368x368"
$SCALE_NUMBER = 1
$CONFIDENCE_THRESHOLD = 0.3
```

### For Accuracy (Research)
```powershell
$NET_RESOLUTION = "656x368"  
$SCALE_NUMBER = 2
$CONFIDENCE_THRESHOLD = 0.1
```

### For Maximum Quality (Offline)
```powershell
$NET_RESOLUTION = "1312x736"
$SCALE_NUMBER = 3
$CONFIDENCE_THRESHOLD = 0.05
```

## Troubleshooting

### Common Issues

**OpenPose not found:**
```powershell
# Check if OPENPOSEPATH is set
echo $env:OPENPOSEPATH

# Set manually if needed
$env:OPENPOSEPATH = "C:\path\to\openpose"
```

**Out of memory errors:**
- Reduce `$NET_RESOLUTION` to `368x368`
- Set `$SCALE_NUMBER` to `1`
- Process shorter video segments using `$FRAME_RANGE`

**Slow processing:**
- Use `$NET_RESOLUTION = "368x368"` for faster processing
- Set `$EXTRACT_COMPREHENSIVE_FRAMES = $false` to skip frame extraction
- Increase `$CONFIDENCE_THRESHOLD` to reduce false detections

**No poses detected:**
- Lower `$CONFIDENCE_THRESHOLD` (try `0.1`)
- Check if people are clearly visible in the video
- Try different `$MODEL_POSE` options

## Batch Processing

To process multiple videos, modify the script:
```powershell
# Process all videos in a folder
Get-ChildItem ".\data\videos\*.avi" | ForEach-Object {
    $INPUT_FILE = $_.FullName
    $OUTPUT_JSON = ".\outputs\$($_.BaseName)_pose.json"
    # ... run detection command
}
```

## Command Line Alternative

You can also run the detection directly without scripts:
```powershell
python src\video2pose.py input.mp4 --output pose.json --toronto-gait-format
```

For all available options:
```powershell
python src\video2pose.py --help
```

## Support

- Review `OPENPOSE_PARAMETERS.md` for detailed parameter explanations
- Check the official [OpenPose repository](https://github.com/CMU-Perceptual-Computing-Lab/openpose) for installation help
- Enable `--verbose` logging for detailed processing information 