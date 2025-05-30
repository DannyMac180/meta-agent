"""Lightweight YAML shim with optional PyYAML support."""

from __future__ import annotations

import json
import importlib
import sys
from pathlib import Path
from typing import Any


class YAMLError(Exception):
    """Exception raised for YAML parsing errors."""


_REAL_YAML = None


def _load_real_yaml() -> Any:
    """Attempt to load PyYAML from a bundled virtual environment."""
    global _REAL_YAML
    if _REAL_YAML is not None:
        return _REAL_YAML

    orig_module = sys.modules.get(__name__)
    for parent in Path(__file__).resolve().parents:
        venv = parent / ".venv" / "lib"
        if not venv.exists():
            continue
        for site in venv.glob("python*/site-packages"):
            if not site.is_dir():
                continue
            sys.path.insert(0, str(site))
            try:
                sys.modules.pop(__name__, None)
                module = importlib.import_module("yaml")
                if getattr(module, "__file__", "") != __file__:
                    _REAL_YAML = module
                    return module
            except Exception:
                pass
            finally:
                sys.modules[__name__] = orig_module
                if str(site) in sys.path:
                    sys.path.remove(str(site))
    return None


def safe_load(stream: Any) -> Any:
    """Parse YAML using PyYAML if available, else fall back to JSON."""
    yaml_mod = _load_real_yaml()
    text = stream.read() if hasattr(stream, "read") else str(stream)
    if yaml_mod is not None:
        try:
            return yaml_mod.safe_load(text)
        except Exception as e:
            raise YAMLError(str(e))
    try:
        return json.loads(text)
    except Exception as e:
        raise YAMLError(str(e))


def dump(data: Any, stream: Any = None) -> str:
    """Serialize data to YAML using PyYAML if available."""
    yaml_mod = _load_real_yaml()
    if yaml_mod is not None:
        text = yaml_mod.dump(data)
    else:
        text = json.dumps(data, indent=2)
    if stream is not None:
        stream.write(text)
        return ""
    return text
