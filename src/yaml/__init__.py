"""Minimal YAML loader used for tests.

This module provides a very small subset of PyYAML's functionality so that the
rest of the codebase can operate without the real dependency.  Only the features
required by the tests are implemented – basic dictionaries, lists and primitive
scalar values.  If the input looks like JSON we simply delegate to ``json``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, List


def _load_real_yaml():
    """Load the bundled PyYAML distribution if present."""
    path = (
        Path(__file__).resolve().parents[2]
        / ".venv/lib/python3.11/site-packages/yaml/__init__.py"
    )
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location("_pyyaml", path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules.setdefault("_pyyaml", module)
        spec.loader.exec_module(module)
        return module
    return None


_REAL_YAML = _load_real_yaml()


class YAMLError(Exception):
    """Raised when ``safe_load`` cannot parse the provided YAML."""

    pass


def safe_load(stream: Any) -> Any:
    """Very small subset of ``yaml.safe_load``.

    The implementation only supports the structures needed in the tests:
    dictionaries, lists and primitive values (strings, integers, floats and
    booleans).  The parser is intentionally simple and will raise ``YAMLError``
    for any input it cannot understand.
    """

    if hasattr(stream, "read"):
        text = stream.read()
    else:
        text = str(stream)

    text = text.strip()

    # If this already looks like JSON, delegate to the json module directly.
    if text.startswith("{") or text.startswith("["):
        try:
            return json.loads(text)
        except Exception as exc:
            raise YAMLError(str(exc))

    if _REAL_YAML is not None:
        try:
            return _REAL_YAML.safe_load(text)
        except Exception as exc:  # pragma: no cover - delegate failure
            raise YAMLError(str(exc))

    lines = text.splitlines()
    if not lines:
        return {}

    def parse_scalar(value: str) -> Any:
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        if value == "null" or value == "~":
            return None
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            return value

    root: Any = {}
    stack: List[Any] = [root]
    indents: List[int] = [0]
    last_key: List[str | None] = [None]

    for raw_line in lines:
        if not raw_line.strip():
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        line = raw_line.lstrip()

        # Pop to the correct indentation level
        while indent < indents[-1]:
            stack.pop()
            indents.pop()
            last_key.pop()

        current = stack[-1]

        if line.startswith("- "):
            item = line[2:].strip()
            value: Any
            if ":" in item:
                key, rest = item.split(":", 1)
                value = {
                    key.strip(): parse_scalar(rest.strip()) if rest.strip() else {}
                }
            else:
                value = parse_scalar(item)

            if not isinstance(current, list):
                # Convert the current mapping key to a list if needed
                key = last_key[-1]
                if key is None or not isinstance(current, dict):
                    raise YAMLError("Invalid list placement")
                new_list: List[Any] = []
                current[key] = new_list
                stack.append(new_list)
                indents.append(indent)
                last_key.append(None)
                current = new_list

            current.append(value)

            if isinstance(value, dict) and item.endswith(":"):
                stack.append(value)
                indents.append(indent + 2)
                last_key.append(list(value.keys())[0])
            continue

        if ":" not in line:
            raise YAMLError(f"Invalid line: {raw_line}")

        key, rest = line.split(":", 1)
        key = key.strip()
        value = rest.strip()
        parsed = parse_scalar(value) if value else {}

        if isinstance(current, list):
            if not current or not isinstance(current[-1], dict):
                current.append({})
            current[-1][key] = parsed
        else:
            current[key] = parsed

        if value == "":
            stack.append(parsed)
            indents.append(indent + 2)
            last_key.append(key)

    return root


def dump(data: Any, stream: Any = None) -> str:
    if _REAL_YAML is not None:
        text = _REAL_YAML.dump(data)
    else:
        text = json.dumps(data, indent=2)

    if stream is not None:
        stream.write(text)
        return ""
    return text
