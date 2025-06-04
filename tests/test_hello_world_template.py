from meta_agent.template_registry import TemplateRegistry
from meta_agent.template_search import TemplateSearchEngine


def test_hello_world_template_registered() -> None:
    reg = TemplateRegistry()
    templates = {t["slug"] for t in reg.list_templates()}
    assert "hello-world" in templates
    content = reg.load_template("hello-world")
    assert content and "Hello" in content


def test_search_hello_world() -> None:
    reg = TemplateRegistry()
    engine = TemplateSearchEngine(reg)
    results = engine.search("hello")
    assert any(r.slug == "hello-world" for r in results)
