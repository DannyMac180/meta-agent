from meta_agent.template_sharing import TemplateSharingManager
from meta_agent.template_schema import (
    TemplateMetadata,
    TemplateCategory,
    TemplateComplexity,
)
from meta_agent.template_registry import TemplateRegistry


def _meta(slug: str) -> TemplateMetadata:
    return TemplateMetadata(
        slug=slug,
        title=slug,
        description="demo",
        category=TemplateCategory.CONVERSATION,
        complexity=TemplateComplexity.BASIC,
    )


def test_export_import_and_rating(tmp_path):
    reg = TemplateRegistry(base_dir=tmp_path)
    manager = TemplateSharingManager(reg)
    reg.register(_meta("greet"), "hello", version="0.1.0")

    exported = manager.export_template("greet")
    assert exported["content"] == "hello"

    reg2 = TemplateRegistry(base_dir=tmp_path / "other")
    manager2 = TemplateSharingManager(reg2)
    manager2.import_template(exported)
    assert reg2.load_template("greet") == "hello"

    manager.add_rating("greet", 5)
    manager.add_rating("greet", 3)
    count, avg = manager.get_rating("greet")
    assert count == 2 and avg == 4.0

    top = manager.showcase()
    assert top and top[0][0] == "greet"


def test_merge_versions(tmp_path):
    reg = TemplateRegistry(base_dir=tmp_path)
    manager = TemplateSharingManager(reg)
    meta = _meta("demo")
    reg.register(meta, "first", version="0.1.0")
    reg.register(meta, "second", version="0.2.0")

    merged = manager.merge_versions("demo", "0.1.0", "0.2.0")
    assert merged.strip() == "second"
