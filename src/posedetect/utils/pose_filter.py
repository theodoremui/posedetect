"""
Pose filtering utilities for removing frames/poses with no valid detections.

This module provides functions to filter pose detection results, removing
frames where no poses are detected or poses with insufficient valid joints.
"""

from typing import List, Dict, Any, Optional, Set
from loguru import logger

from ..models.pose import Pose


def has_valid_pose(pose: Pose, confidence_threshold: float = 0.1, min_valid_joints: int = 1) -> bool:
    """
    Check if a pose has valid detections.
    
    Args:
        pose: Pose object to check
        confidence_threshold: Minimum confidence for a joint to be considered valid
        min_valid_joints: Minimum number of valid joints required
        
    Returns:
        True if pose has sufficient valid joints, False otherwise
    """
    if not pose.joints:
        return False
    
    valid_joints = sum(
        1 for joint in pose.joints 
        if joint.keypoint.confidence >= confidence_threshold
    )
    
    return valid_joints >= min_valid_joints


def filter_poses_by_validity(
    poses: List[Pose], 
    confidence_threshold: float = 0.1, 
    min_valid_joints: int = 1
) -> List[Pose]:
    """
    Filter poses keeping only those with valid detections.
    
    Args:
        poses: List of poses to filter
        confidence_threshold: Minimum confidence for a joint to be considered valid
        min_valid_joints: Minimum number of valid joints required
        
    Returns:
        List of poses with valid detections
    """
    if not poses:
        return []
    
    original_count = len(poses)
    
    valid_poses = [
        pose for pose in poses 
        if has_valid_pose(pose, confidence_threshold, min_valid_joints)
    ]
    
    filtered_count = len(valid_poses)
    removed_count = original_count - filtered_count
    
    logger.info(f"Pose filtering results:")
    logger.info(f"  Original poses: {original_count}")
    logger.info(f"  Valid poses: {filtered_count}")
    logger.info(f"  Removed poses: {removed_count}")
    
    if removed_count > 0:
        percentage_removed = (removed_count / original_count) * 100
        logger.info(f"  Filtered out: {percentage_removed:.1f}% of poses")
    
    return valid_poses


def get_frames_with_valid_poses(
    poses: List[Pose], 
    confidence_threshold: float = 0.1, 
    min_valid_joints: int = 1
) -> Set[int]:
    """
    Get set of frame numbers that contain valid poses.
    
    Args:
        poses: List of poses to analyze
        confidence_threshold: Minimum confidence for a joint to be considered valid
        min_valid_joints: Minimum number of valid joints required
        
    Returns:
        Set of frame numbers with valid poses
    """
    valid_frames = set()
    
    for pose in poses:
        if has_valid_pose(pose, confidence_threshold, min_valid_joints):
            frame_number = getattr(pose, 'frame_number', 0)
            if frame_number is not None:
                valid_frames.add(frame_number)
    
    return valid_frames


def group_poses_by_frame_filtered(
    poses: List[Pose], 
    confidence_threshold: float = 0.1, 
    min_valid_joints: int = 1
) -> Dict[int, List[Pose]]:
    """
    Group poses by frame number, including only frames with valid poses.
    
    Args:
        poses: List of poses to group
        confidence_threshold: Minimum confidence for a joint to be considered valid
        min_valid_joints: Minimum number of valid joints required
        
    Returns:
        Dictionary mapping frame numbers to lists of valid poses
    """
    poses_by_frame = {}
    total_frames = 0
    
    for pose in poses:
        if has_valid_pose(pose, confidence_threshold, min_valid_joints):
            frame_number = getattr(pose, 'frame_number', 0)
            if frame_number is not None:
                if frame_number not in poses_by_frame:
                    poses_by_frame[frame_number] = []
                poses_by_frame[frame_number].append(pose)
            total_frames += 1
    
    logger.info(f"Grouped {total_frames} valid poses into {len(poses_by_frame)} frames")
    return poses_by_frame


def get_filtering_summary(
    original_poses: List[Pose], 
    filtered_poses: List[Pose]
) -> Dict[str, Any]:
    """
    Generate a summary of pose filtering results.
    
    Args:
        original_poses: Original pose list before filtering
        filtered_poses: Pose list after filtering
        
    Returns:
        Dictionary with filtering statistics
    """
    original_count = len(original_poses)
    filtered_count = len(filtered_poses)
    removed_count = original_count - filtered_count
    
    # Count unique frames
    original_frames = set()
    filtered_frames = set()
    
    for pose in original_poses:
        frame_number = getattr(pose, 'frame_number', 0)
        if frame_number is not None:
            original_frames.add(frame_number)
    
    for pose in filtered_poses:
        frame_number = getattr(pose, 'frame_number', 0)
        if frame_number is not None:
            filtered_frames.add(frame_number)
    
    original_frame_count = len(original_frames)
    filtered_frame_count = len(filtered_frames)
    removed_frame_count = original_frame_count - filtered_frame_count
    
    return {
        'original_poses': original_count,
        'filtered_poses': filtered_count,
        'removed_poses': removed_count,
        'original_frames': original_frame_count,
        'filtered_frames': filtered_frame_count,
        'removed_frames': removed_frame_count,
        'pose_retention_rate': (filtered_count / original_count) * 100 if original_count > 0 else 0,
        'frame_retention_rate': (filtered_frame_count / original_frame_count) * 100 if original_frame_count > 0 else 0
    } 