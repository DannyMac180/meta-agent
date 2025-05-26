import json
import hashlib
from pathlib import Path

from meta_agent.bundle_generator import BundleGenerator
from meta_agent.models import BUNDLE_SCHEMA_VERSION


def test_bundle_generator_creates_files(tmp_path: Path) -> None:
    gen = BundleGenerator(tmp_path)
    metadata = gen.generate(
        agent_code="print('agent')",
        tests={"test_sample.py": "def test_sample():\n    assert True"},
        requirements=["foo==1.0"],
        readme="# Hello",
        guardrails_manifest="{}",
    )

    assert (tmp_path / "agent.py").exists()
    assert (tmp_path / "tests" / "test_sample.py").exists()
    assert (tmp_path / "requirements.txt").exists()
    assert (tmp_path / "README.md").exists()
    assert (tmp_path / "guardrails" / "manifest.json").exists()
    assert (tmp_path / "traces").is_dir()
    assert (tmp_path / "bundle.json").exists()

    with open(tmp_path / "bundle.json", encoding="utf-8") as f:
        data = json.load(f)
    assert data["schema_version"] == BUNDLE_SCHEMA_VERSION
    checksums = data["custom"]["checksums"]

    with open(tmp_path / "agent.py", encoding="utf-8") as f:
        expected = hashlib.sha256(f.read().encode("utf-8")).hexdigest()
    assert checksums["agent.py"] == expected


def test_bundle_generator_templates(tmp_path: Path) -> None:
    gen = BundleGenerator(tmp_path)
    gen.generate(agent_code="", templates={"extra.txt": "hello"})
    assert (tmp_path / "extra.txt").exists()
    with open(tmp_path / "extra.txt", encoding="utf-8") as f:
        assert f.read() == "hello"
