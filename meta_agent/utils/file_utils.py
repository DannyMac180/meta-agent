"""
File utilities for the meta-agent package.

This module provides functions for file operations.
"""

import os
from typing import Dict, Optional


def write_file(path: str, content: str) -> None:
    """
    Write content to a file, creating directories if needed.
    
    Args:
        path: Path to the file
        content: Content to write
    """
    # Create directory if it doesn't exist
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Write the file
    with open(path, "w") as f:
        f.write(content)


def write_files(base_path: str, files: Dict[str, str]) -> None:
    """
    Write multiple files, creating directories if needed.
    
    Args:
        base_path: Base directory path
        files: Dictionary mapping relative file paths to content
    """
    for relative_path, content in files.items():
        full_path = os.path.join(base_path, relative_path)
        write_file(full_path, content)


def read_file(path: str) -> Optional[str]:
    """
    Read content from a file.
    
    Args:
        path: Path to the file
        
    Returns:
        File content or None if the file doesn't exist
    """
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return None
