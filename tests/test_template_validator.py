from meta_agent.template_validator import TemplateValidator, TemplateTestCase
from meta_agent.template_schema import (
    TemplateMetadata,
    TemplateCategory,
    TemplateComplexity,
)


def test_template_validator_success() -> None:
    validator = TemplateValidator()
    case = TemplateTestCase(context={"name": "Bob"}, expected_output="Hello Bob")
    result = validator.validate("Hello {{ name }}", [case])
    assert result.success
    assert result.errors == []


def test_template_validator_syntax_error() -> None:
    validator = TemplateValidator()
    result = validator.validate("{% for x in %}")
    assert not result.success
    assert any("syntax error" in e for e in result.errors)


def test_template_validator_missing_variable() -> None:
    validator = TemplateValidator()
    case = TemplateTestCase(context={"name": "Alice"})
    result = validator.validate("Hello {{ name }} from {{ city }}", [case])
    assert not result.success
    assert any("missing variables" in e for e in result.errors)


def test_template_validator_performance_fail() -> None:
    validator = TemplateValidator()
    case = TemplateTestCase(context={}, expected_output="Hello")
    result = validator.validate("Hello", [case], max_render_seconds=0.0)
    assert not result.success
    assert any("too slow" in e for e in result.errors)


def test_template_validator_shell_detection() -> None:
    validator = TemplateValidator()
    result = validator.validate("{{ os.system('ls') }}")
    assert not result.success
    assert any("shell command" in e for e in result.errors)


def test_template_validator_license_scan(monkeypatch) -> None:
    def fake_resolve(pkgs):
        return [], {"badpkg": "GPL"}, None

    validator = TemplateValidator()
    monkeypatch.setattr(validator.dep_manager, "resolve", fake_resolve)
    meta = TemplateMetadata(
        slug="demo",
        title="Demo",
        description="",
        intended_use="",
        io_contract={"input": "text", "output": "text"},
        tools=["badpkg"],
        guardrails=[],
        model_pref="gpt3",
        category=TemplateCategory.CONVERSATION,
        complexity=TemplateComplexity.BASIC,
        created_by="me",
        semver="0.1.0",
        last_test_passed=None,
        tags=[],
    )
    result = validator.validate("hi", metadata=meta)
    assert not result.success
    assert any("non-permissive license" in e for e in result.errors)
