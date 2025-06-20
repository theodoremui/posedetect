@echo off
setlocal enabledelayedexpansion

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

:: Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i

:: Extract major and minor version numbers
for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
    set MAJOR=%%a
    set MINOR=%%b
)

:: Check if Python version is 3.7 or higher
if !MAJOR! LSS 3 (
    echo Error: Python version !PYTHON_VERSION! is too old. Python 3.7 or higher is required.
    exit /b 1
)
if !MAJOR! EQU 3 if !MINOR! LSS 7 (
    echo Error: Python version !PYTHON_VERSION! is too old. Python 3.7 or higher is required.
    exit /b 1
)

echo Using Python version !PYTHON_VERSION!

:: Run the pose detection command with multi-line formatting
python src/video2pose.py ^
    .\data\video.avi ^
    --extract-comprehensive-frames ^
    --frame-extraction-config .\config\video_config.json

echo video extraction completed.