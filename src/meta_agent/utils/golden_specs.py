from __future__ import annotations

from importlib import resources
from typing import List

import yaml


_DEF_PATH = "data/golden_spec_fuzz_set.yaml"


def load_golden_spec_fuzz_set() -> List[str]:
    """Return the list of vague specification strings used for tests."""
    try:
        data_path = resources.files("meta_agent").joinpath(_DEF_PATH)
        text = data_path.read_text(encoding="utf-8")
        data = yaml.safe_load(text) or {}
    except FileNotFoundError:
        return []
    specs = data.get("specs")
    if isinstance(specs, list):
        return [str(s) for s in specs]
    return []
