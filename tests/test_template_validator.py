from meta_agent.template_validator import TemplateValidator, TemplateTestCase


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
