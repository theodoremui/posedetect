#!/usr/bin/env python3
"""
Video to Pose Detection Tool

A command-line application for extracting human pose information from
video and image files using OpenPose.

This is the main entry point that delegates to the CLI module.
"""

import sys
from posedetect.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
