import re
from meta_agent.dependency_manager import DependencyManager


def test_resolve_pins_versions():
    manager = DependencyManager()
    reqs, licenses, _ = manager.resolve(["pydantic", "click"])
    assert any(r.startswith("pydantic==") for r in reqs)
    assert any(r.startswith("click==") for r in reqs)
    assert licenses.get("pydantic") == "MIT"
    assert "click" in licenses


def test_resolve_with_hashes():
    manager = DependencyManager()
    reqs, licenses, hashes = manager.resolve(["pydantic"], include_hashes=True)
    assert any(r.startswith("pydantic==") for r in reqs)
    assert isinstance(hashes, dict)
    assert "pydantic" in hashes
    assert re.fullmatch(r"[0-9a-f]{64}", hashes["pydantic"])
