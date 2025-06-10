import os
from typing import Any, Dict
import pytest
from meta_agent.state_manager import StateManager
from meta_agent.template_engine import TemplateEngine, validate_agent_code
from meta_agent.sub_agent_manager import CoderAgent, TesterAgent


# Simulate a full orchestration run
@pytest.mark.integration
def test_full_orchestration_e2e():
    # 1. Setup state manager
    sm = StateManager()
    sm.set_status("running")
    sm.update_progress(0.1, current_step="init")

    # 2. Simulate sub-agent runs
    spec = {"task_id": "foo", "description": "Write and test a function"}
    coder = CoderAgent()
    tester = TesterAgent()
    coder_output = pytest.run(coro=coder.run(spec)) if hasattr(pytest, "run") else None
    if coder_output is None:
        import asyncio

        coder_output = asyncio.run(coder.run(spec))
    tester_output = (
        pytest.run(coro=tester.run(spec)) if hasattr(pytest, "run") else None
    )
    if tester_output is None:
        import asyncio

        tester_output = asyncio.run(tester.run(spec))

    sm.update_progress(0.5, current_step="sub_agents_done")

    # 3. Assemble agent
    templates_dir = os.path.join(
        os.path.dirname(__file__), "../../src/meta_agent/templates"
    )
    engine = TemplateEngine(templates_dir=templates_dir)
    sub_agent_outputs = {
        "agent_class_name": "OrchestratedAgent",
        "name": "OrchestratedAgent",
        "instructions": "Do everything",
        "core_logic": f"# {coder_output['output']}\n# {tester_output['output']}\nreturn 'done'",
        "tools": ["def tool1(self): pass"],
        "guardrails": ["def guardrail1(self): pass"],
    }
    code = engine.assemble_agent(sub_agent_outputs)
    sm.update_progress(0.9, current_step="assembly_done")

    # 4. Validate
    valid, err = validate_agent_code(code)
    assert valid, f"Validation failed: {err}"
    sm.set_status("completed")
    sm.update_progress(1.0, current_step="done")

    # 5. Check reporting and state
    report: Dict[str, Any] = sm.get_report(as_dict=True)
    assert report["status"] == "completed"
    assert report["progress"] == 1.0
    assert report["current_step"] == "done"
    assert "sub_agents_done" in report["completed_steps"]
    assert "done" in report["completed_steps"]
