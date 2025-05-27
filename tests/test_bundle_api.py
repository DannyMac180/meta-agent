from pathlib import Path

from meta_agent.bundle_generator import BundleGenerator
from meta_agent.bundle import Bundle


def test_bundle_load_and_list_files(tmp_path: Path) -> None:
    gen = BundleGenerator(tmp_path)
    gen.generate(agent_code="print('hi')")

    b = Bundle(tmp_path)
    assert b.metadata.schema_version
    files = b.list_files()
    assert "agent.py" in files
    assert b.read_text("agent.py").strip() == "print('hi')"


def test_bundle_generator_hooks(tmp_path: Path) -> None:
    calls: list[str] = []

    def pre(path: Path) -> None:
        calls.append("pre")

    def post(path: Path, meta) -> None:
        calls.append("post")

    gen = BundleGenerator(tmp_path)
    gen.generate(agent_code="print('x')", pre_hook=pre, post_hook=post)

    assert calls == ["pre", "post"]
