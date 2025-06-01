from meta_agent.template_mixer import TemplateMixer
from meta_agent.template_creator import TemplateCreator
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
        intended_use="demo",
        io_contract={"input": "text", "output": "text"},
        tools=[],
        guardrails=[],
        model_pref="gpt3",
        category=TemplateCategory.CONVERSATION,
        complexity=TemplateComplexity.BASIC,
        created_by="tester",
        semver="0.1.0",
        last_test_passed="2024-01-01T00:00:00Z",
    )


def test_render_inheritance(tmp_path) -> None:
    reg = TemplateRegistry(base_dir=tmp_path)
    creator = TemplateCreator(reg)
    creator.create(_meta("base"), "{% block greet %}Hello{% endblock %}")
    creator.create(
        _meta("child"),
        "{% extends 'base' %}{% block greet %}{{ super() }} {{ name }}{% endblock %}",
    )

    mixer = TemplateMixer(reg)
    result = mixer.render("child", context={"name": "Bob"})
    assert result.strip() == "Hello Bob"


def test_dependency_graph(tmp_path) -> None:
    reg = TemplateRegistry(base_dir=tmp_path)
    creator = TemplateCreator(reg)
    creator.create(_meta("a"), "A")
    creator.create(_meta("b"), "{% extends 'a' %}B")
    creator.create(_meta("c"), "{% include 'b' %}C")

    mixer = TemplateMixer(reg)
    graph = mixer.dependency_graph("c")
    assert graph["c"] == ["b"]
    assert graph["b"] == ["a"]
    assert graph["a"] == []
