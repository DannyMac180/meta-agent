"""
Utility functions for file operations.
"""

import os
import json
from typing import Dict, Any


def ensure_directory(directory: str) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        directory: Directory path to ensure exists
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def write_file(file_path: str, content: str) -> None:
    """
    Write content to a file, creating directories if necessary.
    
    Args:
        file_path: Path to the file
        content: Content to write
    """
    directory = os.path.dirname(file_path)
    if directory:
        ensure_directory(directory)
    
    with open(file_path, 'w') as f:
        f.write(content)


def read_json_file(file_path: str) -> Dict[str, Any]:
    """
    Read and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON content as a dictionary
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def parse_json_string(json_string: str) -> Dict[str, Any]:
    """
    Parse a JSON string.
    
    Args:
        json_string: JSON string to parse
        
    Returns:
        Parsed JSON content as a dictionary
        
    Raises:
        json.JSONDecodeError: If the string contains invalid JSON
    """
    return json.loads(json_string)