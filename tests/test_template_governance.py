import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from meta_agent.template_governance import TemplateGovernance


def test_sign_and_verify(tmp_path: Path) -> None:
    cache = tmp_path / "cache.json"
    gov = TemplateGovernance(secret="key", cache_path=cache)
    sig = gov.sign("print('hi')\n")
    assert sig
    assert gov.verify("print('hi')\n", sig)
    data = json.loads(cache.read_text())
    checksum = hashlib.sha256("print('hi')\n".encode()).hexdigest()
    assert data[checksum] == sig


def test_lint(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd, input, capture_output):
        return MagicMock(stdout=b"template.py:1:1 F401 unused import os\n")

    monkeypatch.setattr("subprocess.run", fake_run)
    gov = TemplateGovernance(secret="k")
    issues = gov.lint("import os\n")
    assert issues and "unused import" in issues[0]


def test_run_unsigned(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    called = {}

    def fake_run(self, code_directory, command, **_):
        called["args"] = (code_directory, command)
        return 0, "out", "err"

    monkeypatch.setattr(
        "meta_agent.sandbox.sandbox_manager.SandboxManager.run_code_in_sandbox",
        fake_run,
    )
    gov = TemplateGovernance(secret="s")
    exit_code, out, err = gov.run_unsigned(tmp_path, ["cmd"])
    assert exit_code == 0 and out == "out" and err == "err"
    assert called["args"] == (tmp_path, ["cmd"])
