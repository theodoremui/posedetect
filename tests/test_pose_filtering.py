"""
Tests for pose filtering functionality.

This module tests the pose filtering utilities that remove frames/poses 
with no valid detections.
"""

import pytest
from src.posedetect.models.pose import Pose, Joint, KeyPoint
from src.posedetect.utils.pose_filter import (
    has_valid_pose,
    filter_poses_by_validity,
    get_frames_with_valid_poses,
    group_poses_by_frame_filtered,
    get_filtering_summary
)


def create_test_pose(person_id: int = 0, frame_number: int = 0, joint_confidences: list = None) -> Pose:
    """Create a test pose with specified joint confidences."""
    if joint_confidences is None:
        joint_confidences = [0.8, 0.7, 0.6]  # Default valid confidences
    
    joints = []
    joint_names = ['nose', 'left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']
    
    for i, confidence in enumerate(joint_confidences):
        if i < len(joint_names):
            joint = Joint(
                name=joint_names[i],
                keypoint=KeyPoint(x=100 + i * 10, y=200 + i * 10, confidence=confidence),
                joint_id=i
            )
            joints.append(joint)
    
    pose = Pose(
        joints=joints,
        person_id=person_id,
        frame_number=frame_number,
        confidence=sum(joint_confidences) / len(joint_confidences) if joint_confidences else 0.0
    )
    
    return pose


class TestPoseValidation:
    """Test pose validation functions."""
    
    def test_has_valid_pose_with_valid_joints(self):
        """Test that poses with valid joints are detected as valid."""
        pose = create_test_pose(joint_confidences=[0.8, 0.7, 0.6])
        assert has_valid_pose(pose, confidence_threshold=0.1, min_valid_joints=1)
        assert has_valid_pose(pose, confidence_threshold=0.5, min_valid_joints=2)
    
    def test_has_valid_pose_with_invalid_joints(self):
        """Test that poses with only invalid joints are detected as invalid."""
        pose = create_test_pose(joint_confidences=[0.05, 0.03, 0.02])
        assert not has_valid_pose(pose, confidence_threshold=0.1, min_valid_joints=1)
    
    def test_has_valid_pose_with_mixed_joints(self):
        """Test poses with mix of valid and invalid joints."""
        pose = create_test_pose(joint_confidences=[0.8, 0.05, 0.02])
        assert has_valid_pose(pose, confidence_threshold=0.1, min_valid_joints=1)
        assert not has_valid_pose(pose, confidence_threshold=0.1, min_valid_joints=2)
    
    def test_has_valid_pose_empty_joints(self):
        """Test that poses with no joints are invalid."""
        pose = Pose(joints=[], person_id=0)
        assert not has_valid_pose(pose)
    
    def test_has_valid_pose_threshold_boundary(self):
        """Test pose validation at confidence threshold boundaries."""
        pose = create_test_pose(joint_confidences=[0.1, 0.099, 0.101])
        
        # Exactly at threshold should be valid
        assert has_valid_pose(pose, confidence_threshold=0.1, min_valid_joints=1)
        assert has_valid_pose(pose, confidence_threshold=0.1, min_valid_joints=2)
        
        # Just below threshold should be invalid
        assert not has_valid_pose(pose, confidence_threshold=0.102, min_valid_joints=1)


class TestPoseFiltering:
    """Test pose filtering functions."""
    
    def test_filter_poses_by_validity_keeps_valid(self):
        """Test that valid poses are kept in filtering."""
        poses = [
            create_test_pose(person_id=0, frame_number=0, joint_confidences=[0.8, 0.7]),
            create_test_pose(person_id=1, frame_number=1, joint_confidences=[0.6, 0.5]),
        ]
        
        filtered = filter_poses_by_validity(poses, confidence_threshold=0.1)
        assert len(filtered) == 2
        assert all(pose in filtered for pose in poses)
    
    def test_filter_poses_by_validity_removes_invalid(self):
        """Test that invalid poses are removed in filtering."""
        poses = [
            create_test_pose(person_id=0, frame_number=0, joint_confidences=[0.8, 0.7]),  # Valid
            create_test_pose(person_id=1, frame_number=1, joint_confidences=[0.05, 0.03]),  # Invalid
            create_test_pose(person_id=2, frame_number=2, joint_confidences=[0.6, 0.5]),  # Valid
        ]
        
        filtered = filter_poses_by_validity(poses, confidence_threshold=0.1)
        assert len(filtered) == 2
        assert filtered[0].person_id == 0
        assert filtered[1].person_id == 2
    
    def test_filter_poses_by_validity_empty_list(self):
        """Test filtering with empty pose list."""
        filtered = filter_poses_by_validity([], confidence_threshold=0.1)
        assert len(filtered) == 0
    
    def test_filter_poses_by_validity_all_invalid(self):
        """Test filtering when all poses are invalid."""
        poses = [
            create_test_pose(person_id=0, frame_number=0, joint_confidences=[0.05, 0.03]),
            create_test_pose(person_id=1, frame_number=1, joint_confidences=[0.02, 0.01]),
        ]
        
        filtered = filter_poses_by_validity(poses, confidence_threshold=0.1)
        assert len(filtered) == 0


class TestFrameFiltering:
    """Test frame-based filtering functions."""
    
    def test_get_frames_with_valid_poses(self):
        """Test getting frame numbers with valid poses."""
        poses = [
            create_test_pose(person_id=0, frame_number=5, joint_confidences=[0.8, 0.7]),   # Valid
            create_test_pose(person_id=1, frame_number=10, joint_confidences=[0.05, 0.03]), # Invalid
            create_test_pose(person_id=2, frame_number=15, joint_confidences=[0.6, 0.5]),   # Valid
            create_test_pose(person_id=3, frame_number=5, joint_confidences=[0.4, 0.3]),    # Valid (same frame as first)
        ]
        
        valid_frames = get_frames_with_valid_poses(poses, confidence_threshold=0.1)
        assert valid_frames == {5, 15}
    
    def test_get_frames_with_valid_poses_empty(self):
        """Test getting valid frames from empty pose list."""
        valid_frames = get_frames_with_valid_poses([], confidence_threshold=0.1)
        assert len(valid_frames) == 0
    
    def test_group_poses_by_frame_filtered(self):
        """Test grouping poses by frame with filtering."""
        poses = [
            create_test_pose(person_id=0, frame_number=5, joint_confidences=[0.8, 0.7]),   # Valid
            create_test_pose(person_id=1, frame_number=5, joint_confidences=[0.6, 0.5]),   # Valid (same frame)
            create_test_pose(person_id=2, frame_number=10, joint_confidences=[0.05, 0.03]), # Invalid
            create_test_pose(person_id=3, frame_number=15, joint_confidences=[0.4, 0.3]),   # Valid
        ]
        
        grouped = group_poses_by_frame_filtered(poses, confidence_threshold=0.1)
        
        # Should have frames 5 and 15, but not 10
        assert set(grouped.keys()) == {5, 15}
        assert len(grouped[5]) == 2  # Two valid poses in frame 5
        assert len(grouped[15]) == 1  # One valid pose in frame 15
        
        # Check person IDs
        frame_5_person_ids = {pose.person_id for pose in grouped[5]}
        assert frame_5_person_ids == {0, 1}


class TestFilteringSummary:
    """Test filtering summary functions."""
    
    def test_get_filtering_summary(self):
        """Test generating filtering summary statistics."""
        original_poses = [
            create_test_pose(person_id=0, frame_number=5, joint_confidences=[0.8, 0.7]),   # Valid
            create_test_pose(person_id=1, frame_number=10, joint_confidences=[0.05, 0.03]), # Invalid
            create_test_pose(person_id=2, frame_number=15, joint_confidences=[0.6, 0.5]),   # Valid
            create_test_pose(person_id=3, frame_number=20, joint_confidences=[0.02, 0.01]), # Invalid
        ]
        
        filtered_poses = filter_poses_by_validity(original_poses, confidence_threshold=0.1)
        summary = get_filtering_summary(original_poses, filtered_poses)
        
        assert summary['original_poses'] == 4
        assert summary['filtered_poses'] == 2
        assert summary['removed_poses'] == 2
        assert summary['original_frames'] == 4
        assert summary['filtered_frames'] == 2
        assert summary['removed_frames'] == 2
        assert summary['pose_retention_rate'] == 50.0
        assert summary['frame_retention_rate'] == 50.0
    
    def test_get_filtering_summary_no_filtering(self):
        """Test summary when no poses are filtered out."""
        poses = [
            create_test_pose(person_id=0, frame_number=5, joint_confidences=[0.8, 0.7]),
            create_test_pose(person_id=1, frame_number=10, joint_confidences=[0.6, 0.5]),
        ]
        
        summary = get_filtering_summary(poses, poses)  # Same list
        
        assert summary['original_poses'] == 2
        assert summary['filtered_poses'] == 2
        assert summary['removed_poses'] == 0
        assert summary['pose_retention_rate'] == 100.0
        assert summary['frame_retention_rate'] == 100.0
    
    def test_get_filtering_summary_empty_original(self):
        """Test summary with empty original pose list."""
        summary = get_filtering_summary([], [])
        
        assert summary['original_poses'] == 0
        assert summary['filtered_poses'] == 0
        assert summary['removed_poses'] == 0
        assert summary['pose_retention_rate'] == 0
        assert summary['frame_retention_rate'] == 0 