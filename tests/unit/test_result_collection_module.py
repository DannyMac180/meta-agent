from unittest.mock import MagicMock
import pytest

from meta_agent.evaluation.result_collection import (
    ResultCollectionModule,
    CollectionResult,
)
from meta_agent.evaluation.execution import ExecutionResult
import meta_agent.evaluation.result_collection as rc_mod


def test_init_creates_execution_module(monkeypatch):
    fake_cls = MagicMock()
    fake_instance = MagicMock()
    fake_cls.return_value = fake_instance
    monkeypatch.setattr(rc_mod, "ExecutionModule", fake_cls)
    module = ResultCollectionModule()
    assert module.execution_module is fake_instance


def test_execute_and_collect_success(monkeypatch, tmp_path):
    fake_exec = MagicMock()
    fake_exec.run_tests.return_value = ExecutionResult(0, "out", "err")
    module = ResultCollectionModule(fake_exec)
    result = module.execute_and_collect(tmp_path, timeout=5)
    assert isinstance(result, CollectionResult)
    assert result.exit_code == 0
    assert result.stdout == "out"
    assert result.stderr == "err"
    assert result.duration >= 0
    fake_exec.run_tests.assert_called_with(tmp_path, timeout=5)


def test_execute_and_collect_propagates_error(monkeypatch, tmp_path):
    fake_exec = MagicMock()
    fake_exec.run_tests.side_effect = rc_mod.SandboxExecutionError("boom")
    module = ResultCollectionModule(fake_exec)
    with pytest.raises(rc_mod.SandboxExecutionError):
        module.execute_and_collect(tmp_path)
