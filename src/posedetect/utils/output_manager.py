"""
Output management utilities for pose detection results.

This module provides utilities for managing output files, JSON serialization,
CSV export, video overlay generation, and result formatting with proper error handling.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from loguru import logger

from ..models.pose import Pose
from ..exporters.csv_exporter import CSVExporter, CSVFormat
from ..video.overlay_generator import VideoOverlayGenerator, OverlayConfig
from ..video.frame_extraction import FrameExtractionManager, FrameExtractionConfig


class OutputManager:
    """
    Manages output operations for pose detection results.
    
    This class handles JSON serialization, CSV export, video overlay generation,
    file writing, and result formatting following the Single Responsibility Principle.
    """
    
    def __init__(self, output_path: Path):
        """
        Initialize the output manager.
        
        Args:
            output_path: Path where output will be written
        """
        self.output_path = output_path
        self.results: List[Pose] = []
        self._input_video_path: Optional[Path] = None
        
    def add_pose(self, pose: Pose) -> None:
        """
        Add a pose result to the collection.
        
        Args:
            pose: Pose object to add
        """
        self.results.append(pose)
        logger.debug(f"Added pose for person {pose.person_id}, frame {pose.frame_number}")
    
    def add_poses(self, poses: List[Pose]) -> None:
        """
        Add multiple pose results to the collection.
        
        Args:
            poses: List of Pose objects to add
        """
        self.results.extend(poses)
        logger.debug(f"Added {len(poses)} poses to results")
    
    def clear_results(self) -> None:
        """Clear all stored results."""
        self.results.clear()
        logger.debug("Cleared all pose results")
    
    def get_results_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the pose detection results.
        
        Returns:
            Dictionary containing results summary
        """
        if not self.results:
            return {
                'total_poses': 0,
                'total_frames': 0,
                'people_detected': 0,
                'frames_with_poses': 0
            }
        
        frames_with_poses = set()
        people_ids = set()
        
        for pose in self.results:
            if pose.frame_number is not None:
                frames_with_poses.add(pose.frame_number)
            people_ids.add(pose.person_id)
        
        return {
            'total_poses': len(self.results),
            'total_frames': max((p.frame_number for p in self.results if p.frame_number), default=0) + 1,
            'people_detected': len(people_ids),
            'frames_with_poses': len(frames_with_poses),
            'average_poses_per_frame': len(self.results) / len(frames_with_poses) if frames_with_poses else 0
        }
    
    def create_output_data(self, 
                          input_file: str, 
                          processing_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create the complete output data structure.
        
        Args:
            input_file: Path to the input file that was processed
            processing_metadata: Optional metadata about the processing
            
        Returns:
            Complete output data dictionary
        """
        output_data = {
            'metadata': {
                'input_file': input_file,
                'output_generated_at': datetime.now().isoformat(),
                'total_poses_detected': len(self.results),
                'processing_info': processing_metadata or {}
            },
            'summary': self.get_results_summary(),
            'poses': [pose.to_dict() for pose in self.results]
        }
        
        return output_data
    
    def save_json(self, 
                  input_file: str, 
                  processing_metadata: Optional[Dict[str, Any]] = None,
                  indent: int = 2) -> None:
        """
        Save pose detection results to JSON file.
        
        Args:
            input_file: Path to the input file that was processed
            processing_metadata: Optional metadata about the processing
            indent: JSON indentation level
            
        Raises:
            OSError: If file cannot be written
        """
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        output_data = self.create_output_data(input_file, processing_metadata)
        
        try:
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=indent, ensure_ascii=False)
            
            logger.info(f"Saved {len(self.results)} poses to {self.output_path}")
            logger.info(f"Results summary: {self.get_results_summary()}")
            
        except OSError as e:
            logger.error(f"Failed to save output file: {e}")
            raise
    
    def load_json(self) -> List[Pose]:
        """
        Load pose detection results from JSON file.
        
        Returns:
            List of Pose objects
            
        Raises:
            FileNotFoundError: If output file doesn't exist
            json.JSONDecodeError: If JSON is invalid
        """
        if not self.output_path.exists():
            raise FileNotFoundError(f"Output file not found: {self.output_path}")
        
        try:
            with open(self.output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            poses = [Pose.from_dict(pose_data) for pose_data in data['poses']]
            self.results = poses
            
            logger.info(f"Loaded {len(poses)} poses from {self.output_path}")
            return poses
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in output file: {e}")
            raise
        except KeyError as e:
            logger.error(f"Missing required field in JSON: {e}")
            raise
    
    def export_csv(self, csv_path: Optional[Path] = None) -> Path:
        """
        Export pose results to CSV format.
        
        Args:
            csv_path: Optional path for CSV file. If None, uses same name as JSON with .csv extension
            
        Returns:
            Path to the created CSV file
        """
        if csv_path is None:
            csv_path = self.output_path.with_suffix('.csv')
        
        # This could be extended to use pandas for better CSV handling
        # For now, we'll create a simple CSV with basic pose information
        
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(csv_path, 'w', encoding='utf-8') as f:
            # Write header
            f.write("frame_number,timestamp,person_id,joint_name,x,y,confidence\n")
            
            # Write data
            for pose in self.results:
                for joint in pose.joints:
                    f.write(f"{pose.frame_number or 0},"
                           f"{pose.timestamp or 0.0},"
                           f"{pose.person_id},"
                           f"{joint.name},"
                           f"{joint.keypoint.x},"
                           f"{joint.keypoint.y},"
                           f"{joint.keypoint.confidence}\n")
        
        logger.info(f"Exported pose data to CSV: {csv_path}")
        return csv_path
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the results (alias for get_results_summary).
        
        Returns:
            Dictionary containing results summary
        """
        return self.get_results_summary()
    
    def set_input_video_path(self, video_path: Union[str, Path]) -> None:
        """
        Set the path to the input video for overlay generation.
        
        Args:
            video_path: Path to the input video file
        """
        self._input_video_path = Path(video_path)
        logger.debug(f"Set input video path: {self._input_video_path}")
    
    def export_csv_advanced(
        self, 
        csv_path: Optional[Path] = None,
        format_type: CSVFormat = CSVFormat.NORMALIZED,
        include_metadata: bool = True
    ) -> Path:
        """
        Export pose results to CSV format using the advanced CSV exporter.
        
        Args:
            csv_path: Optional path for CSV file. If None, uses same name as JSON with .csv extension
            format_type: CSV format type (normalized, wide, or summary)
            include_metadata: Whether to include metadata in the CSV
            
        Returns:
            Path to the created CSV file
            
        Raises:
            ValueError: If no poses are available to export
        """
        if not self.results:
            raise ValueError("No poses available to export")
        
        if csv_path is None:
            base_name = self.output_path.stem
            suffix = f"_{format_type.value}" if format_type != CSVFormat.NORMALIZED else ""
            csv_path = self.output_path.parent / f"{base_name}{suffix}.csv"
        
        csv_exporter = CSVExporter(format_type)
        csv_exporter.export_poses(self.results, csv_path, include_metadata)
        
        logger.info(f"Exported {len(self.results)} poses to {csv_path} ({format_type.value} format)")
        return csv_path
    
    def export_all_csv_formats(self, base_path: Optional[Path] = None) -> Dict[str, Path]:
        """
        Export poses in all available CSV formats.
        
        Args:
            base_path: Base path for CSV files. If None, uses output_path directory
            
        Returns:
            Dictionary mapping format names to file paths
            
        Raises:
            ValueError: If no poses are available to export
        """
        if not self.results:
            raise ValueError("No poses available to export")
        
        if base_path is None:
            base_path = self.output_path.parent / self.output_path.stem
        
        exported_files = {}
        
        for format_type in CSVFormat:
            csv_path = base_path.parent / f"{base_path.name}_{format_type.value}.csv"
            exported_path = self.export_csv_advanced(csv_path, format_type)
            exported_files[format_type.value] = exported_path
        
        logger.info(f"Exported poses in {len(exported_files)} CSV formats")
        return exported_files
    
    def generate_overlay_video(
        self,
        output_video_path: Optional[Path] = None,
        config: Optional[OverlayConfig] = None,
        progress_callback: Optional[callable] = None
    ) -> Path:
        """
        Generate overlay video with pose visualizations.
        
        Args:
            output_video_path: Path for output video. If None, uses output_path with .mp4 extension
            config: Configuration for overlay generation
            progress_callback: Optional callback for progress updates
            
        Returns:
            Path to the generated overlay video
            
        Raises:
            ValueError: If no poses or input video path available
            FileNotFoundError: If input video doesn't exist
        """
        if not self.results:
            raise ValueError("No poses available for overlay generation")
        
        if self._input_video_path is None:
            raise ValueError("Input video path not set. Call set_input_video_path() first")
        
        if not self._input_video_path.exists():
            raise FileNotFoundError(f"Input video not found: {self._input_video_path}")
        
        if output_video_path is None:
            output_video_path = self.output_path.with_suffix('.mp4')
        
        # Ensure output directory exists
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create overlay generator
        overlay_generator = VideoOverlayGenerator(config)
        
        # Generate overlay video
        overlay_generator.generate_overlay_video(
            input_video_path=self._input_video_path,
            poses_data=self.results,
            output_video_path=output_video_path,
            progress_callback=progress_callback
        )
        
        logger.info(f"Generated overlay video: {output_video_path}")
        return output_video_path

    def generate_frame_overlays(
        self,
        output_frames_directory: Optional[Path] = None,
        config: Optional[OverlayConfig] = None,
        frame_range: Optional[tuple] = None,
        progress_callback: Optional[callable] = None
    ) -> List[Path]:
        """
        Generate individual frame images with pose overlays.
        
        Args:
            output_frames_directory: Directory for frame images. If None, uses output_path with _frames suffix
            config: Configuration for overlay generation
            frame_range: Optional tuple (start_frame, end_frame) to limit extraction
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of paths to generated frame images
            
        Raises:
            ValueError: If no poses or input video path available
            FileNotFoundError: If input video doesn't exist
        """
        if not self.results:
            raise ValueError("No poses available for frame overlay generation")
        
        if self._input_video_path is None:
            raise ValueError("Input video path not set. Call set_input_video_path() first")
        
        if not self._input_video_path.exists():
            raise FileNotFoundError(f"Input video not found: {self._input_video_path}")
        
        if output_frames_directory is None:
            # Create frames directory next to output file
            base_name = self.output_path.stem
            output_frames_directory = self.output_path.parent / f"{base_name}_frames"
        
        # Ensure output directory exists
        output_frames_directory.mkdir(parents=True, exist_ok=True)
        
        # Create overlay generator
        overlay_generator = VideoOverlayGenerator(config)
        
        # Generate frame overlays
        generated_files = overlay_generator.generate_frame_overlays(
            input_video_path=self._input_video_path,
            poses_data=self.results,
            output_directory=output_frames_directory,
            frame_range=frame_range,
            progress_callback=progress_callback
        )
        
        logger.info(f"Generated {len(generated_files)} frame overlays in: {output_frames_directory}")
        return generated_files

    def generate_comprehensive_frame_extractions(
        self,
        frame_config: Optional[FrameExtractionConfig] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive frame extractions including both raw and overlay frames.
        
        This method creates two separate directories:
        - Raw frames: Unprocessed video frames
        - Overlay frames: Frames with pose overlays
        
        Args:
            frame_config: Configuration for frame extraction
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with extraction results and paths
            
        Raises:
            ValueError: If no poses or input video path available
            FileNotFoundError: If input video doesn't exist
        """
        if not self.results:
            raise ValueError("No poses available for frame extraction")
        
        if self._input_video_path is None:
            raise ValueError("Input video path not set. Call set_input_video_path() first")
        
        if not self._input_video_path.exists():
            raise FileNotFoundError(f"Input video not found: {self._input_video_path}")
        
        # Use default config if none provided
        if frame_config is None:
            frame_config = FrameExtractionConfig(
                base_output_directory=str(self.output_path.parent),
                extract_raw_frames=True,
                extract_overlay_frames=True
            )
        
        # Create frame extraction manager
        extraction_manager = FrameExtractionManager(frame_config)
        
        # Enhanced progress callback that handles different extraction phases
        def enhanced_progress_callback(progress: float, frame: int, total: int, phase: str):
            if progress_callback:
                progress_callback(progress, frame, total, phase)
            
            # Log progress at key intervals
            if int(progress * 100) % 10 == 0:  # Every 10%
                logger.info(f"{phase.title()} extraction progress: {progress:.1%} ({frame}/{total})")
        
        try:
            # Extract both raw and overlay frames
            extraction_results = extraction_manager.extract_all_frame_types(
                video_path=self._input_video_path,
                poses=self.results,
                base_output_directory=self.output_path.parent,
                progress_callback=enhanced_progress_callback if frame_config.enable_progress_callback else None
            )
            
            # Generate summary
            summary = extraction_manager.get_extraction_summary(extraction_results)
            
            # Log results
            logger.info("Comprehensive frame extraction completed:")
            logger.info(f"  Raw frames: {summary['total_raw_frames']}")
            logger.info(f"  Overlay frames: {summary['total_overlay_frames']}")
            logger.info(f"  Output directories: {list(summary['output_directories'].keys())}")
            
            # Add summary to results
            extraction_results['summary'] = summary
            
            return extraction_results
            
        except Exception as e:
            logger.error(f"Comprehensive frame extraction failed: {e}")
            raise
    
    def export_all_formats(
        self,
        input_file: str,
        processing_metadata: Optional[Dict[str, Any]] = None,
        include_csv: bool = True,
        include_video: bool = False,
        include_frames: bool = False,
        include_comprehensive_frames: bool = False,
        csv_formats: Optional[List[CSVFormat]] = None,
        overlay_config: Optional[OverlayConfig] = None,
        frame_config: Optional[FrameExtractionConfig] = None,
        frame_range: Optional[tuple] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Export results in all requested formats.
        
        Args:
            input_file: Path to the input file that was processed
            processing_metadata: Optional metadata about the processing
            include_csv: Whether to generate CSV files
            include_video: Whether to generate overlay video
            include_frames: Whether to generate individual frame overlay images
            include_comprehensive_frames: Whether to generate both raw and overlay frame directories
            csv_formats: List of CSV formats to generate (defaults to all)
            overlay_config: Configuration for video overlay
            frame_config: Configuration for comprehensive frame extraction
            frame_range: Optional tuple (start_frame, end_frame) for frame extraction
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with paths to all generated files
            
        Raises:
            ValueError: If no poses are available to export
        """
        if not self.results:
            raise ValueError("No poses available to export")
        
        exported_files = {
            'json': None,
            'csv': {},
            'video': None,
            'frames': [],
            'comprehensive_frames': {}
        }
        
        # Export JSON
        self.save_json(input_file, processing_metadata)
        exported_files['json'] = self.output_path
        
        # Export CSV formats
        if include_csv:
            if csv_formats is None:
                csv_formats = list(CSVFormat)
            
            for format_type in csv_formats:
                try:
                    csv_path = self.export_csv_advanced(format_type=format_type)
                    exported_files['csv'][format_type.value] = csv_path
                except Exception as e:
                    logger.warning(f"Failed to export CSV format {format_type.value}: {e}")
        
        # Export overlay video
        if include_video:
            try:
                if self._input_video_path is not None:
                    video_path = self.generate_overlay_video(
                        config=overlay_config,
                        progress_callback=progress_callback
                    )
                    exported_files['video'] = video_path
                else:
                    logger.warning("Cannot generate overlay video: input video path not set")
            except Exception as e:
                logger.warning(f"Failed to generate overlay video: {e}")
        
        # Export frame overlays
        if include_frames:
            try:
                if self._input_video_path is not None:
                    
                    def frame_progress_callback(progress: float, frame: int, total: int):
                        if progress_callback:
                            # Adjust progress for frame extraction phase
                            progress_callback(progress, frame, total)
                    
                    frame_files = self.generate_frame_overlays(
                        config=overlay_config,
                        frame_range=frame_range,
                        progress_callback=frame_progress_callback
                    )
                    exported_files['frames'] = frame_files
                else:
                    logger.warning("Cannot generate frame overlays: input video path not set")
            except Exception as e:
                logger.warning(f"Failed to generate frame overlays: {e}")
        
        # Export comprehensive frame extractions (raw + overlay frames)
        if include_comprehensive_frames:
            try:
                if self._input_video_path is not None:
                    
                    def comprehensive_progress_callback(progress: float, frame: int, total: int, phase: str = "frames"):
                        if progress_callback:
                            # Adjust progress for comprehensive extraction phase
                            progress_callback(progress, frame, total, phase)
                    
                    # Set up frame extraction config with frame range if provided
                    if frame_config is None:
                        frame_config = FrameExtractionConfig(
                            base_output_directory=str(self.output_path.parent),
                            frame_range=frame_range,
                            extract_raw_frames=True,
                            extract_overlay_frames=True
                        )
                    elif frame_range is not None:
                        # Update existing config with frame range
                        frame_config.frame_range = frame_range
                    
                    comprehensive_results = self.generate_comprehensive_frame_extractions(
                        frame_config=frame_config,
                        progress_callback=comprehensive_progress_callback
                    )
                    exported_files['comprehensive_frames'] = comprehensive_results
                else:
                    logger.warning("Cannot generate comprehensive frame extractions: input video path not set")
            except Exception as e:
                logger.warning(f"Failed to generate comprehensive frame extractions: {e}")
        
        logger.info(f"Exported results in multiple formats: {len(exported_files)} types")
        return exported_files
    
    def get_export_summary(self) -> Dict[str, Any]:
        """
        Get a summary of available export options and file information.
        
        Returns:
            Dictionary with export information
        """
        summary = {
            'poses_count': len(self.results),
            'output_path': str(self.output_path),
            'input_video_path': str(self._input_video_path) if self._input_video_path else None,
            'available_csv_formats': CSVExporter.get_available_formats(),
            'video_overlay_supported': self._input_video_path is not None,
            'results_summary': self.get_results_summary()
        }
        
        return summary 