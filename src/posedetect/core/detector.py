"""
Core pose detection functionality using OpenPose.

This module contains the main PoseDetector class that interfaces with the
OpenPose library to detect human poses in images and videos.
"""

import os
import sys
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from loguru import logger

from ..models.pose import Pose, Joint, KeyPoint, COCO_JOINT_NAMES, BODY_25_JOINT_NAMES
from ..utils.video_processor import VideoProcessor


class PoseDetector:
    """
    Main pose detection class using OpenPose.
    
    This class handles the initialization of OpenPose and provides methods
    for detecting poses in images and videos following SOLID principles.
    """
    
    def __init__(self, 
                 model_folder: Optional[str] = None,
                 net_resolution: str = "368x368",
                 output_resolution: Optional[str] = None,
                 model_pose: str = "COCO",
                 scale_number: int = 1,
                 scale_gap: float = 0.3):
        """
        Initialize the pose detector.
        
        Args:
            model_folder: Path to OpenPose models folder
            net_resolution: Network input resolution (e.g., "368x368")
            output_resolution: Output resolution (if None, uses input resolution)
            model_pose: Pose model to use ("COCO", "MPI", etc.)
            scale_number: Number of scales to average
            scale_gap: Scale gap between scales
        """
        self.model_folder = model_folder or self._get_default_model_folder()
        self.net_resolution = net_resolution
        self.output_resolution = output_resolution
        self.model_pose = model_pose
        self.scale_number = scale_number
        self.scale_gap = scale_gap
        
        self.op_wrapper = None
        self._is_initialized = False
        
        logger.info(f"PoseDetector initialized with model: {self.model_pose}")
    
    def _get_default_model_folder(self) -> str:
        """
        Get the default OpenPose models folder from environment variable.
        
        Returns:
            Path to OpenPose models folder
            
        Raises:
            EnvironmentError: If OPENPOSEPATH is not set
        """
        openpose_path = os.environ.get('OPENPOSEPATH')
        if not openpose_path:
            raise EnvironmentError(
                "OPENPOSEPATH environment variable not set. "
                "Please set it to point to your OpenPose installation directory."
            )
        
        models_folder = os.path.join(openpose_path, 'models')
        if not os.path.exists(models_folder):
            raise FileNotFoundError(f"OpenPose models folder not found: {models_folder}")
        
        return models_folder
    
    def _setup_windows_dll_path(self, openpose_path: str) -> None:
        """
        Setup Windows PATH environment variable for OpenPose DLL dependencies.
        
        Args:
            openpose_path: Path to OpenPose installation directory
        """
        # List of directories that might contain OpenPose DLLs
        dll_paths = [
            # Main bin directory (most common for precompiled versions)
            os.path.join(openpose_path, 'bin'),
            
            # Alternative locations for DLLs
            os.path.join(openpose_path, 'build', 'bin'),
            os.path.join(openpose_path, 'build', 'x64', 'Release'),
            os.path.join(openpose_path, 'build', 'x64', 'Debug'),
            os.path.join(openpose_path, 'x64', 'Release'),
            os.path.join(openpose_path, 'x64', 'Debug'),
            
            # 3rdparty dependencies (sometimes needed)
            os.path.join(openpose_path, '3rdparty', 'windows', 'opencv', 'x64', 'vc15', 'bin'),
            os.path.join(openpose_path, '3rdparty', 'windows', 'caffe', 'bin'),
            os.path.join(openpose_path, '3rdparty', 'windows', 'caffe3rdparty', 'bin'),
            
            # Root directory (in case DLLs are directly there)
            openpose_path,
        ]
        
        # Get current PATH
        current_path = os.environ.get('PATH', '')
        path_entries = current_path.split(os.pathsep) if current_path else []
        
        # Add existing DLL directories to PATH
        added_paths = []
        for dll_path in dll_paths:
            if os.path.exists(dll_path) and dll_path not in path_entries:
                path_entries.insert(0, dll_path)  # Insert at beginning for priority
                added_paths.append(dll_path)
                logger.debug(f"Added to Windows PATH: {dll_path}")
        
        if added_paths:
            # Update the PATH environment variable
            new_path = os.pathsep.join(path_entries)
            os.environ['PATH'] = new_path
            logger.info(f"Updated Windows PATH with {len(added_paths)} OpenPose directories")
            
            # Log which DLL files we can find
            for path in added_paths:
                try:
                    dll_files = [f for f in os.listdir(path) if f.endswith('.dll')]
                    if dll_files:
                        logger.debug(f"Found {len(dll_files)} DLL files in {path}")
                        for dll in sorted(dll_files)[:5]:  # Log first 5 DLLs
                            logger.debug(f"  {dll}")
                        if len(dll_files) > 5:
                            logger.debug(f"  ... and {len(dll_files) - 5} more")
                except (OSError, PermissionError):
                    pass
        else:
            logger.warning("No OpenPose DLL directories found to add to PATH")
    
    def _setup_openpose_path(self) -> None:
        """Add OpenPose Python bindings to the system path and setup DLL paths."""
        openpose_path = os.environ.get('OPENPOSEPATH')
        if not openpose_path:
            raise EnvironmentError("OPENPOSEPATH environment variable not set")
        
        logger.info(f"OpenPose path from environment: {openpose_path}")
        
        # Verify OPENPOSEPATH exists
        if not os.path.exists(openpose_path):
            raise EnvironmentError(f"OPENPOSEPATH directory does not exist: {openpose_path}")
        
        # Setup Windows PATH for DLL dependencies (on Windows)
        if sys.platform.startswith('win'):
            self._setup_windows_dll_path(openpose_path)
        
        # List of possible OpenPose Python module locations (in order of preference)
        possible_paths = [
            # Windows precompiled binaries (most common)
            os.path.join(openpose_path, 'bin', 'python', 'openpose', 'Release'),
            os.path.join(openpose_path, 'bin', 'python', 'openpose', 'Debug'),
            os.path.join(openpose_path, 'python', 'openpose', 'Release'),
            os.path.join(openpose_path, 'python', 'openpose', 'Debug'),
            
            # Build directory locations
            os.path.join(openpose_path, 'build', 'python', 'openpose', 'Release'),
            os.path.join(openpose_path, 'build', 'python', 'openpose', 'Debug'),
            os.path.join(openpose_path, 'build', 'python'),
            
            # Direct python directory
            os.path.join(openpose_path, 'python'),
            
            # Alternative locations
            os.path.join(openpose_path, 'python', 'dist'),
            os.path.join(openpose_path, 'python', 'openpose'),
            
            # Root directory (in case modules are directly there)
            openpose_path,
        ]
        
        found_paths = []
        openpose_module_found = False
        
        # Check each possible path
        for path in possible_paths:
            if os.path.exists(path):
                found_paths.append(path)
                logger.debug(f"Found OpenPose directory: {path}")
                
                # Check if openpose module files exist in this path
                module_files = [
                    'openpose.py',
                    'openpose.pyd',  # Windows compiled module
                    'openpose.so',   # Linux compiled module
                    '_openpose.pyd', # Alternative Windows naming
                    '_openpose.so',  # Alternative Linux naming
                    'pyopenpose.py', # Alternative naming
                    'pyopenpose.pyd', # Alternative Windows naming
                    'pyopenpose.so',  # Alternative Linux naming
                ]
                
                # Also check for Python version-specific .pyd files
                python_version = f"cp{sys.version_info.major}{sys.version_info.minor}"
                versioned_modules = [
                    f'pyopenpose.{python_version}-win_amd64.pyd',
                    f'openpose.{python_version}-win_amd64.pyd',
                ]
                
                # Check for any .pyd files with version numbers (more flexible)
                try:
                    for file in os.listdir(path):
                        if file.startswith(('pyopenpose.cp', 'openpose.cp')) and file.endswith('.pyd'):
                            versioned_modules.append(file)
                except OSError:
                    pass
                
                all_module_files = module_files + versioned_modules
                
                for module_file in all_module_files:
                    module_path = os.path.join(path, module_file)
                    if os.path.exists(module_path):
                        logger.info(f"Found OpenPose module: {module_path}")
                        openpose_module_found = True
                        
                        # Add this path to sys.path if not already there
                        if path not in sys.path:
                            sys.path.insert(0, path)  # Insert at beginning for priority
                            logger.info(f"Added to Python path: {path}")
                        break
                
                if openpose_module_found:
                    break
        
        # Additional debugging: scan python directory structure
        python_dir = os.path.join(openpose_path, 'python')
        if os.path.exists(python_dir):
            logger.debug(f"Contents of {python_dir}:")
            try:
                for item in os.listdir(python_dir):
                    item_path = os.path.join(python_dir, item)
                    if os.path.isdir(item_path):
                        logger.debug(f"  Directory: {item}")
                        # Check subdirectories too
                        try:
                            for subitem in os.listdir(item_path):
                                if subitem.endswith(('.py', '.pyd', '.so')):
                                    logger.debug(f"    File: {subitem}")
                        except PermissionError:
                            logger.debug(f"    [Permission denied to list contents]")
                    elif item.endswith(('.py', '.pyd', '.so')):
                        logger.debug(f"  File: {item}")
            except PermissionError:
                logger.debug("  [Permission denied to list contents]")
        
        if not openpose_module_found:
            error_msg = f"""
OpenPose Python module not found in any expected location.

OPENPOSEPATH: {openpose_path}
Searched in these directories:
{chr(10).join(f"  - {path} {'(exists)' if os.path.exists(path) else '(not found)'}" for path in possible_paths)}

To fix this issue:
1. Verify OpenPose is properly compiled with Python bindings
2. Check if openpose.py or openpose.pyd exists in the python directory
3. On Windows, ensure you have the Release or Debug build with Python bindings
4. You may need to rebuild OpenPose with Python support enabled

For manual setup, you can also set the exact path by adding the directory 
containing openpose.py/openpose.pyd to your PYTHONPATH environment variable.
"""
            raise EnvironmentError(error_msg.strip())
        
        logger.info("OpenPose Python path setup completed successfully")
    
    def initialize(self) -> None:
        """
        Initialize the OpenPose wrapper.
        
        Raises:
            ImportError: If OpenPose cannot be imported
            RuntimeError: If OpenPose initialization fails
        """
        if self._is_initialized:
            logger.warning("PoseDetector already initialized")
            return
        
        try:
            # Setup OpenPose paths
            self._setup_openpose_path()
            
            # Try to import OpenPose (must be done after path setup)
            op = None
            import_error = None
            
            # Try different import patterns
            try:
                import openpose as op
                logger.info("Successfully imported 'openpose'")
            except ImportError as e:
                import_error = e
                try:
                    import pyopenpose as op
                    logger.info("Successfully imported 'pyopenpose'")
                except ImportError as e2:
                    # Provide detailed error message
                    error_msg = f"""
Failed to import OpenPose Python module.

Primary error (openpose): {e}
Secondary error (pyopenpose): {e2}

This could be due to:
1. Python version mismatch - OpenPose module may be compiled for a different Python version
2. Missing dependencies - Required DLLs may not be found
3. Architecture mismatch - Ensure Python and OpenPose are both 64-bit or 32-bit

Current Python version: {sys.version}
Detected OpenPose module: Check diagnostic output for available .pyd files
"""
                    logger.error(error_msg.strip())
                    raise ImportError("Could not import OpenPose Python module") from e2
            
            if op is None:
                raise ImportError("Failed to import any OpenPose module")
            
            # Check if COCO model exists, fallback to BODY_25 if missing
            actual_model_pose = self.model_pose
            if self.model_pose == "COCO":
                coco_model_path = os.path.join(self.model_folder, "pose", "coco", "pose_iter_440000.caffemodel")
                if not os.path.exists(coco_model_path):
                    logger.warning(f"COCO model file not found: {coco_model_path}")
                    logger.info("Automatically switching to BODY_25 model (already available)")
                    actual_model_pose = "BODY_25"
            
            # Use MINIMAL OpenPose parameters - same as working test
            params = {
                "model_folder": self.model_folder,
                "model_pose": actual_model_pose,
                "net_resolution": self.net_resolution,
            }
            
            logger.info(f"OpenPose configuration: {params}")
            
            if self.output_resolution:
                params["output_resolution"] = self.output_resolution
            
            # Initialize OpenPose wrapper
            opWrapper = op.WrapperPython()
            opWrapper.configure(params)
            opWrapper.start()
            
            self.op_wrapper = opWrapper
            self._is_initialized = True
            self.actual_model_pose = actual_model_pose  # Store the model being used
            
            logger.info(f"OpenPose initialized successfully with {actual_model_pose} model")
            
        except ImportError as e:
            logger.error(f"Failed to import OpenPose: {e}")
            logger.error("Make sure OpenPose is properly installed and OPENPOSEPATH is set correctly")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize OpenPose: {e}")
            raise RuntimeError(f"OpenPose initialization failed: {e}")
    
    def _ensure_initialized(self) -> None:
        """Ensure the detector is initialized."""
        if not self._is_initialized:
            self.initialize()
    
    def detect_poses_in_image(self, image: np.ndarray) -> List[Pose]:
        """
        Detect poses in a single image.
        
        Args:
            image: Input image as numpy array (BGR format)
            
        Returns:
            List of detected Pose objects
            
        Raises:
            RuntimeError: If OpenPose processing fails
        """
        self._ensure_initialized()
        
        if not self._is_initialized or self.op_wrapper is None:
            raise RuntimeError("OpenPose is not properly initialized")
        
        try:
            # Try to import the module that was successfully imported during initialization
            op = None
            try:
                import openpose as op
            except ImportError:
                try:
                    import pyopenpose as op
                except ImportError:
                    raise ImportError("OpenPose module not available after initialization")
            
            # Create OpenPose datum
            datum = op.Datum()
            datum.cvInputData = image
            
            logger.debug(f"Processing image of shape: {image.shape}")
            
            # Process image
            self.op_wrapper.emplaceAndPop(op.VectorDatum([datum]))
            
            # Extract pose data
            poses = []
            if datum.poseKeypoints is not None:
                logger.debug(f"OpenPose keypoints shape: {datum.poseKeypoints.shape}")
                if len(datum.poseKeypoints.shape) >= 2:
                    poses = self._convert_openpose_output(datum.poseKeypoints)
                else:
                    logger.warning(f"Unexpected keypoints shape: {datum.poseKeypoints.shape}")
            else:
                logger.debug("No keypoints detected by OpenPose")
            
            logger.debug(f"Detected {len(poses)} poses in image")
            return poses
            
        except ImportError as e:
            logger.error(f"OpenPose import error during detection: {e}")
            raise RuntimeError(f"OpenPose import failed: {e}")
        except Exception as e:
            logger.error(f"Error detecting poses in image: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            # For critical errors, we should fail rather than continue silently
            if "initialization" in str(e).lower() or "import" in str(e).lower():
                raise RuntimeError(f"Critical OpenPose error: {e}")
            # For processing errors, log but continue (return empty list)
            logger.warning("Continuing with empty pose detection for this frame")
            return []
    
    def detect_poses_in_video(self, video_path: Path) -> List[Pose]:
        """
        Detect poses in all frames of a video.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            List of detected Pose objects from all frames
            
        Raises:
            RuntimeError: If OpenPose or video processing fails
        """
        self._ensure_initialized()
        
        if not self._is_initialized or self.op_wrapper is None:
            raise RuntimeError("OpenPose is not properly initialized for video processing")
        
        all_poses = []
        frames_processed = 0
        frames_with_errors = 0
        
        try:
            with VideoProcessor(video_path) as video_proc:
                metadata = video_proc.get_metadata()
                logger.info(f"Processing video: {metadata['frame_count']} frames at {metadata['fps']} FPS")
                
                for frame_number, timestamp, frame in video_proc.iterate_frames():
                    try:
                        frame_poses = self.detect_poses_in_image(frame)
                        
                        # Add frame information to poses
                        for pose in frame_poses:
                            pose.frame_number = frame_number
                            pose.timestamp = timestamp
                        
                        all_poses.extend(frame_poses)
                        frames_processed += 1
                        
                        if frame_number % 30 == 0:  # Log every 30 frames
                            logger.info(f"Processed frame {frame_number}/{metadata['frame_count']} - Poses: {len(frame_poses)}")
                    
                    except RuntimeError as e:
                        # Critical errors should stop processing
                        logger.error(f"Critical error on frame {frame_number}: {e}")
                        raise
                    except Exception as e:
                        # Non-critical errors: log and continue
                        logger.warning(f"Error processing frame {frame_number}: {e}")
                        frames_with_errors += 1
                        # Continue processing other frames
                
                logger.info(f"Video processing complete:")
                logger.info(f"  - Frames processed: {frames_processed}")
                logger.info(f"  - Frames with errors: {frames_with_errors}")
                logger.info(f"  - Total poses detected: {len(all_poses)}")
                
                # If no frames were processed at all, that's a critical error
                if frames_processed == 0:
                    raise RuntimeError(f"No frames were successfully processed from video {video_path}")
                
        except RuntimeError:
            # Re-raise runtime errors (critical failures)
            raise
        except Exception as e:
            logger.error(f"Error processing video: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            raise RuntimeError(f"Video processing failed: {e}")
        
        return all_poses
    
    def _convert_openpose_output(self, pose_keypoints: np.ndarray) -> List[Pose]:
        """
        Convert OpenPose output to Pose objects.
        
        Args:
            pose_keypoints: OpenPose keypoints array
            
        Returns:
            List of Pose objects
        """
        poses = []
        
        logger.debug(f"Converting OpenPose output with shape: {pose_keypoints.shape}")
        logger.debug(f"Data type: {pose_keypoints.dtype}")
        logger.debug(f"Min/Max values: {np.min(pose_keypoints):.3f} / {np.max(pose_keypoints):.3f}")
        
        # pose_keypoints shape: [num_people, num_keypoints, 3] where 3 = (x, y, confidence)
        for person_id in range(pose_keypoints.shape[0]):
            person_keypoints = pose_keypoints[person_id]
            
            logger.debug(f"Processing person {person_id} with {person_keypoints.shape[0]} keypoints")
            
            # Create joints from keypoints
            joints = []
            total_confidence = 0.0
            valid_joints = 0
            confidence_counts = {0.0: 0, 0.01: 0, 0.1: 0, 0.3: 0}
            
            for joint_id in range(person_keypoints.shape[0]):
                x, y, confidence = person_keypoints[joint_id]
                
                # Count confidence levels for debugging
                for thresh in confidence_counts.keys():
                    if confidence > thresh:
                        confidence_counts[thresh] += 1
                
                # Include all joints with any confidence (like working test)
                if confidence > 0:  # Accept any non-zero confidence
                    # Use correct joint names mapping based on model
                    joint_names = BODY_25_JOINT_NAMES if getattr(self, 'actual_model_pose', 'COCO') == 'BODY_25' else COCO_JOINT_NAMES
                    joint_name = joint_names.get(joint_id, f"joint_{joint_id}")
                    keypoint = KeyPoint(x=float(x), y=float(y), confidence=float(confidence))
                    joint = Joint(name=joint_name, keypoint=keypoint, joint_id=joint_id)
                    joints.append(joint)
                    
                    total_confidence += confidence
                    valid_joints += 1
                    
                    # Log first few keypoints for debugging
                    if valid_joints <= 3:
                        logger.debug(f"  Joint {joint_id} ({joint_name}): ({x:.1f}, {y:.1f}, conf={confidence:.4f})")
            
            logger.debug(f"Person {person_id} confidence distribution: {confidence_counts}")
            logger.debug(f"Person {person_id} valid joints: {valid_joints}")
            
            # Create pose if we have ANY valid joints (like working test)
            if valid_joints > 0:
                avg_confidence = total_confidence / valid_joints if valid_joints > 0 else 0.0
                pose = Pose(
                    joints=joints,
                    person_id=person_id,
                    confidence=avg_confidence
                )
                poses.append(pose)
                logger.debug(f"Created pose for person {person_id} with {len(joints)} joints, avg confidence: {avg_confidence:.4f}")
            else:
                logger.debug(f"Skipped person {person_id}: no valid joints found")
        
        logger.debug(f"Total poses created: {len(poses)}")
        return poses
    
    def get_pose_with_overlay(self, image: np.ndarray) -> Tuple[List[Pose], np.ndarray]:
        """
        Detect poses and return both poses and image with overlay.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Tuple of (poses, image_with_overlay)
        """
        self._ensure_initialized()
        
        try:
            # Try to import the module that was successfully imported during initialization
            op = None
            try:
                import openpose as op
            except ImportError:
                try:
                    import pyopenpose as op
                except ImportError:
                    raise ImportError("OpenPose module not available")
            
            datum = op.Datum()
            datum.cvInputData = image
            
            # Process image
            self.op_wrapper.emplaceAndPop(op.VectorDatum([datum]))
            
            # Extract poses
            poses = []
            if datum.poseKeypoints is not None and len(datum.poseKeypoints.shape) >= 2:
                poses = self._convert_openpose_output(datum.poseKeypoints)
            
            # Get rendered image (if available)
            rendered_image = datum.cvOutputData if datum.cvOutputData is not None else image
            
            return poses, rendered_image
            
        except Exception as e:
            logger.error(f"Error detecting poses with overlay: {e}")
            return [], image
    
    def cleanup(self) -> None:
        """Clean up OpenPose resources."""
        if hasattr(self, 'op_wrapper') and self.op_wrapper:
            try:
                self.op_wrapper.stop()
                logger.info("OpenPose wrapper stopped")
            except Exception as e:
                logger.warning(f"Error stopping OpenPose wrapper: {e}")
        
        self._is_initialized = False
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
    
    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup() 