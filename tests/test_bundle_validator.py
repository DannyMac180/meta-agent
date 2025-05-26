from pathlib import Path

from meta_agent.bundle_generator import BundleGenerator
from meta_agent.bundle_validator import BundleValidator


def create_sample_bundle(tmp_path: Path) -> Path:
    gen = BundleGenerator(tmp_path)
    gen.generate(
        agent_code="def main():\n    return 'ok'",
        tests={
            "test_main.py": "from agent import main\n\ndef test_main():\n    assert main() == 'ok'",
        },
        requirements=["pytest==8.0.0"],
        readme="# Sample",
    )
    return tmp_path


def test_bundle_validator_success(tmp_path: Path) -> None:
    bundle_dir = create_sample_bundle(tmp_path)
    validator = BundleValidator(bundle_dir)
    result = validator.validate()
    assert result.success is True
    assert result.errors == []


def test_bundle_validator_checksum_failure(tmp_path: Path) -> None:
    bundle_dir = create_sample_bundle(tmp_path)
    (bundle_dir / "agent.py").write_text("broken")
    validator = BundleValidator(bundle_dir)
    result = validator.validate()
    assert result.success is False
    assert any("checksum mismatch" in e for e in result.errors)


def test_bundle_validator_unpinned_requirement(tmp_path: Path) -> None:
    bundle_dir = create_sample_bundle(tmp_path)
    (bundle_dir / "requirements.txt").write_text("pytest>=8")
    validator = BundleValidator(bundle_dir)
    result = validator.validate()
    assert result.success is False
    assert any("unpinned requirement" in e for e in result.errors)


def test_bundle_validator_test_failure(tmp_path: Path) -> None:
    bundle_dir = create_sample_bundle(tmp_path)
    (bundle_dir / "tests" / "test_main.py").write_text(
        "def test_fail():\n    assert False"
    )
    validator = BundleValidator(bundle_dir)
    result = validator.validate()
    assert result.success is False
    assert any("tests failed" in e for e in result.errors)
