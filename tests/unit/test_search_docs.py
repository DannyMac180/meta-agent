import importlib
import sys
import subprocess
import os
from pathlib import Path

# --------------------------------------------------------------------------- #
# Helpers                                                                     #
# --------------------------------------------------------------------------- #

_MOD = "meta_agent.search_docs"
_FALLBACK_MSG = "Hosted tools unavailable: using stub implementations"


def _clear_import(name: str, monkeypatch):
    """Remove *name* from sys.modules and invalidate caches so it re-imports."""
    monkeypatch.delitem(sys.modules, name, raising=False)
    importlib.invalidate_caches()


# --------------------------------------------------------------------------- #
# Tests                                                                        #
# --------------------------------------------------------------------------- #


def test_import_fallback_logs_warning():
    """Importing search_docs in a subprocess should emit a fallback warning."""
    cmd = (
        "import sys, types, importlib, logging; "
        "sys.modules['agents']=types.ModuleType('agents'); "
        "logging.basicConfig(level=logging.WARNING); "
        "import importlib; importlib.invalidate_caches(); "
        "import meta_agent.search_docs"
    )
    env = os.environ.copy()
    src_path = Path(__file__).resolve().parents[2] / "src"
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}" + env.get("PYTHONPATH", "")
    result = subprocess.run(
        [sys.executable, "-c", cmd], capture_output=True, text=True, env=env
    )
    stderr = result.stderr
    assert _FALLBACK_MSG in stderr, "Fallback warning not found in subprocess stderr"


def test_search_docs_function_uses_stub(monkeypatch):
    """search_docs should gracefully handle the stubbed WebSearchTool output."""
    _clear_import(_MOD, monkeypatch)
    search_docs = importlib.import_module(_MOD)

    # Force WebSearchTool to our stub that returns a simple string.
    monkeypatch.setattr(
        search_docs,
        "WebSearchTool",
        lambda *_a, **_kw: "Hosted tool unavailable in this environment.",
    )

    assert search_docs.search_docs("anything", k=3) == [
        "Hosted tool unavailable in this environment."
    ]


# It might be good to add a test for the 'happy path' as well,
# assuming 'agents' and its tools ARE available, but that requires
# mocking the actual tools if they make external calls.
