import json
from typing import Any, Dict


def save_config(cfg: Dict[str, Any], file_path: str) -> None:
    """Save configuration dictionary to a JSON file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(cfg, f)


def load_config(file_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file. Returns empty dict on error."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, IOError):
        return {}
