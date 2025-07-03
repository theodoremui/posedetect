# OpenPose Pose Detection Script
# This script runs the OpenPose-based pose detection with configurable parameters
# Based on OpenPose parameters from: https://github.com/CMU-Perceptual-Computing-Lab/openpose

# =============================================================================
# INPUT/OUTPUT PARAMETERS
# =============================================================================

# Input file (video or image)
$INPUT_FILE = ".\data\videos\video.avi"

# Output directory for results
$OUTPUT_JSON = ".\outputs\openpose-video-results\pose.json"

# Optional overlay outputs
$OVERLAY_VIDEO = ".\outputs\openpose-video-results\overlay.mp4"
# $OVERLAY_IMAGE = ".\outputs\openpose-video-results\overlay.jpg"  # For image inputs only

# =============================================================================
# OPENPOSE MODEL PARAMETERS
# =============================================================================

# OpenPose model folder path (uses OPENPOSEPATH environment variable if not specified)
# $MODEL_FOLDER = "C:\path\to\openpose\models"

# Pose model to use: COCO (25 keypoints), MPI (15 keypoints), MPI_4_layers (15 keypoints)
$MODEL_POSE = "COCO"

# Network input resolution (higher = more accurate but slower)
# Common options: 368x368, 656x368, 1312x736
$NET_RESOLUTION = "656x368"

# Number of scales to average (1-4, higher = more accurate but slower)
$SCALE_NUMBER = 1

# Scale gap between scales (0.15-0.3, lower = more accurate but slower)
$SCALE_GAP = 0.25

# =============================================================================
# DETECTION CONFIDENCE PARAMETERS
# =============================================================================

# Minimum confidence threshold for keypoints (0.0-1.0)
# Lower = more detections but potentially more false positives
$CONFIDENCE_THRESHOLD = 0.3

# =============================================================================
# VISUALIZATION PARAMETERS
# =============================================================================

# Show confidence scores in visualizations
$SHOW_CONFIDENCE = $true

# Keypoint circle radius in visualization (pixels)
$KEYPOINT_RADIUS = 4

# Connection line thickness in visualization (pixels)
$CONNECTION_THICKNESS = 2

# =============================================================================
# EXPORT OPTIONS
# =============================================================================

# Export CSV data (Toronto Gait format)
$EXPORT_CSV = $true

# Export JSON data (Toronto Gait format)
$EXPORT_JSON = $true

# Export in Toronto Older Adults Gait Archive format
$TORONTO_GAIT_FORMAT = $true

# Export all available formats (JSON, CSV, video overlay)
$EXPORT_ALL_FORMATS = $false

# =============================================================================
# VIDEO/FRAME PROCESSING OPTIONS
# =============================================================================

# Extract individual frame images with pose overlays (video inputs only)
$EXTRACT_FRAMES = $false

# Extract both raw frames and overlay frames to separate directories
$EXTRACT_COMPREHENSIVE_FRAMES = $true

# Frame range to extract (format: start:end, e.g., "10:50")
# $FRAME_RANGE = "0:100"

# Directory to save extracted frame images
# $FRAMES_DIRECTORY = ".\outputs\openpose-video-results\frames"

# =============================================================================
# LOGGING PARAMETERS
# =============================================================================

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
$LOG_LEVEL = "INFO"

# Enable verbose logging
$VERBOSE = $true

# Log to file (optional)
# $LOG_FILE = ".\outputs\openpose-video-results\processing.log"

# =============================================================================
# ADVANCED OPTIONS
# =============================================================================

# JSON file with overlay generation configuration (optional)
# $OVERLAY_CONFIG = ".\config\overlay_config.json"

# JSON file with frame extraction configuration (optional)
# $FRAME_EXTRACTION_CONFIG = ".\config\frame_extraction_config.json"

# =============================================================================
# BUILD COMMAND
# =============================================================================

Write-Host "🚀 Starting OpenPose Pose Detection..." -ForegroundColor Green
Write-Host "Input: $INPUT_FILE" -ForegroundColor Cyan
Write-Host "Output: $OUTPUT_JSON" -ForegroundColor Cyan
Write-Host "Model: $MODEL_POSE @ $NET_RESOLUTION" -ForegroundColor Yellow

# Build the command with all parameters
$cmd = @(
    "python", "src\video2pose.py"
    $INPUT_FILE
    "--output", $OUTPUT_JSON
)

# Model parameters
if ($MODEL_FOLDER) { $cmd += "--model-folder", $MODEL_FOLDER }
$cmd += "--model-pose", $MODEL_POSE
$cmd += "--net-resolution", $NET_RESOLUTION
$cmd += "--scale-number", $SCALE_NUMBER
$cmd += "--scale-gap", $SCALE_GAP

# Detection parameters
$cmd += "--confidence-threshold", $CONFIDENCE_THRESHOLD

# Visualization parameters
if ($SHOW_CONFIDENCE) { $cmd += "--show-confidence" }
$cmd += "--keypoint-radius", $KEYPOINT_RADIUS
$cmd += "--connection-thickness", $CONNECTION_THICKNESS

# Output parameters
if ($OVERLAY_VIDEO) { $cmd += "--overlay-video", $OVERLAY_VIDEO }
# if ($OVERLAY_IMAGE) { $cmd += "--overlay-image", $OVERLAY_IMAGE }

# Export options
if ($EXPORT_CSV) { $cmd += "--export-csv" }
if ($EXPORT_JSON) { $cmd += "--export-json" }
if ($TORONTO_GAIT_FORMAT) { $cmd += "--toronto-gait-format" }
if ($EXPORT_ALL_FORMATS) { $cmd += "--export-all-formats" }

# Frame processing options
if ($EXTRACT_FRAMES) { $cmd += "--extract-frames" }
if ($EXTRACT_COMPREHENSIVE_FRAMES) { $cmd += "--extract-comprehensive-frames" }
if ($FRAME_RANGE) { $cmd += "--frame-range", $FRAME_RANGE }
if ($FRAMES_DIRECTORY) { $cmd += "--frames-directory", $FRAMES_DIRECTORY }

# Advanced configuration
if ($OVERLAY_CONFIG) { $cmd += "--overlay-config", $OVERLAY_CONFIG }
if ($FRAME_EXTRACTION_CONFIG) { $cmd += "--frame-extraction-config", $FRAME_EXTRACTION_CONFIG }

# Logging parameters
$cmd += "--log-level", $LOG_LEVEL
if ($VERBOSE) { $cmd += "--verbose" }
if ($LOG_FILE) { $cmd += "--log-file", $LOG_FILE }

# =============================================================================
# EXECUTE COMMAND
# =============================================================================

Write-Host "`n📋 Command to execute:" -ForegroundColor Yellow
Write-Host ($cmd -join " ") -ForegroundColor Gray

Write-Host "`n⏳ Processing..." -ForegroundColor Yellow

try {
    # Execute the command
    & $cmd[0] $cmd[1..($cmd.Length-1)]
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Processing completed successfully!" -ForegroundColor Green
        
        # Show output summary
        Write-Host "`n📁 Output files:" -ForegroundColor Cyan
        if (Test-Path $OUTPUT_JSON) { Write-Host "  • JSON: $OUTPUT_JSON" -ForegroundColor White }
        if ($OVERLAY_VIDEO -and (Test-Path $OVERLAY_VIDEO)) { Write-Host "  • Video: $OVERLAY_VIDEO" -ForegroundColor White }
        
        # Check for additional outputs
        $outputDir = Split-Path $OUTPUT_JSON -Parent
        $csvFiles = Get-ChildItem -Path $outputDir -Filter "*.csv" -ErrorAction SilentlyContinue
        if ($csvFiles) {
            Write-Host "  • CSV files: $($csvFiles.Count) files in $outputDir" -ForegroundColor White
        }
        
        $framesDirs = Get-ChildItem -Path $outputDir -Directory -Filter "*frames*" -ErrorAction SilentlyContinue
        if ($framesDirs) {
            Write-Host "  • Frame directories: $($framesDirs.Count) directories in $outputDir" -ForegroundColor White
        }
        
    } else {
        Write-Host "`n❌ Processing failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host "`n💥 Error occurred: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🏁 Script completed." -ForegroundColor Blue 