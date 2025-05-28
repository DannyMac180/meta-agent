from pydantic import ValidationError

from meta_agent.template_schema import (
    TemplateCategory,
    TemplateComplexity,
    TemplateMetadata,
)


def test_template_metadata_valid() -> None:
    meta = TemplateMetadata(
        slug="basic-chat",
        title="Basic Chat Bot",
        description="Minimal conversational agent",
        category=TemplateCategory.CONVERSATION,
        subcategory="qa",
        complexity=TemplateComplexity.BASIC,
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
            category="invalid",  # type: ignore[arg-type]
            subcategory="x",
            complexity=TemplateComplexity.BASIC,
        )
    except ValidationError:
        pass
    else:  # pragma: no cover - should not succeed
        assert False, "ValidationError not raised"
