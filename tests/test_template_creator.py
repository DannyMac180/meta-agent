from meta_agent.template_creator import TemplateCreator, validate_template
from meta_agent.template_schema import (
    TemplateMetadata,
    TemplateCategory,
    TemplateComplexity,
)
from meta_agent.template_registry import TemplateRegistry


def _meta() -> TemplateMetadata:
    return TemplateMetadata(
        slug="demo",
        title="Demo Template",
        description="Simple demo",
        category=TemplateCategory.CONVERSATION,
        complexity=TemplateComplexity.BASIC,
        tags=["demo"],
    )


def test_validate_template_success() -> None:
    ok, err = validate_template("hello {{ name }}")
    assert ok and err == ""


def test_validate_template_failure() -> None:
    ok, err = validate_template("{% for x in %}")
    assert not ok and err


def test_creator_register(tmp_path) -> None:
    reg = TemplateRegistry(base_dir=tmp_path)
    creator = TemplateCreator(reg)
    path = creator.create(_meta(), "hi {{name}}", version="0.1.0")
    assert path
    assert reg.load_template("demo") == "hi {{name}}"
