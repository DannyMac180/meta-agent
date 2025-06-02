from meta_agent.template_governance import TemplateGovernance


def test_sign_and_verify(tmp_path):
    gov = TemplateGovernance(cache_dir=tmp_path)
    content = "print('hi')"
    sig = gov.sign_template(content)
    assert gov.verify_template(content, sig)
    assert not gov.verify_template("print('bye')", sig)


def test_lint_template(tmp_path):
    gov = TemplateGovernance(cache_dir=tmp_path)
    good = "def foo():\n    pass\n"
    bad = "from typing import *\n"
    assert gov.lint_template(good)
    assert not gov.lint_template(bad)


def test_run_unsigned_template(tmp_path):
    class FakeSandbox:
        def run_code_in_sandbox(self, code_directory, command, **kwargs):
            return 0, "ok", ""

    gov = TemplateGovernance(cache_dir=tmp_path, sandbox_manager=FakeSandbox())
    out = gov.run_unsigned_template("print('hello')")
    assert out == "ok"
