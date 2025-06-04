from meta_agent.template_governance import TemplateGovernance


def test_lint_template() -> None:
    gov = TemplateGovernance()
    assert gov.lint_template("def foo():\n    pass\n")


def test_lint_template_failure() -> None:
    gov = TemplateGovernance()
    assert not gov.lint_template("def foo(:\n    pass\n")
