from meta_agent.template_registry import TemplateRegistry
from meta_agent.template_schema import (
    IOContract,
    TemplateMetadata,
    TemplateCategory,
    TemplateComplexity,
)


def _meta() -> TemplateMetadata:
    return TemplateMetadata(
        slug="greet",
        title="Greeting",
        description="Say hi",
        intended_use="demo",
        io_contract=IOContract(input="text", output="text"),
        tools=[],
        guardrails=[],
        model_pref="gpt3",
        category=TemplateCategory.CONVERSATION,
        complexity=TemplateComplexity.BASIC,
        created_by="tester",
        semver="0.1.0",
        last_test_passed="2024-01-01T00:00:00Z",
        tags=["demo"],
    )


def test_register_and_load(tmp_path):
    reg = TemplateRegistry(base_dir=tmp_path)
    meta = _meta()
    reg.register(meta, "hello {{name}}", version="0.1.0")

    templates = reg.list_templates()
    assert len(templates) == 1
    info = templates[0]
    assert info["slug"] == "greet"
    assert info["current_version"] == "0.1.0"
    assert info["versions"][0]["version"] == "0.1.0"

    content = reg.load_template("greet")
    assert content == "hello {{name}}"


def test_versioning_diff_and_rollback(tmp_path):
    reg = TemplateRegistry(base_dir=tmp_path)
    meta = _meta()
    reg.register(meta, "hello {{name}}", version="0.1.0")
    reg.register(meta, "hi {{name}}", version="0.2.0")

    diff = reg.diff("greet", "0.1.0", "0.2.0")
    assert "-hello {{name}}" in diff
    assert "+hi {{name}}" in diff

    reg.rollback("greet", "0.1.0")
    assert reg.list_templates()[0]["current_version"] == "0.1.0"
    assert reg.load_template("greet") == "hello {{name}}"
