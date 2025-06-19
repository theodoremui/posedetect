"""
Tests for pose detection data models.

This module contains comprehensive tests for the Pose, Joint, and KeyPoint
data models including serialization and deserialization.
"""

import pytest
import json
from typing import List

from src.posedetect.models.pose import Pose, Joint, KeyPoint, COCO_JOINT_NAMES


class TestKeyPoint:
    """Test cases for KeyPoint class."""
    
    def test_keypoint_creation(self):
        """Test KeyPoint creation with valid data."""
        kp = KeyPoint(x=100.5, y=200.3, confidence=0.8)
        assert kp.x == 100.5
        assert kp.y == 200.3
        assert kp.confidence == 0.8
    
    def test_keypoint_to_dict(self):
        """Test KeyPoint serialization to dictionary."""
        kp = KeyPoint(x=100.5, y=200.3, confidence=0.8)
        expected = {"x": 100.5, "y": 200.3, "confidence": 0.8}
        assert kp.to_dict() == expected
    
    def test_keypoint_from_dict(self):
        """Test KeyPoint deserialization from dictionary."""
        data = {"x": 100.5, "y": 200.3, "confidence": 0.8}
        kp = KeyPoint.from_dict(data)
        assert kp.x == 100.5
        assert kp.y == 200.3
        assert kp.confidence == 0.8
    
    def test_keypoint_edge_cases(self):
        """Test KeyPoint with edge case values."""
        # Zero confidence
        kp = KeyPoint(x=0.0, y=0.0, confidence=0.0)
        assert kp.confidence == 0.0
        
        # Maximum confidence
        kp = KeyPoint(x=1920.0, y=1080.0, confidence=1.0)
        assert kp.confidence == 1.0


class TestJoint:
    """Test cases for Joint class."""
    
    def test_joint_creation(self):
        """Test Joint creation with valid data."""
        kp = KeyPoint(x=100.5, y=200.3, confidence=0.8)
        joint = Joint(name="nose", keypoint=kp, joint_id=0)
        assert joint.name == "nose"
        assert joint.joint_id == 0
        assert joint.keypoint == kp
    
    def test_joint_to_dict(self):
        """Test Joint serialization to dictionary."""
        kp = KeyPoint(x=100.5, y=200.3, confidence=0.8)
        joint = Joint(name="nose", keypoint=kp, joint_id=0)
        
        expected = {
            "name": "nose",
            "joint_id": 0,
            "keypoint": {"x": 100.5, "y": 200.3, "confidence": 0.8}
        }
        assert joint.to_dict() == expected
    
    def test_joint_from_dict(self):
        """Test Joint deserialization from dictionary."""
        data = {
            "name": "nose",
            "joint_id": 0,
            "keypoint": {"x": 100.5, "y": 200.3, "confidence": 0.8}
        }
        joint = Joint.from_dict(data)
        assert joint.name == "nose"
        assert joint.joint_id == 0
        assert joint.keypoint.x == 100.5


class TestPose:
    """Test cases for Pose class."""
    
    def create_sample_pose(self) -> Pose:
        """Create a sample pose for testing."""
        joints = [
            Joint("nose", KeyPoint(100.0, 50.0, 0.9), 0),
            Joint("left_eye", KeyPoint(90.0, 45.0, 0.8), 1),
            Joint("right_eye", KeyPoint(110.0, 45.0, 0.8), 2),
        ]
        return Pose(joints=joints, person_id=0, frame_number=10, timestamp=0.5)
    
    def test_pose_creation(self):
        """Test Pose creation with valid data."""
        pose = self.create_sample_pose()
        assert len(pose.joints) == 3
        assert pose.person_id == 0
        assert pose.frame_number == 10
        assert pose.timestamp == 0.5
    
    def test_get_joint_by_name(self):
        """Test getting joint by name."""
        pose = self.create_sample_pose()
        nose_joint = pose.get_joint_by_name("nose")
        assert nose_joint is not None
        assert nose_joint.name == "nose"
        assert nose_joint.joint_id == 0
        
        # Test non-existent joint
        invalid_joint = pose.get_joint_by_name("invalid")
        assert invalid_joint is None
    
    def test_get_joint_by_id(self):
        """Test getting joint by ID."""
        pose = self.create_sample_pose()
        nose_joint = pose.get_joint_by_id(0)
        assert nose_joint is not None
        assert nose_joint.name == "nose"
        
        # Test non-existent joint ID
        invalid_joint = pose.get_joint_by_id(99)
        assert invalid_joint is None
    
    def test_get_keypoints_array(self):
        """Test getting keypoints as array."""
        pose = self.create_sample_pose()
        keypoints = pose.get_keypoints_array()
        assert len(keypoints) == 3
        assert keypoints[0] == (100.0, 50.0, 0.9)  # nose
        assert keypoints[1] == (90.0, 45.0, 0.8)   # left_eye
        assert keypoints[2] == (110.0, 45.0, 0.8)  # right_eye
    
    def test_pose_to_dict(self):
        """Test Pose serialization to dictionary."""
        pose = self.create_sample_pose()
        pose_dict = pose.to_dict()
        
        assert pose_dict["person_id"] == 0
        assert pose_dict["frame_number"] == 10
        assert pose_dict["timestamp"] == 0.5
        assert len(pose_dict["joints"]) == 3
        assert pose_dict["joints"][0]["name"] == "nose"
    
    def test_pose_from_dict(self):
        """Test Pose deserialization from dictionary."""
        pose = self.create_sample_pose()
        pose_dict = pose.to_dict()
        reconstructed_pose = Pose.from_dict(pose_dict)
        
        assert reconstructed_pose.person_id == pose.person_id
        assert reconstructed_pose.frame_number == pose.frame_number
        assert reconstructed_pose.timestamp == pose.timestamp
        assert len(reconstructed_pose.joints) == len(pose.joints)
    
    def test_pose_to_json(self):
        """Test Pose JSON serialization."""
        pose = self.create_sample_pose()
        json_str = pose.to_json()
        
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["person_id"] == 0
        assert parsed["frame_number"] == 10
    
    def test_pose_without_optional_fields(self):
        """Test Pose creation without optional fields."""
        joints = [Joint("nose", KeyPoint(100.0, 50.0, 0.9), 0)]
        pose = Pose(joints=joints)
        
        assert pose.person_id == 0  # default
        assert pose.frame_number is None
        assert pose.timestamp is None
        assert pose.confidence is None


class TestCocoJointNames:
    """Test cases for COCO joint names mapping."""
    
    def test_coco_joint_names_coverage(self):
        """Test that COCO joint names cover expected range."""
        # COCO model should have 17 keypoints (0-16)
        assert len(COCO_JOINT_NAMES) == 17
        
        # Check some key joints
        assert COCO_JOINT_NAMES[0] == "nose"
        assert COCO_JOINT_NAMES[5] == "left_shoulder"
        assert COCO_JOINT_NAMES[6] == "right_shoulder"
        assert COCO_JOINT_NAMES[15] == "left_ankle"
        assert COCO_JOINT_NAMES[16] == "right_ankle"
    
    def test_all_joint_ids_sequential(self):
        """Test that joint IDs are sequential from 0."""
        expected_ids = set(range(17))
        actual_ids = set(COCO_JOINT_NAMES.keys())
        assert actual_ids == expected_ids


if __name__ == "__main__":
    pytest.main([__file__]) 