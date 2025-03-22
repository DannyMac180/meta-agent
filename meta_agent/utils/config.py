"""
Configuration utilities for the meta-agent package.

This module provides functions for loading and managing configuration settings.
This file is maintained for backward compatibility and imports from the
centralized config module.
"""

from meta_agent.config import (
    load_config,
    get_api_key,
    check_api_key,
    print_api_key_warning,
    config
)
