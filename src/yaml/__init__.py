"""Very small YAML helper used in tests.

This module provides a tiny subset of ``yaml`` functionality so that the
project can run without the real PyYAML dependency.  Only the ``safe_load``
and ``dump`` functions required by the tests are implemented.  ``safe_load``
supports the limited YAML features used throughout the test suite: basic
key/value pairs and lists of dictionaries.  It falls back to ``json.loads``
first so JSON input continues to work as before.
"""

from __future__ import annotations

import json
from typing import Any, List


class YAMLError(Exception):
    pass


def _convert_scalar(value: str) -> Any:
    """Convert a YAML scalar to a Python type."""

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _parse_simple_yaml(lines: List[str], start: int, indent: int) -> tuple[Any, int]:
    """Parse a simple block of YAML starting at ``start`` with ``indent``."""

    # If the first relevant line starts with a list indicator, parse a list
    i = start
    while i < len(lines) and not lines[i].strip():
        i += 1
    if (
        i < len(lines)
        and lines[i].lstrip().startswith("- ")
        and (len(lines[i]) - len(lines[i].lstrip(" ")) == indent)
    ):
        lst: List[Any] = []
        while i < len(lines):
            line = lines[i]
            if not line.strip():
                i += 1
                continue
            current_indent = len(line) - len(line.lstrip(" "))
            if current_indent < indent:
                break
            if not line.lstrip().startswith("- "):
                break
            item_content = line.lstrip()[2:].strip()
            i += 1
            if item_content:
                if ":" in item_content:
                    k, v = item_content.split(":", 1)
                    item: Any = {k.strip(): _convert_scalar(v.strip())}
                else:
                    item = _convert_scalar(item_content)
            else:
                item = {}
            # parse subfields
            while i < len(lines):
                sub_line = lines[i]
                sub_indent = len(sub_line) - len(sub_line.lstrip(" "))
                if sub_indent <= current_indent:
                    break
                sub_key, sub_val = sub_line.strip().split(":", 1)
                item[sub_key.strip()] = _convert_scalar(sub_val.strip())
                i += 1
            lst.append(item)
        return lst, i

    result: dict[str, Any] = {}
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        current_indent = len(line) - len(line.lstrip(" "))
        if current_indent < indent:
            break
        if current_indent > indent:
            raise YAMLError("Invalid indentation")
        stripped = line.strip()
        if ":" not in stripped:
            raise YAMLError(f"Invalid line: {line}")
        key, rest = stripped.split(":", 1)
        key = key.strip()
        rest = rest.strip()
        i += 1
        if rest == "":
            # Determine if next block is a list or nested mapping
            if i < len(lines) and lines[i].lstrip().startswith("- "):
                lst: List[Any] = []
                while i < len(lines):
                    item_line = lines[i]
                    if len(item_line) - len(item_line.lstrip(" ")) < indent + 2:
                        break
                    if not item_line.lstrip().startswith("- "):
                        break
                    item_content = item_line.lstrip()[2:].strip()
                    i += 1
                    item: Any
                    if item_content == "":
                        item = {}
                    elif ":" in item_content:
                        k, v = item_content.split(":", 1)
                        item = {k.strip(): _convert_scalar(v.strip())}
                    else:
                        item = _convert_scalar(item_content)
                    # Parse additional properties for the list item
                    while i < len(lines):
                        sub_line = lines[i]
                        sub_indent = len(sub_line) - len(sub_line.lstrip(" "))
                        if sub_indent <= indent + 2:
                            break
                        sub_key, sub_val = sub_line.strip().split(":", 1)
                        item[sub_key.strip()] = _convert_scalar(sub_val.strip())
                        i += 1
                    lst.append(item)
                result[key] = lst
            else:
                sub_obj, i = _parse_simple_yaml(lines, i, indent + 2)
                result[key] = sub_obj
        else:
            result[key] = _convert_scalar(rest)
    return result, i


def safe_load(stream: Any) -> Any:
    """Parse a JSON or very small subset of YAML."""

    if hasattr(stream, "read"):
        data = stream.read()
    else:
        data = str(stream)
    # Normalise indentation to handle triple-quoted strings in tests
    import textwrap

    data = textwrap.dedent(data)

    # Try JSON first for backwards compatibility
    try:
        return json.loads(data)
    except Exception:
        pass

    try:
        lines = data.splitlines()
        parsed, _ = _parse_simple_yaml(lines, 0, 0)
        return parsed
    except Exception as e:  # noqa: BLE001 - part of simple parser
        raise YAMLError(str(e))


def _dump_yaml(obj: Any, indent: int = 0) -> List[str]:
    lines: List[str] = []
    prefix = " " * indent
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.extend(_dump_yaml(v, indent + 2))
            else:
                lines.append(f"{prefix}{k}: {v}")
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(_dump_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {item}")
    else:
        lines.append(f"{prefix}{obj}")
    return lines


def dump(data: Any, stream: Any = None) -> str:
    text = "\n".join(_dump_yaml(data))
    if stream is not None:
        stream.write(text)
        return ""
    return text
