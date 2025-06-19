"""
Logging configuration module using loguru.

This module provides centralized logging configuration for the pose detection
application with different log levels and formats.
"""

import sys
from pathlib import Path
from typing import Optional
from loguru import logger


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    verbose: bool = False
) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path to write logs to
        verbose: Enable verbose logging format
    """
    # Remove default handler
    logger.remove()
    
    # Configure console logging
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    ) if verbose else (
        "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    
    logger.add(
        sys.stdout,
        format=log_format,
        level=log_level,
        colorize=True,
    )
    
    # Configure file logging if specified
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
                "{name}:{function}:{line} | {message}"
            ),
            level="DEBUG",
            rotation="10 MB",
            retention="1 week",
            compression="zip",
        )
    
    logger.info(f"Logging configured with level: {log_level}")
    if log_file:
        logger.info(f"Log file: {log_file}")


def get_logger(name: str):
    """Get a logger instance for a specific module."""
    return logger.bind(name=name) 