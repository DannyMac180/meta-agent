"""
Unit tests for the MetaAgentOrchestrator.
"""

import pytest
import logging
from unittest.mock import MagicMock, AsyncMock

from src.meta_agent.orchestrator import MetaAgentOrchestrator
from src.meta_agent.planning_engine import PlanningEngine 
from src.meta_agent.sub_agent_manager import SubAgentManager 

# Mock for the main agent (if still needed by some tests, otherwise can be removed)
@pytest.fixture
def mock_main_agent():
    """Provides a mock main agent."""
    return MagicMock(name="MockMainAgent")

# Mock for PlanningEngine
@pytest.fixture
def mock_planning_engine():
    """Provides a mock PlanningEngine."""
    engine = MagicMock(spec=PlanningEngine)
    # Configure mock methods as needed for tests, e.g.:
    engine.analyze_tasks.return_value = {
        "execution_order": ["task_1", "task_2"],
        "task_requirements": [
            {"task_id": "task_1", "description": "Task 1 details", "agent_type": "CodeGenerator"},
            {"task_id": "task_2", "description": "Task 2 details", "agent_type": "Tester"}
        ]
    }
    return engine

# Mock for SubAgentManager
@pytest.fixture
def mock_sub_agent_manager():
    """Provides a mock SubAgentManager."""
    manager = MagicMock(spec=SubAgentManager)
    # Configure mock methods as needed, e.g., mock agent creation/retrieval:
    mock_sub_agent = AsyncMock()
    mock_sub_agent.name = "MockSubAgent"
    mock_sub_agent.run = AsyncMock(return_value={"status": "completed"})
    manager.get_or_create_agent.return_value = mock_sub_agent
    return manager

@pytest.fixture
def orchestrator(mock_planning_engine, mock_sub_agent_manager):
    """Provides an orchestrator instance with mocked dependencies."""
    # Updated to use new mocks
    orch = MetaAgentOrchestrator(planning_engine=mock_planning_engine, sub_agent_manager=mock_sub_agent_manager)
    return orch

@pytest.fixture
def sample_specification():
    """Provides a sample agent specification dictionary."""
    return {"name": "TestAgent", "description": "A test agent specification"}

@pytest.mark.asyncio
async def test_orchestrator_init(mock_planning_engine, mock_sub_agent_manager, caplog):
    """Test orchestrator initialization and logging."""
    with caplog.at_level(logging.INFO):
        # Updated to use new mocks
        orchestrator_instance = MetaAgentOrchestrator(planning_engine=mock_planning_engine, sub_agent_manager=mock_sub_agent_manager)
    assert isinstance(orchestrator_instance, MetaAgentOrchestrator)
    assert orchestrator_instance.planning_engine == mock_planning_engine
    assert orchestrator_instance.sub_agent_manager == mock_sub_agent_manager
    assert "MetaAgentOrchestrator initialized" in caplog.text

@pytest.mark.asyncio
async def test_orchestrator_run_success(orchestrator, sample_specification, mock_planning_engine, mock_sub_agent_manager):
    """Test the successful run of the orchestrator."""
    # Mock decompose_spec to return something simple
    orchestrator.decompose_spec = MagicMock(return_value={'subtasks': [{'id': 'task_1'}, {'id': 'task_2'}]})

    results = await orchestrator.run(specification=sample_specification)

    # Assertions:
    orchestrator.decompose_spec.assert_called_once_with(sample_specification)
    mock_planning_engine.analyze_tasks.assert_called_once_with({'subtasks': [{'id': 'task_1'}, {'id': 'task_2'}]})
    assert mock_sub_agent_manager.get_or_create_agent.call_count == 2 # Called for task_1 and task_2
    # Check if the sub-agent's run method was called for each task
    mock_sub_agent = mock_sub_agent_manager.get_or_create_agent.return_value
    assert mock_sub_agent.run.call_count == 2
    # Check the structure of the results
    assert "task_1" in results
    assert "task_2" in results
    assert results["task_1"]["status"] == "completed"
    assert results["task_2"]["status"] == "completed"

@pytest.mark.asyncio
async def test_orchestrator_run_planning_failure(orchestrator, sample_specification, mock_planning_engine):
    """Test orchestrator run when planning fails."""
    # Simulate PlanningEngine raising an exception
    mock_planning_engine.analyze_tasks.side_effect = Exception("Planning Error")
    orchestrator.decompose_spec = MagicMock(return_value={'subtasks': [{'id': 'task_1'}]})

    results = await orchestrator.run(specification=sample_specification)

    # Assertions:
    assert results["status"] == "failed"
    assert "Planning Error" in results["error"]
    mock_planning_engine.analyze_tasks.assert_called_once()

@pytest.mark.asyncio
async def test_orchestrator_run_empty_plan(orchestrator, sample_specification, mock_planning_engine, caplog):
    """Test orchestrator run when the plan has no executable tasks."""
    # Mock planning to return an empty execution order
    mock_planning_engine.analyze_tasks.return_value = {"execution_order": [], "task_requirements": []}
    orchestrator.decompose_spec = MagicMock(return_value={'subtasks': []})

    with caplog.at_level(logging.WARNING):
        results = await orchestrator.run(specification=sample_specification)

    # Assertions:
    assert results["status"] == "No tasks to execute"
    assert "Execution order is empty" in caplog.text
    mock_planning_engine.analyze_tasks.assert_called_once()

@pytest.mark.asyncio
async def test_orchestrator_run_sub_agent_failure(orchestrator, sample_specification, mock_planning_engine, mock_sub_agent_manager):
    """Test orchestrator run when a sub-agent fails."""
    # Mock planning engine to return a plan
    mock_planning_engine.analyze_tasks.return_value = {
        "execution_order": ["task_1"],
        "task_requirements": [
            {"task_id": "task_1", "description": "Failing task", "agent_type": "FailingAgent"}
        ]
    }
    orchestrator.decompose_spec = MagicMock(return_value={'subtasks': [{'id': 'task_1'}]})

    # Mock sub-agent manager to return an agent that fails
    failing_agent = AsyncMock()
    failing_agent.name = "FailingSubAgent"
    failing_agent.run = AsyncMock(side_effect=Exception("Sub-agent execution failed"))
    mock_sub_agent_manager.get_or_create_agent.return_value = failing_agent

    results = await orchestrator.run(specification=sample_specification)

    # Assertions:
    assert "task_1" in results
    assert results["task_1"]["status"] == "failed"
    assert "Sub-agent execution failed" in results["task_1"]["error"]
    mock_sub_agent_manager.get_or_create_agent.assert_called_once()
    failing_agent.run.assert_called_once()

# Add more tests as needed for decompose_spec stub, error handling, etc.

# Example test for decompose_spec (assuming it remains a simple stub for now)
# def test_decompose_spec_stub(orchestrator, sample_specification):
#     """Test the decompose_spec stub returns expected structure."""
#     decomposed = orchestrator.decompose_spec(sample_specification)
#     assert "subtasks" in decomposed
#     assert isinstance(decomposed["subtasks"], list)
#     # Add more specific assertions if the stub becomes more complex
