from meta_agent.template_registry import TemplateRegistry
from meta_agent.template_schema import (
    TemplateCategory,
    TemplateComplexity,
    TemplateMetadata,
)
from meta_agent.template_index import TemplateIndex


def _meta(slug: str) -> TemplateMetadata:
    return TemplateMetadata(
        slug=slug,
        title=slug,
        description="demo",
        category=TemplateCategory.CONVERSATION,
        complexity=TemplateComplexity.BASIC,
        tags=[slug],
    )


def test_build_and_search(tmp_path) -> None:
    reg = TemplateRegistry(base_dir=tmp_path)
    reg.register(_meta("foo"), "hello foo")
    reg.register(_meta("bar"), "hello bar")

    index = TemplateIndex(reg)
    index.rebuild()

    results = index.search("hello foo")
    assert results and results[0]["slug"] == "foo"


def test_auto_rebuild_on_drift(tmp_path) -> None:
    reg = TemplateRegistry(base_dir=tmp_path)
    reg.register(_meta("foo"), "hello foo")

    index = TemplateIndex(reg)
    index.rebuild()

    # modify template to trigger checksum mismatch
    tpl_path = reg.templates_dir / "foo" / "v0_1_0" / "template.yaml"
    tpl_path.write_text("hi foo", encoding="utf-8")

    index.ensure_up_to_date()
    results = index.search("hi foo")
    assert results and results[0]["slug"] == "foo"
