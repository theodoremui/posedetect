# CSV Export and Video Overlay Design Documentation

## Overview

This document describes the design and implementation of the CSV export and video overlay functionality added to the pose detection system. The implementation follows best software engineering practices with modular design, comprehensive testing, and clear separation of concerns.

## Architecture

### 1. Module Structure

```
src/posedetect/
├── exporters/
│   ├── __init__.py
│   └── csv_exporter.py         # CSV export functionality
├── video/
│   ├── __init__.py
│   └── overlay_generator.py    # Video overlay generation
├── utils/
│   └── output_manager.py       # Enhanced with multi-format export
└── cli/
    └── main.py                 # Updated CLI with new options
```

### 2. Design Principles

- **Single Responsibility Principle**: Each module has a specific, well-defined purpose
- **Open/Closed Principle**: Extensible design allows adding new export formats
- **Dependency Inversion**: Components depend on abstractions, not concretions
- **DRY (Don't Repeat Yourself)**: Common functionality is shared and reusable
- **Modular Design**: Clear interfaces between components

## Components

### 1. CSV Exporter (`src/posedetect/exporters/csv_exporter.py`)

#### Purpose
Converts pose detection data into CSV format with multiple layout options for different analysis needs.

#### Features
- **Three CSV Formats**:
  - `NORMALIZED`: One row per joint detection (best for data analysis)
  - `WIDE`: One row per pose with joints as columns (compact format)
  - `SUMMARY`: One row per person per frame with aggregate statistics

#### Key Classes

```python
class CSVFormat(Enum):
    """Supported CSV output formats."""
    NORMALIZED = "normalized"
    WIDE = "wide"
    SUMMARY = "summary"

class CSVExporter:
    """Export pose detection data to CSV format."""
    
    def __init__(self, format_type: CSVFormat = CSVFormat.NORMALIZED)
    def export_poses(self, poses: List[Pose], output_path: Path, include_metadata: bool = True)
```

#### Design Decisions

1. **Enum-based Format Selection**: Type-safe format specification
2. **Configurable Metadata**: Optional inclusion of additional statistics
3. **Unicode Support**: Proper encoding for international characters
4. **Bounding Box Calculation**: Automatic calculation of pose bounding boxes
5. **Error Handling**: Comprehensive validation and error reporting

#### Usage Examples

```python
# Normalized format (default)
exporter = CSVExporter(CSVFormat.NORMALIZED)
exporter.export_poses(poses, "output_normalized.csv")

# Wide format
exporter = CSVExporter(CSVFormat.WIDE)
exporter.export_poses(poses, "output_wide.csv", include_metadata=False)

# Summary format with bounding boxes
exporter = CSVExporter(CSVFormat.SUMMARY)
exporter.export_poses(poses, "output_summary.csv")
```

### 2. Video Overlay Generator (`src/posedetect/video/overlay_generator.py`)

#### Purpose
Creates video overlays by combining original video frames with pose detection visualizations.

#### Features
- **Configurable Visualization**: Colors, thickness, confidence thresholds
- **Progress Tracking**: Callback support for progress monitoring
- **Multiple Input Formats**: Supports pose data as objects or JSON files
- **Frame Synchronization**: Proper mapping between video frames and pose data
- **Error Recovery**: Robust handling of missing frames or corrupted data

#### Key Classes

```python
@dataclass
class OverlayConfig:
    """Configuration for video overlay generation."""
    output_codec: str = 'mp4v'
    skeleton_color: Tuple[int, int, int] = (0, 255, 0)
    joint_color: Tuple[int, int, int] = (255, 0, 0)
    confidence_threshold: float = 0.1
    # ... additional configuration options

class VideoOverlayGenerator:
    """Generate video overlays with pose detection results."""
    
    def __init__(self, config: Optional[OverlayConfig] = None)
    def generate_overlay_video(self, input_video_path, poses_data, output_video_path, progress_callback)
```

#### Design Decisions

1. **Dataclass Configuration**: Type-safe, readable configuration
2. **OpenCV Integration**: Leverages OpenCV for video processing
3. **Memory Efficiency**: Frame-by-frame processing to handle large videos
4. **Flexible Input**: Accepts both pose objects and JSON file paths
5. **Visualization Hierarchy**: Skeleton connections, joints, then text overlays

#### Usage Examples

```python
# Basic overlay generation
config = OverlayConfig(
    skeleton_color=(0, 255, 0),
    confidence_threshold=0.5
)
generator = VideoOverlayGenerator(config)

def progress_callback(progress, frame, total):
    print(f"Progress: {progress:.1%}")

generator.generate_overlay_video(
    input_video_path="input.mp4",
    poses_data=poses,
    output_video_path="overlay.mp4",
    progress_callback=progress_callback
)
```

### 3. Enhanced Output Manager (`src/posedetect/utils/output_manager.py`)

#### Purpose
Coordinates multi-format export operations and manages output file generation.

#### New Features
- **Multi-format Export**: JSON, CSV (all formats), and video overlays
- **Video Path Management**: Tracks input video for overlay generation
- **Batch Operations**: Export all formats with single command
- **Export Summary**: Provides overview of available export options

#### Key Methods

```python
class OutputManager:
    def set_input_video_path(self, video_path: Path)
    def export_csv_advanced(self, format_type: CSVFormat, include_metadata: bool = True)
    def export_all_csv_formats(self) -> Dict[str, Path]
    def generate_overlay_video(self, config: OverlayConfig, progress_callback)
    def export_all_formats(self, include_csv: bool, include_video: bool) -> Dict[str, Any]
    def get_export_summary() -> Dict[str, Any]
```

#### Design Decisions

1. **Centralized Coordination**: Single point for managing all export operations
2. **Optional Features**: Graceful degradation when components unavailable
3. **Progress Reporting**: Consistent progress callback interface
4. **Error Isolation**: Individual format failures don't break entire export
5. **Metadata Integration**: Consistent metadata handling across formats

### 4. Enhanced CLI (`src/posedetect/cli/main.py`)

#### New Options

```bash
# CSV export options
--export-csv                    # Enable CSV export
--csv-format {normalized,wide,summary,all}  # Specify CSV format
--export-all-formats           # Export all available formats

# Video overlay options
--overlay-config CONFIG.json   # JSON configuration file for overlays
```

#### Usage Examples

```bash
# Export to all CSV formats
python -m posedetect video.mp4 --export-csv --csv-format all

# Export all formats with video overlay
python -m posedetect video.mp4 --export-all-formats

# Custom overlay configuration
python -m posedetect video.mp4 --overlay-video output.mp4 --overlay-config config.json
```

## Configuration

### Overlay Configuration Example

```json
{
    "output_codec": "XVID",
    "output_fps": 30.0,
    "skeleton_color": [255, 0, 0],
    "joint_color": [0, 255, 0],
    "confidence_threshold": 0.3,
    "line_thickness": 3,
    "joint_radius": 5,
    "show_confidence": true,
    "show_person_id": true,
    "font_scale": 0.6,
    "resize_factor": 0.8
}
```

## Testing Strategy

### 1. Unit Tests

- **CSV Exporter Tests** (`tests/test_exporters.py`):
  - Format validation
  - Data integrity
  - Unicode support
  - Error handling
  - Bounding box calculation

- **Video Overlay Tests** (`tests/test_video_overlay.py`):
  - Configuration validation
  - Frame processing
  - Video I/O mocking
  - Progress callbacks
  - Error scenarios

- **Output Manager Tests** (`tests/test_enhanced_output_manager.py`):
  - Multi-format coordination
  - Path management
  - Export summaries
  - Integration testing

### 2. Integration Tests

- End-to-end workflow testing
- CLI argument validation
- File format compatibility
- Performance benchmarking

### 3. Mock Testing

- OpenCV operations mocked for consistent testing
- Video file I/O simulation
- Progress callback verification
- Error injection testing

## Performance Considerations

### 1. Memory Management

- **Frame-by-Frame Processing**: Videos processed one frame at a time
- **Lazy Loading**: Pose data loaded only when needed
- **Resource Cleanup**: Proper disposal of video capture objects

### 2. Video Processing Optimization

- **Codec Selection**: Configurable codecs for size/quality tradeoffs
- **Frame Skipping**: Optional frame skipping for faster processing
- **Resize Support**: Automatic frame resizing to reduce processing load

### 3. CSV Export Efficiency

- **Streaming Write**: Large datasets written incrementally
- **Memory-Efficient Formats**: Wide format optimized for memory usage
- **Batch Operations**: Multiple formats generated in single pass

## Error Handling

### 1. Graceful Degradation

```python
# Example: Export continues even if video overlay fails
try:
    video_path = output_manager.generate_overlay_video(config=overlay_config)
    exported_files['video'] = video_path
except Exception as e:
    logger.warning(f"Failed to generate overlay video: {e}")
    exported_files['video'] = None
```

### 2. Validation

- Input validation for all file paths
- Format validation for configuration
- Data validation for pose objects
- Progress callback validation

### 3. Recovery

- Automatic fallback to default configurations
- Partial export completion when possible
- Detailed error reporting for debugging

## Future Extensions

### 1. Additional Export Formats

- XML export support
- YAML export support
- Database export integration
- Protocol buffer support

### 2. Advanced Video Features

- Multi-track video support
- Audio preservation
- Video metadata embedding
- Time-lapse generation

### 3. Visualization Enhancements

- 3D pose visualization
- Heatmap overlays
- Motion trails
- Confidence visualization

## Best Practices for Usage

### 1. Performance

```python
# Use appropriate CSV format for your needs
exporter = CSVExporter(CSVFormat.SUMMARY)  # For statistical analysis
exporter = CSVExporter(CSVFormat.NORMALIZED)  # For detailed analysis
```

### 2. Memory Management

```python
# Process large videos with progress tracking
def progress_callback(progress, frame, total):
    if frame % 100 == 0:  # Log every 100 frames
        logger.info(f"Processed {frame}/{total} frames")

output_manager.generate_overlay_video(progress_callback=progress_callback)
```

### 3. Error Handling

```python
# Always check export results
try:
    exported_files = output_manager.export_all_formats(
        input_file="video.mp4",
        include_csv=True,
        include_video=True
    )
    
    if exported_files['video'] is None:
        logger.warning("Video overlay generation failed")
    
except ValueError as e:
    logger.error(f"Export failed: {e}")
```

## Conclusion

The CSV export and video overlay functionality provides a comprehensive, modular solution for pose detection data export and visualization. The design emphasizes:

- **Modularity**: Clear separation of concerns
- **Extensibility**: Easy addition of new formats
- **Robustness**: Comprehensive error handling
- **Performance**: Efficient processing of large datasets
- **Usability**: Simple, intuitive interfaces

This implementation serves as a solid foundation for future enhancements while maintaining backward compatibility and ease of use. 