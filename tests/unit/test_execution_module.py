import pytest
from unittest.mock import MagicMock

import meta_agent.evaluation.execution as exec_mod
from meta_agent.evaluation.execution import ExecutionModule, ExecutionResult


def test_init_creates_manager(monkeypatch):
    fake_cls = MagicMock()
    fake_instance = MagicMock()
    fake_cls.return_value = fake_instance
    monkeypatch.setattr(exec_mod, "SandboxManager", fake_cls)
    module = ExecutionModule()
    assert module.sandbox_manager is fake_instance


def test_run_tests_success(monkeypatch, tmp_path):
    fake_manager = MagicMock()
    fake_manager.run_code_in_sandbox.return_value = (0, "out", "err")
    module = ExecutionModule(fake_manager)
    result = module.run_tests(tmp_path, timeout=5)
    assert isinstance(result, ExecutionResult)
    assert result.exit_code == 0
    assert result.stdout == "out"
    assert result.stderr == "err"
    fake_manager.run_code_in_sandbox.assert_called_with(
        code_directory=tmp_path,
        command=["pytest", "-vv"],
        timeout=5,
    )


def test_run_tests_propagates_error(monkeypatch, tmp_path):
    fake_manager = MagicMock()
    fake_manager.run_code_in_sandbox.side_effect = exec_mod.SandboxExecutionError(
        "boom"
    )
    module = ExecutionModule(fake_manager)
    with pytest.raises(exec_mod.SandboxExecutionError):
        module.run_tests(tmp_path)
