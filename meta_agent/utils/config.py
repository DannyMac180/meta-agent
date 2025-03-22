"""
Configuration utilities for the meta-agent package.

This module provides functions for loading and managing configuration settings.
"""

import os
from dotenv import load_dotenv
from typing import Optional


def load_config() -> None:
    """
    Load configuration from environment variables and .env file.
    """
    load_dotenv()


def get_api_key() -> Optional[str]:
    """
    Get the OpenAI API key from environment variables.
    
    Returns:
        The API key if found, None otherwise
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    return api_key


def check_api_key() -> bool:
    """
    Check if the OpenAI API key is set.
    
    Returns:
        True if the API key is set, False otherwise
    """
    api_key = get_api_key()
    return api_key is not None


def print_api_key_warning() -> None:
    """
    Print a warning message if the OpenAI API key is not set.
    """
    print("Warning: OPENAI_API_KEY environment variable not set.")
    print("Please set your OpenAI API key in the .env file or as an environment variable:")
    print("export OPENAI_API_KEY='your-api-key'")
