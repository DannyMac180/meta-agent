"""
Unit tests for the MetaAgentOrchestrator.
"""

import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch

# Make sure the src directory is importable
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from meta_agent.orchestrator import MetaAgentOrchestrator
# Import placeholder agents to check isinstance if needed, though mocks are usually sufficient
from meta_agent.sub_agent_manager import CoderAgent, TesterAgent, BaseAgent

# Fixture for a mock agent (main agent, less relevant now but keep for init)
@pytest.fixture
def mock_main_agent():
    return MagicMock(name="MockMainAgent")

# Fixture for a sample specification
@pytest.fixture
def sample_spec():
    return {"name": "TestAgent", "description": "A test agent specification"}

# Fixture for the orchestrator instance
@pytest.fixture
def orchestrator(mock_main_agent):
    orch = MetaAgentOrchestrator(agent=mock_main_agent)
    return orch

# --- Updated Tests --- 

@pytest.mark.asyncio
async def test_orchestrator_run_success(orchestrator, sample_spec, caplog):
    """Test successful run execution with the new delegation flow."""
    # Mock data
    dummy_tasks = {
        "subtasks": [
            {"id": "task_1", "description": "Generate code"},
            {"id": "task_2", "description": "Write tests"}
        ]
    }
    dummy_plan = {
        "task_requirements": [
            {"task_id": "task_1", "tools": ["coder"], "guardrails": ["g1"]},
            {"task_id": "task_2", "tools": ["tester"], "guardrails": ["g1"]}
        ],
        "execution_order": ["task_1", "task_2"],
        "dependencies": {}
    }
    # Create mocks for the sub-agents with an async run method
    mock_coder_agent = MagicMock(spec=CoderAgent, name="CoderAgent")
    mock_coder_agent.run = AsyncMock(return_value={"status": "coder_success", "output": "Code generated for task_1"})
    mock_coder_agent.name = "CoderAgent"

    mock_tester_agent = MagicMock(spec=TesterAgent, name="TesterAgent")
    mock_tester_agent.run = AsyncMock(return_value={"status": "tester_success", "output": "Tests passed for task_2"})
    mock_tester_agent.name = "TesterAgent"

    # Patch methods on the specific orchestrator instance
    with patch.object(orchestrator, 'decompose_spec', return_value=dummy_tasks) as mock_decompose, \
         patch.object(orchestrator.planning_engine, 'analyze_tasks', return_value=dummy_plan) as mock_analyze, \
         patch.object(orchestrator.sub_agent_manager, 'get_or_create_agent') as mock_get_create:

        # Define side effects for get_or_create_agent based on task_id
        def side_effect(req):
            if req['task_id'] == 'task_1':
                return mock_coder_agent
            elif req['task_id'] == 'task_2':
                return mock_tester_agent
            return None # Should not happen in this test case
        mock_get_create.side_effect = side_effect

        with caplog.at_level(logging.INFO):
            result = await orchestrator.run(sample_spec)

    # Assertions
    mock_decompose.assert_called_once_with(sample_spec)
    mock_analyze.assert_called_once_with(dummy_tasks)
    assert mock_get_create.call_count == 2
    # Check calls to get_or_create_agent with the correct requirements
    mock_get_create.assert_any_call(dummy_plan['task_requirements'][0])
    mock_get_create.assert_any_call(dummy_plan['task_requirements'][1])

    # Check calls to sub-agent run methods
    mock_coder_agent.run.assert_called_once_with(specification=dummy_plan['task_requirements'][0])
    mock_tester_agent.run.assert_called_once_with(specification=dummy_plan['task_requirements'][1])

    # Check final results returned by orchestrator.run
    assert isinstance(result, dict)
    assert 'task_1' in result
    assert result['task_1'] == mock_coder_agent.run.return_value # Check if result matches mock return
    assert 'task_2' in result
    assert result['task_2'] == mock_tester_agent.run.return_value

    # Check logs
    assert f"Starting orchestration for specification: {sample_spec['name']}" in caplog.text
    assert f"Executing task task_1 using agent {mock_coder_agent.name}..." in caplog.text
    assert f"Executing task task_2 using agent {mock_tester_agent.name}..." in caplog.text
    assert "Orchestration completed successfully." in caplog.text

@pytest.mark.asyncio
async def test_orchestrator_run_planning_failure(orchestrator, sample_spec, caplog):
    """Test run execution when planning_engine.analyze_tasks raises an exception."""
    dummy_tasks = {"subtasks": [{"id": "task_1", "description": "..."}]}
    test_exception = ValueError("Planning Failed")

    # Patch methods
    with patch.object(orchestrator, 'decompose_spec', return_value=dummy_tasks) as mock_decompose, \
         patch.object(orchestrator.planning_engine, 'analyze_tasks', side_effect=test_exception) as mock_analyze:
        
        with caplog.at_level(logging.ERROR):
            result = await orchestrator.run(sample_spec)

    # Assertions
    mock_decompose.assert_called_once_with(sample_spec)
    mock_analyze.assert_called_once_with(dummy_tasks)
    assert isinstance(result, dict)
    assert result.get('status') == 'failed'
    assert result.get('error') == str(test_exception)
    assert f"Orchestration failed: {test_exception}" in caplog.text

@pytest.mark.asyncio
async def test_orchestrator_run_empty_plan(orchestrator, sample_spec, caplog):
    """Test run execution when the execution plan has no tasks."""
    dummy_tasks = {"subtasks": []} 
    empty_plan = {
        "task_requirements": [],
        "execution_order": [],
        "dependencies": {}
    }

    # Patch methods needed before the check for empty execution_order
    with patch.object(orchestrator, 'decompose_spec', return_value=dummy_tasks) as mock_decompose, \
         patch.object(orchestrator.planning_engine, 'analyze_tasks', return_value=empty_plan) as mock_analyze:

        with caplog.at_level(logging.WARNING):
            result = await orchestrator.run(sample_spec)

    # Assertions
    mock_decompose.assert_called_once_with(sample_spec)
    mock_analyze.assert_called_once_with(dummy_tasks)
    assert isinstance(result, dict)
    assert result.get('status') == 'No tasks to execute'
    assert "Execution order is empty. No tasks to execute." in caplog.text

@pytest.mark.asyncio
async def test_orchestrator_init(mock_main_agent, caplog):
    """Test orchestrator initialization and logging."""
    with caplog.at_level(logging.INFO):
        orchestrator_instance = MetaAgentOrchestrator(agent=mock_main_agent)
        assert orchestrator_instance.agent == mock_main_agent
        assert "MetaAgentOrchestrator initialized." in caplog.text
        assert "PlanningEngine initialized." in caplog.text
        assert "SubAgentManager initialized." in caplog.text
