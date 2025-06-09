from meta_agent.template_registry import TemplateRegistry
from meta_agent.template_schema import (
    IOContract,
    TemplateMetadata,
    TemplateCategory,
    TemplateComplexity,
)
from meta_agent.template_search import TemplateSearchEngine


def _meta(slug: str, category: TemplateCategory) -> TemplateMetadata:
    return TemplateMetadata(
        slug=slug,
        title=slug.title(),
        description=f"Template {slug}",
        intended_use="demo",
        io_contract=IOContract(input="text", output="text"),
        tools=[],
        guardrails=[],
        model_pref="gpt3",
        category=category,
        complexity=TemplateComplexity.BASIC,
        created_by="tester",
        semver="0.1.0",
        last_test_passed="2024-01-01T00:00:00Z",
        tags=[slug],
    )


def test_search_basic(tmp_path):
    reg = TemplateRegistry(base_dir=tmp_path)
    reg.register(_meta("greet", TemplateCategory.CONVERSATION), "hello world")
    reg.register(_meta("calc", TemplateCategory.REASONING), "1 + 1")

    engine = TemplateSearchEngine(reg)
    results = engine.search("hello")
    assert results
    assert results[0].slug == "greet"
    assert "hello" in results[0].preview


def test_search_filters(tmp_path):
    reg = TemplateRegistry(base_dir=tmp_path)
    reg.register(_meta("foo", TemplateCategory.CONVERSATION), "foo content")
    reg.register(_meta("bar", TemplateCategory.REASONING), "bar content")

    engine = TemplateSearchEngine(reg)
    res_cat = engine.search("content", category=TemplateCategory.CONVERSATION.value)
    assert len(res_cat) == 1 and res_cat[0].slug == "foo"

    res_tag = engine.search("content", tags=["bar"])
    assert len(res_tag) == 1 and res_tag[0].slug == "bar"

    res_none = engine.search("content", tags=["missing"])
    assert res_none == []


def test_search_capabilities(tmp_path):
    reg = TemplateRegistry(base_dir=tmp_path)
    reg.register(_meta("basic", TemplateCategory.CONVERSATION), "c1")
    m2 = _meta("web", TemplateCategory.CONVERSATION)
    m2.requires_web_search = True
    reg.register(m2, "c2")

    engine = TemplateSearchEngine(reg)
    none = engine.search("c", capabilities=[])
    assert [r.slug for r in none] == ["basic"]

    cap = engine.search("c", capabilities=["web_search"])
    slugs = {r.slug for r in cap}
    assert slugs == {"basic", "web"}
