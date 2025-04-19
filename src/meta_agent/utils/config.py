import json
from typing import Any, Dict, Optional


def load_config(path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.

    Args:
        path: Path to the configuration file.

    Returns:
        Dictionary containing configuration. Returns empty dict if file not found or invalid.
    """
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_config(config: Dict[str, Any], path: str) -> None:
    """
    Save configuration to a JSON file.

    Args:
        config: Dictionary of configuration values.
        path: Path where to write the configuration file.
    """
    with open(path, 'w') as f:
        json.dump(config, f, indent=4)
