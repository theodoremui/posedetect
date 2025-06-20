# PoseDetect: OpenPose-based Human Pose Detection

A comprehensive, well-structured Python application for extracting human pose information from video and image files using OpenPose. Built with software engineering best practices including SOLID principles, DRY methodology, proper testing, and modular architecture.

## Features

- **Multi-format Support**: Process both video files (MP4, AVI, MOV, etc.) and image files (JPG, PNG, BMP, etc.)
- **OpenPose Integration**: Seamless integration with OpenPose for accurate human pose detection
- **Comprehensive Output**: JSON and CSV export formats with detailed metadata
- **Visualization**: Create overlay videos and images with pose annotations
- **Robust Architecture**: Built following SOLID principles with proper separation of concerns
- **Extensive Testing**: Comprehensive test suite with pytest for reliability
- **Rich Logging**: Configurable logging with loguru for debugging and monitoring
- **CLI Interface**: User-friendly command-line interface with extensive configuration options

## Prerequisites

- **Python 3.7** (specific version required for OpenPose compatibility)
- OpenPose library properly installed
- OPENPOSEPATH environment variable pointing to your OpenPose installation

## Python Version Compatibility

**Your OpenPose installation requires exactly Python 3.7** because the precompiled binaries are version-specific:

- **Available**: `pyopenpose.cp37-win_amd64.pyd` (Python 3.7)
- **Your Python**: 3.8.20 (incompatible)
- **Solution**: Use Python 3.7

### Python 3.7 Requirements

The default OpenPose was developed on Python 3.7. The available Windows binary was created based on Python 3.7.


1. **Download & Install Python 3.7.9**: 
   ```
   https://www.python.org/ftp/python/3.7.9/python-3.7.9-amd64.exe
   ```
   Check "Add Python to PATH"  
   You can keep your current Python 3.8

2. **Run the automated setup**:
   ```cmd
   setup_python37_fixed.bat
   ```

3. **Or manual setup**:
   ```cmd
   # Create Python 3.7 environment
   py -3.7 -m venv .venv37
   
   # Activate it  
   .venv37\Scripts\activate.bat
   
   # Install dependencies
   pip install -e .
   
   # Test OpenPose
   python quick_test.py
   ```

### Verification

After setup, you should see:
```
🐍 Python 3.7.9
📁 OPENPOSEPATH: C:\Users\...\openpose
✅ pyopenpose imported successfully!
✅ WrapperPython created!
🎉 OpenPose is working correctly!
```

### OpenPose Installation

1. Install OpenPose following the [official installation guide](https://github.com/CMU-Perceptual-Computing-Lab/openpose)
2. Set the `OPENPOSEPATH` environment variable to point to your OpenPose installation directory
3. Ensure OpenPose Python bindings are properly compiled and accessible

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd posedetect
```

2. Install the package and dependencies:
```bash
pip install -e .
```

3. For development, install with dev dependencies:
```bash
pip install -e ".[dev]"
```

## Usage

### Basic Usage

Process a video file (automatically generates timestamped JSON and CSV files):
```bash
python -m posedetect.cli.main input_video.mp4 --output outputs/poses.json
# Generates: outputs/poses_20250619_140615.json and outputs/poses_20250619_140615.csv
```

Process an image file (automatically generates timestamped JSON and CSV files):
```bash
python -m posedetect.cli.main input_image.jpg --output outputs/poses.json
# Generates: outputs/poses_20250619_140732.json and outputs/poses_20250619_140732.csv
```

### Advanced Usage

```bash
# Custom output location (JSON and CSV automatically generated with timestamps)
python -m posedetect.cli.main input.mp4 --output results/poses.json

# Create overlay video with poses
python -m posedetect.cli.main input.mp4 --overlay-video output_with_poses.mp4

# Export all formats (JSON, all CSV variants, and video overlay)
python -m posedetect.cli.main input.mp4 --export-all-formats

# Export additional CSV formats (normalized is always generated)
python -m posedetect.cli.main input.mp4 --export-csv --csv-format all

# Custom OpenPose configuration
python -m posedetect.cli.main input.mp4 --net-resolution 656x368 --model-pose COCO

# Verbose logging with custom confidence threshold
python -m posedetect.cli.main input.mp4 --verbose --confidence-threshold 0.5

# Custom overlay configuration
python -m posedetect.cli.main input.mp4 --overlay-video output.mp4 --overlay-config config.json

# Extract individual frame images with pose overlays (video inputs only)
python -m posedetect.cli.main input.mp4 --extract-frames

# Extract specific frame range (frames 10-50)
python -m posedetect.cli.main input.mp4 --extract-frames --frame-range 10:50

# Specify custom directory for extracted frames
python -m posedetect.cli.main input.mp4 --extract-frames --frames-directory my_frames/

# Combine frame extraction with other exports
python -m posedetect.cli.main input.mp4 --export-all-formats --extract-frames --frame-range 0:100

# Extract comprehensive frame sets (raw + overlay frames to separate directories)
python -m posedetect.cli.main input.mp4 --extract-comprehensive-frames

# Comprehensive extraction with custom configuration
python -m posedetect.cli.main input.mp4 --extract-comprehensive-frames --frame-extraction-config config.json

# Comprehensive extraction with frame range
python -m posedetect.cli.main input.mp4 --extract-comprehensive-frames --frame-range 0:50
```

### Command Line Options

```
usage: video2pose.py [-h] [--output OUTPUT] [--overlay-video OVERLAY_VIDEO]
                     [--overlay-image OVERLAY_IMAGE] [--model-folder MODEL_FOLDER]
                     [--net-resolution NET_RESOLUTION] [--model-pose {COCO,MPI,MPI_4_layers}]
                     [--scale-number SCALE_NUMBER] [--scale-gap SCALE_GAP]
                     [--confidence-threshold CONFIDENCE_THRESHOLD] [--show-confidence]
                     [--keypoint-radius KEYPOINT_RADIUS] [--connection-thickness CONNECTION_THICKNESS]
                     [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [--log-file LOG_FILE]
                     [--verbose] [--export-csv]
                     input

Extract OpenPose joint positions from video or image files

positional arguments:
  input                 Input video or image file path

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        Output JSON file path (default: outputs/pose.json)
  --overlay-video OVERLAY_VIDEO
                        Create an overlay video with poses drawn (for video inputs only)
  --overlay-image OVERLAY_IMAGE
                        Create an overlay image with poses drawn (for image inputs only)
  --model-folder MODEL_FOLDER
                        OpenPose models folder path (uses OPENPOSEPATH if not specified)
  --net-resolution NET_RESOLUTION
                        Network input resolution (default: 368x368)
  --model-pose {COCO,MPI,MPI_4_layers}
                        Pose model to use (default: COCO)
  --scale-number SCALE_NUMBER
                        Number of scales to average (default: 1)
  --scale-gap SCALE_GAP
                        Scale gap between scales (default: 0.3)
  --confidence-threshold CONFIDENCE_THRESHOLD
                        Minimum confidence threshold for keypoints (default: 0.1)
  --show-confidence     Show confidence scores in visualizations
  --keypoint-radius KEYPOINT_RADIUS
                        Radius of keypoint circles in visualization (default: 4)
  --connection-thickness CONNECTION_THICKNESS
                        Thickness of connection lines in visualization (default: 2)
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Logging level (default: INFO)
  --log-file LOG_FILE   Log to file (in addition to console)
  --verbose, -v         Enable verbose logging
  --export-csv          Also export results to CSV format
  --extract-frames      Extract individual frame images with pose overlays (for video inputs only)
  --frame-range FRAME_RANGE
                        Frame range to extract (format: start:end, e.g., 10:50)
  --frames-directory FRAMES_DIRECTORY
                        Directory to save extracted frame images (default: {output_name}_frames)
  --extract-comprehensive-frames
                        Extract both raw frames and overlay frames to separate directories (for video inputs only)
  --frame-extraction-config FRAME_EXTRACTION_CONFIG
                        JSON file with frame extraction configuration
```

## Comprehensive Frame Extraction

The comprehensive frame extraction feature creates **two separate sets of outputs** for detailed analysis:

### 🎯 Output Structure

```
outputs/
├── pose_video_20250619_131354.json         # Pose detection data
├── pose_video_20250619_131354.csv          # CSV export
├── frames_video_20250619_131354/           # 📁 Raw frames directory
│   ├── frame_00000.jpg                     # Unprocessed frame 0
│   ├── frame_00001.jpg                     # Unprocessed frame 1
│   ├── frame_00002.jpg                     # Unprocessed frame 2
│   └── ...
├── overlay_video_20250619_131354/          # 📁 Overlay frames directory
│   ├── frame_00000.jpg                     # Frame 0 with pose overlays
│   ├── frame_00001.jpg                     # Frame 1 with pose overlays
│   ├── frame_00002.jpg                     # Frame 2 with pose overlays
│   └── ...
└── video_overlay_20250619_131354.mp4       # Video overlay (if requested)
```

### 🔧 Configuration Options

Create a frame extraction configuration file (`frame_config.json`):

```json
{
    "base_output_directory": "outputs",
    "directory_name_template": "{type}_{video_name}_{timestamp}",
    "frame_filename_template": "frame_{:05d}.{extension}",
    
    "extract_raw_frames": true,
    "raw_image_format": "jpg",
    "raw_image_quality": 95,
    "raw_resize_factor": null,
    
    "extract_overlay_frames": true,
    "overlay_image_format": "jpg", 
    "overlay_image_quality": 95,
    "overlay_resize_factor": null,
    
    "skeleton_color": [0, 255, 0],
    "joint_color": [255, 0, 0],
    "confidence_threshold": 0.1,
    "line_thickness": 2,
    "joint_radius": 4,
    "show_confidence": true,
    "show_person_id": true,
    "font_scale": 0.5,
    "font_color": [255, 255, 255],
    
    "frame_range": null,
    "frame_skip": 1,
    "enable_progress_callback": true,
    "log_extraction_details": true
}
```

### 📋 Use Cases

**Raw Frames Directory** (`frames_video_timestamp/`):
- 🔬 **Research & Analysis**: Unmodified frames for computer vision research
- 🎨 **Custom Processing**: Apply your own filters, annotations, or analyses
- 📊 **Dataset Creation**: Generate training/testing datasets
- 🔍 **Quality Control**: Manual inspection of original video content

**Overlay Frames Directory** (`overlay_video_timestamp/`):
- 📈 **Presentations**: High-quality individual frames for slides and reports
- 🎯 **Pose Analysis**: Frame-by-frame examination of pose detection results
- 🎬 **Documentation**: Create documentation with specific pose examples
- 🔧 **Debugging**: Verify pose detection accuracy on individual frames

### 🚀 Performance Features

- **Parallel Processing**: Raw and overlay extraction can run simultaneously
- **Memory Efficient**: Frame-by-frame processing without loading entire video
- **Progress Tracking**: Real-time progress updates for long videos
- **Error Isolation**: Individual frame failures don't stop the entire process
- **Configurable Quality**: Independent quality settings for raw vs overlay frames

### 💡 Example Workflows

**Research Workflow**:
```bash
# Extract high-quality raw frames for analysis
python src/video2pose.py research_video.mp4 \
    --extract-comprehensive-frames \
    --frame-extraction-config research_config.json \
    --frame-range 0:1000
```

**Presentation Workflow**:
```bash
# Extract specific frames with overlays for presentation
python src/video2pose.py presentation_video.mp4 \
    --extract-comprehensive-frames \
    --frame-range 50:100
```

**Quality Control Workflow**:
```bash
# Extract every 10th frame for quick review
python src/video2pose.py long_video.mp4 \
    --extract-comprehensive-frames \
    --frame-extraction-config quick_review_config.json
```

Where `quick_review_config.json` includes `"frame_skip": 10`.

## Output Format

### JSON Output Structure

```json
{
  "metadata": {
    "input_file": "input_video.mp4",
    "output_generated_at": "2024-01-15T10:30:00",
    "total_poses_detected": 150,
    "processing_info": {
      "model_pose": "COCO",
      "net_resolution": "368x368",
      "confidence_threshold": 0.1
    }
  },
  "summary": {
    "total_poses": 150,
    "total_frames": 100,
    "people_detected": 2,
    "frames_with_poses": 95,
    "average_poses_per_frame": 1.5
  },
  "poses": [
    {
      "person_id": 0,
      "frame_number": 0,
      "timestamp": 0.0,
      "confidence": 0.85,
      "joints": [
        {
          "name": "nose",
          "joint_id": 0,
          "keypoint": {
            "x": 320.5,
            "y": 240.3,
            "confidence": 0.9
          }
        }
      ]
    }
  ]
}
```

### CSV Output

**Automatically Generated**: A CSV file with timestamped filename is automatically generated alongside the JSON output.

The normalized CSV format includes one row per joint detection:
- `frame_number`: Frame number (0 for images)
- `timestamp`: Time in seconds (0.0 for images)
- `person_id`: ID of the detected person
- `joint_name`: Name of the joint (e.g., "nose", "left_shoulder")
- `joint_id`: OpenPose joint ID number
- `x`, `y`: Pixel coordinates of the joint
- `confidence`: Detection confidence score (0.0 to 1.0)
- `pose_confidence`: Overall pose detection confidence
- `total_joints`: Total number of joints detected for this pose

**Additional CSV Formats**: Use `--export-csv --csv-format all` to generate:
- **Wide format**: One row per pose with joints as columns
- **Summary format**: One row per person per frame with aggregate statistics and bounding boxes

## Architecture

The project follows SOLID principles and clean architecture patterns:

### Project Structure

```
src/posedetect/
├── __init__.py              # Package initialization
├── models/                  # Data models
│   ├── __init__.py
│   └── pose.py             # Pose, Joint, KeyPoint classes
├── core/                   # Core business logic
│   ├── __init__.py
│   ├── detector.py         # Main PoseDetector class
│   └── visualizer.py       # Pose visualization
├── utils/                  # Utility modules
│   ├── __init__.py
│   ├── file_handler.py     # File operations
│   ├── video_processor.py  # Video processing
│   ├── output_manager.py   # Output management
│   └── logging_config.py   # Logging configuration
└── cli/                    # Command-line interface
    ├── __init__.py
    └── main.py             # CLI implementation

tests/                      # Test suite
├── __init__.py
├── test_models.py          # Model tests
├── test_utils.py           # Utility tests
└── test_cli.py             # CLI tests
```

### Key Design Principles

1. **Single Responsibility**: Each class has one clear purpose
2. **Open/Closed**: Open for extension, closed for modification
3. **Liskov Substitution**: Proper inheritance hierarchies
4. **Interface Segregation**: Small, focused interfaces
5. **Dependency Inversion**: Depend on abstractions, not concretions

### Key Components

- **PoseDetector**: Main class for OpenPose integration and pose detection
- **PoseVisualizer**: Handles pose visualization and overlay creation
- **OutputManager**: Manages JSON/CSV output and result serialization
- **FileHandler**: Validates inputs and handles file operations
- **VideoProcessor**: Processes video files and extracts frames

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/posedetect

# Run specific test file
pytest tests/test_models.py

# Verbose output
pytest -v
```

### Test Coverage

The test suite includes:
- Unit tests for all data models
- Integration tests for core functionality
- CLI argument parsing and validation tests
- Utility function tests
- Error handling and edge case tests

## Development

### Setting up Development Environment

1. Install development dependencies:
```bash
pip install -e ".[dev]"
```

2. Run linting:
```bash
black src/ tests/
flake8 src/ tests/
mypy src/
```

3. Run tests:
```bash
pytest --cov=src/posedetect
```

### Contributing

1. Follow the existing code style and architecture patterns
2. Add comprehensive tests for new functionality
3. Update documentation as needed
4. Ensure all tests pass and code quality checks succeed

## Error Handling

The application includes comprehensive error handling:

- **Input Validation**: Validates file existence and format support
- **OpenPose Errors**: Graceful handling of OpenPose initialization failures
- **Processing Errors**: Robust error handling during video/image processing
- **Output Errors**: Proper handling of file I/O errors

## Logging

Configurable logging with loguru:

- **Console Logging**: Colored output with configurable levels
- **File Logging**: Optional file output with rotation
- **Verbose Mode**: Detailed logging for debugging
- **Performance Tracking**: Processing time and frame rate logging

## Supported Formats

### Input Formats

**Images**: JPG, JPEG, PNG, BMP, TIFF, TIF
**Videos**: MP4, AVI, MOV, MKV, FLV, WMV, WEBM

### Output Formats

- **JSON**: Structured data with metadata and pose information
- **CSV**: Tabular format for data analysis
- **Overlay Videos**: MP4 videos with pose annotations
- **Overlay Images**: Images with pose annotations

## Performance Considerations

- **Memory Management**: Efficient video processing with frame-by-frame iteration
- **GPU Support**: Leverages OpenPose GPU acceleration when available
- **Batch Processing**: Optimized for processing multiple frames
- **Resource Cleanup**: Proper cleanup of OpenPose resources

## Troubleshooting

### Quick Diagnosis

If you encounter OpenPose import errors, run the built-in diagnostic:

```bash
# Quick diagnosis
python src/video2pose.py --debug-openpose

# Or run the comprehensive diagnostic tool
python tools/diagnose_openpose.py

# Or use the setup helper
python setup_openpose.py
```

### Common Issues

1. **OpenPose Import Error**:
   ```
   Error: No module named 'openpose'
   ```
   
   **Solutions:**
   - Ensure OPENPOSEPATH environment variable is set correctly
   - Verify OpenPose Python bindings are compiled and installed
   - Run diagnostic: `python src/video2pose.py --debug-openpose`
   - Use setup helper: `python setup_openpose.py`

1.5. **DLL Load Failed (Windows)**:
   ```
   ImportError: DLL load failed: The specified module could not be found.
   ```
   
   **Most Common Cause**: OpenPose DLL dependencies not found in Windows PATH
   
   **Solutions:**
   - **Quick Fix**: Add OpenPose bin directory to PATH:
     ```cmd
     set PATH=%PATH%;C:\path\to\openpose\bin
     ```
   - **Permanent Fix**: Add to system PATH via Environment Variables
   - **Test Fix**: Run `python test_openpose_import.py` to verify
   - The application now automatically adds DLL paths, but manual setup may be needed

2. **OPENPOSEPATH Not Set**:
   ```
   EnvironmentError: OPENPOSEPATH environment variable not set
   ```
   
   **Solutions:**
   - Windows: `set OPENPOSEPATH=C:\path\to\openpose` or `$env:OPENPOSEPATH="C:\path\to\openpose"`
   - Linux/Mac: `export OPENPOSEPATH=/path/to/openpose`
   - Add to your shell profile for permanent setup

3. **OpenPose Models Not Found**:
   ```
   OpenPose models folder not found
   ```
   
   **Solutions:**
   - Ensure the `models` directory exists in your OpenPose installation
   - Download models from the OpenPose repository if missing
   - Check OPENPOSEPATH points to the correct directory

4. **Video Processing Issues**:
   - Verify video file is not corrupted
   - Check video codec compatibility with OpenCV
   - Ensure sufficient disk space for output

5. **Low Detection Accuracy**:
   - Try higher net resolution (e.g., `--net-resolution 656x368`)
   - Adjust confidence threshold (`--confidence-threshold 0.5`)
   - Ensure good lighting and video quality

### Diagnostic Tools

#### 1. Built-in Diagnostic
```bash
python src/video2pose.py --debug-openpose
```
Quick diagnostic integrated into the main application.

#### 2. Comprehensive Diagnostic
```bash
python tools/diagnose_openpose.py
```
Detailed analysis of your OpenPose installation including:
- Environment variable verification
- Directory structure scanning
- Module detection and testing
- Import testing with different configurations

#### 3. Setup Helper
```bash
# Interactive setup
python setup_openpose.py

# Auto-detect installations
python setup_openpose.py detect

# Test current setup
python setup_openpose.py test
```

### Debug Mode

Enable debug logging for detailed troubleshooting:
```bash
python src/video2pose.py input.mp4 --log-level DEBUG --verbose
```

This will show:
- Detailed OpenPose path detection
- Module loading attempts
- Processing progress information
- Error stack traces

### Windows-Specific Issues

1. **Path Separators**: Use forward slashes or escape backslashes in paths
2. **Python Bindings**: Ensure you have the Release or Debug build with Python support
3. **Visual C++ Redistributables**: May be required for OpenPose to work
4. **Architecture Mismatch**: Ensure OpenPose architecture (x64/x86) matches your Python

### Environment Setup Examples

#### Windows PowerShell
```powershell
# Temporary (current session)
$env:OPENPOSEPATH = "C:\Users\username\dev\ambient\openpose"

# Permanent (current user)
[Environment]::SetEnvironmentVariable("OPENPOSEPATH", "C:\Users\username\dev\ambient\openpose", "User")
```

#### Windows Command Prompt
```cmd
# Temporary (current session)
set OPENPOSEPATH=C:\Users\username\dev\ambient\openpose

# Permanent (system-wide) - requires admin
setx OPENPOSEPATH "C:\Users\username\dev\ambient\openpose" /M
```

#### Linux/Mac
```bash
# Temporary (current session)
export OPENPOSEPATH=/home/username/openpose

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export OPENPOSEPATH=/home/username/openpose' >> ~/.bashrc
source ~/.bashrc
```

## License

MIT License

## Acknowledgments

- CMU Perceptual Computing Lab for OpenPose
- Contributors and maintainers of the dependencies used in this project
