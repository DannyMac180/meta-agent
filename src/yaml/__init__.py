import json
from typing import Any


class YAMLError(Exception):
    pass


def safe_load(stream: Any) -> Any:
    try:
        if hasattr(stream, "read"):
            data = stream.read()
        else:
            data = str(stream)
        return json.loads(data)
    except Exception as e:
        raise YAMLError(str(e))


def dump(data: Any, stream: Any = None) -> str:
    text = json.dumps(data, indent=2)
    if stream is not None:
        stream.write(text)
        return ""
    return text
