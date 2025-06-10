from meta_agent.state_manager import StateManager
from typing import Any, Dict


def test_progress_and_status():
    sm = StateManager()
    sm.update_progress(0.5, current_step="step1")
    assert sm.get_progress() == 0.5
    assert sm.get_status() == "initialized"
    sm.set_status("running")
    assert sm.get_status() == "running"
    state = sm.get_state()
    assert state["current_step"] == "step1"
    assert "step1" in state["steps"]


def test_persistence(tmp_path):
    sm = StateManager()
    sm.update_progress(0.7, current_step="foo")
    file = tmp_path / "state.json"
    assert sm.save_state(str(file))
    sm2 = StateManager()
    assert sm2.load_state(str(file))
    assert sm2.get_progress() == 0.7
    assert sm2.get_state()["current_step"] == "foo"


def test_checkpoint(tmp_path):
    sm = StateManager()
    sm.update_progress(0.2, current_step="bar")
    sm.create_checkpoint("cp1", directory=str(tmp_path))
    sm.update_progress(0.9, current_step="baz")
    sm.restore_checkpoint("cp1", directory=str(tmp_path))
    assert sm.get_progress() == 0.2
    assert sm.get_state()["current_step"] == "bar"


def test_retry_logic():
    sm = StateManager()
    step = "foo"
    for i in range(2):
        sm.register_failure(step)
        assert sm.should_retry(step, max_retries=3)
    sm.register_failure(step)
    assert not sm.should_retry(step, max_retries=3)
    sm.reset_retries(step)
    assert sm.should_retry(step, max_retries=3)
    sm.register_failure(step)
    sm.reset_retries()
    assert sm.should_retry(step, max_retries=3)


def test_reporting():
    sm = StateManager()
    sm.update_progress(1.0, current_step="done")
    sm.set_status("completed")
    sm.register_failure("foo")
    report_str = sm.get_report()
    report_dict: Dict[str, Any] = sm.get_report(as_dict=True)
    assert isinstance(report_str, str)
    assert isinstance(report_dict, dict)
    assert report_dict["status"] == "completed"
    assert report_dict["progress"] == 1.0
    assert report_dict["current_step"] == "done"
    assert "foo" in report_dict["retries"]
