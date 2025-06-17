from pydantic import ValidationError

from meta_agent.template_schema import (
    IOContract,
    TemplateCategory,
    TemplateComplexity,
    TemplateMetadata,
)


def test_template_metadata_valid() -> None:
    meta = TemplateMetadata(
        slug="basic-chat",
        title="Basic Chat Bot",
        description="Minimal conversational agent",
        intended_use="demo",
        io_contract=IOContract(input="text", output="text"),
        tools=[],
        guardrails=[],
        model_pref="gpt3",
        category=TemplateCategory.CONVERSATION,
        subcategory="qa",
        complexity=TemplateComplexity.BASIC,
        created_by="tester",
        semver="0.1.0",
        last_test_passed="2024-01-01T00:00:00Z",
        tags=["chat"],
    )
    assert meta.slug == "basic-chat"
    assert meta.category is TemplateCategory.CONVERSATION
    assert meta.complexity is TemplateComplexity.BASIC
    assert meta.tags == ["chat"]


def test_template_metadata_invalid_category() -> None:
    try:
        TemplateMetadata(
            slug="bad",
            title="Bad",
            description="Bad",
            intended_use="demo",
            io_contract=IOContract(input="", output=""),
            tools=[],
            guardrails=[],
            model_pref="gpt3",
            category="invalid",  # type: ignore[arg-type]
            subcategory="x",
            complexity=TemplateComplexity.BASIC,
            created_by="tester",
            semver="0.1.0",
            last_test_passed="2024-01-01T00:00:00Z",
        )
    except ValidationError:
        pass
    else:  # pragma: no cover - should not succeed
        assert False, "ValidationError not raised"


def test_template_metadata_compat_flags() -> None:
    meta = TemplateMetadata(
        slug="compat",
        title="Compat",
        description="desc",
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
        requires_structured_outputs=True,
    )
    assert meta.requires_structured_outputs is True
    assert meta.requires_web_search is False
