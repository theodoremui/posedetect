"""
Data models for pose detection results.

This module contains the core data structures used to represent pose detection
results including joints, keypoints, and complete poses.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
import json


@dataclass
class KeyPoint:
    """
    Represents a single keypoint in the pose.
    
    Attributes:
        x: X coordinate of the keypoint
        y: Y coordinate of the keypoint
        confidence: Confidence score of the detection (0.0 to 1.0)
    """
    x: float
    y: float
    confidence: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert keypoint to dictionary representation."""
        return {
            "x": self.x,
            "y": self.y,
            "confidence": self.confidence
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> "KeyPoint":
        """Create KeyPoint from dictionary."""
        return cls(
            x=data["x"],
            y=data["y"],
            confidence=data["confidence"]
        )


@dataclass
class Joint:
    """
    Represents a joint with its keypoint and semantic information.
    
    Attributes:
        name: Name of the joint (e.g., "nose", "left_shoulder")
        keypoint: KeyPoint containing position and confidence
        joint_id: Numeric ID of the joint in OpenPose convention
    """
    name: str
    keypoint: KeyPoint
    joint_id: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert joint to dictionary representation."""
        return {
            "name": self.name,
            "joint_id": self.joint_id,
            "keypoint": self.keypoint.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Joint":
        """Create Joint from dictionary."""
        return cls(
            name=data["name"],
            joint_id=data["joint_id"],
            keypoint=KeyPoint.from_dict(data["keypoint"])
        )


@dataclass
class Pose:
    """
    Represents a complete pose detection result for a single person.
    
    Attributes:
        joints: List of detected joints
        person_id: ID of the person (useful for multi-person detection)
        frame_number: Frame number where this pose was detected (for videos)
        timestamp: Timestamp in seconds (for videos)
        confidence: Overall confidence score for the pose
    """
    joints: List[Joint]
    person_id: int = 0
    frame_number: Optional[int] = None
    timestamp: Optional[float] = None
    confidence: Optional[float] = None
    
    def get_joint_by_name(self, name: str) -> Optional[Joint]:
        """Get a joint by its name."""
        for joint in self.joints:
            if joint.name == name:
                return joint
        return None
    
    def get_joint_by_id(self, joint_id: int) -> Optional[Joint]:
        """Get a joint by its ID."""
        for joint in self.joints:
            if joint.joint_id == joint_id:
                return joint
        return None
    
    def get_keypoints_array(self) -> List[Tuple[float, float, float]]:
        """Get keypoints as array of (x, y, confidence) tuples."""
        return [(j.keypoint.x, j.keypoint.y, j.keypoint.confidence) for j in self.joints]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pose to dictionary representation."""
        return {
            "person_id": self.person_id,
            "frame_number": self.frame_number,
            "timestamp": self.timestamp,
            "confidence": self.confidence,
            "joints": [joint.to_dict() for joint in self.joints]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pose":
        """Create Pose from dictionary."""
        joints = [Joint.from_dict(joint_data) for joint_data in data["joints"]]
        return cls(
            joints=joints,
            person_id=data.get("person_id", 0),
            frame_number=data.get("frame_number"),
            timestamp=data.get("timestamp"),
            confidence=data.get("confidence")
        )
    
    def to_json(self) -> str:
        """Convert pose to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


# OpenPose COCO model joint names mapping (18 keypoints)
COCO_JOINT_NAMES = {
    0: "nose",
    1: "left_eye",
    2: "right_eye",
    3: "left_ear",
    4: "right_ear",
    5: "left_shoulder",
    6: "right_shoulder",
    7: "left_elbow",
    8: "right_elbow",
    9: "left_wrist",
    10: "right_wrist",
    11: "left_hip",
    12: "right_hip",
    13: "left_knee",
    14: "right_knee",
    15: "left_ankle",
    16: "right_ankle"
}

# OpenPose BODY_25 model joint names mapping (25 keypoints)
BODY_25_JOINT_NAMES = {
    0: "nose",
    1: "neck",
    2: "right_shoulder",
    3: "right_elbow",
    4: "right_wrist",
    5: "left_shoulder",
    6: "left_elbow",
    7: "left_wrist",
    8: "mid_hip",
    9: "right_hip",
    10: "right_knee",
    11: "right_ankle",
    12: "left_hip",
    13: "left_knee",
    14: "left_ankle",
    15: "right_eye",
    16: "left_eye",
    17: "right_ear",
    18: "left_ear",
    19: "left_big_toe",
    20: "left_small_toe",
    21: "left_heel",
    22: "right_big_toe",
    23: "right_small_toe",
    24: "right_heel"
}

# Body part connections for visualization
POSE_CONNECTIONS = [
    (0, 1), (0, 2), (1, 3), (2, 4),  # head
    (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),  # arms
    (5, 11), (6, 12), (11, 12),  # torso
    (11, 13), (13, 15), (12, 14), (14, 16)  # legs
] 