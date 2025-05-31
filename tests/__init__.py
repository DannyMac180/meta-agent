from __future__ import annotations

import sys
from pathlib import Path

pytest_plugins = ["pytest_asyncio", "pytest_mock"]

# Ensure the src directory is on the path for tests
src_dir = Path(__file__).resolve().parent.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
