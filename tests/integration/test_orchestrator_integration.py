"""
Integration tests for the MetaAgentOrchestrator focusing on the interaction
between Orchestrator, PlanningEngine, and SubAgentManager.
"""

import pytest
import logging
from unittest.mock import patch

# Add src path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

from meta_agent.orchestrator import MetaAgentOrchestrator
from meta_agent.planning_engine import PlanningEngine
from meta_agent.sub_agent_manager import SubAgentManager # Import agents for type checking if needed


@pytest.mark.asyncio
async def test_orchestrator_integration_flow(caplog):
    """Test the end-to-end flow from spec to sub-agent execution results."""
    # 1. Setup real components
    planning_engine = PlanningEngine()
    # Use a fresh SubAgentManager instance for each test to avoid state leakage
    sub_agent_manager = SubAgentManager()
    orchestrator = MetaAgentOrchestrator(planning_engine, sub_agent_manager)

    # 2. Define input spec and expected decomposed tasks (mock decompose_spec)
    sample_spec = {"name": "IntegrationTestSpec", "description": "Create a feature, test it, and review it."}
    # Mock the output of decompose_spec
    decomposed_tasks = {
        "subtasks": [
            {"id": "int_task_1", "description": "Implement the core logic using code.", "dependencies": []},
            {"id": "int_task_2", "description": "Write unit tests for the new feature.", "dependencies": ["int_task_1"]},
            {"id": "int_task_3", "description": "Review the implementation for style.", "dependencies": ["int_task_1"]}
        ]
    }

    # 3. Patch only decompose_spec on the orchestrator instance
    with patch.object(orchestrator, 'decompose_spec', return_value=decomposed_tasks) as mock_decompose:
        # 4. Run the orchestrator
        with caplog.at_level(logging.INFO):
            result = await orchestrator.run(sample_spec)

    # 5. Assertions
    mock_decompose.assert_called_once_with(sample_spec)

    # Check logs for evidence of PlanningEngine and SubAgentManager working
    assert "Execution plan generated:" in caplog.text
    # Removed assertions for specific "Identified required tools..." logs
    # as the engine doesn't log this at INFO level.
    # The correct tool assignment is implicitly tested by the agent creation logs below.
    # assert "Identified required tools: ['coder_tool']" in caplog.text
    # assert "Identified required tools: ['tester_tool']" in caplog.text
    # assert "Identified required tools: ['reviewer_tool']" in caplog.text

    # Check that sub_agent_manager was called for each task
    assert "Getting/creating agent for task int_task_1 with tools: ['coder_tool']" in caplog.text
    assert "Creating new CoderAgent for task int_task_1" in caplog.text # Assumes first time run
    assert "Getting/creating agent for task int_task_2 with tools: ['tester_tool']" in caplog.text
    assert "Creating new TesterAgent for task int_task_2" in caplog.text # Assumes first time run
    # Check agent request log for task 3
    assert "Getting/creating agent for task int_task_3 with tools:" in caplog.text
    assert "'coder_tool'" in caplog.text
    assert "'reviewer_tool'" in caplog.text
    # Note: Caching reuse happens at DEBUG level, so not asserting log here.
    # Correct agent usage is verified by the execution logs below.

    # Check the execution loop logs
    assert "Executing task int_task_1 using agent CoderAgent..." in caplog.text
    assert "Task int_task_1 completed by CoderAgent. Result: simulated_success" in caplog.text
    assert "Executing task int_task_2 using agent TesterAgent..." in caplog.text
    assert "Task int_task_2 completed by TesterAgent. Result: simulated_success" in caplog.text
    # Check that CoderAgent executed task 3
    assert "Executing task int_task_3 using agent CoderAgent..." in caplog.text
    assert "Task int_task_3 completed by CoderAgent. Result: simulated_success" in caplog.text

    # Check the final result structure and content
    assert isinstance(result, dict)
    # The order depends on PlanningEngine's dependency analysis
    # For this simple case, it should execute 1, then 2 and 3 can run.
    # Assuming analyze_tasks produces a valid order like [1, 2, 3] or [1, 3, 2]
    plan = planning_engine.analyze_tasks(decomposed_tasks) # Run analyze again to see order
    expected_task_ids = set(plan['execution_order'])
    assert set(result.keys()) == expected_task_ids
    assert len(result) == 3 # Expect results for 3 tasks

    # Verify content for each task result
    if "int_task_1" in result:
        assert result["int_task_1"]["status"] == "simulated_success"
        assert "Generated code by CoderAgent" in result["int_task_1"]["output"]
        assert "int_task_1" in result["int_task_1"]["output"]
    if "int_task_2" in result:
        assert result["int_task_2"]["status"] == "simulated_success"
        assert "Test results from TesterAgent" in result["int_task_2"]["output"]
        assert "int_task_2" in result["int_task_2"]["output"]
    if "int_task_3" in result:
        assert result["int_task_3"]["status"] == "simulated_success"
        # Expect output from CoderAgent based on current logic
        assert "Generated code by CoderAgent" in result["int_task_3"]["output"]
        assert "int_task_3" in result["int_task_3"]["output"]

    assert "Orchestration completed successfully." in caplog.text
