import pytest
from unittest.mock import MagicMock, patch, AsyncMock, call

from meta_agent.orchestrator import MetaAgentOrchestrator
from meta_agent.planning_engine import PlanningEngine
from meta_agent.sub_agent_manager import SubAgentManager


@pytest.fixture
def mock_planning_engine():
    """Fixture for a mocked PlanningEngine."""
    engine = MagicMock(spec=PlanningEngine)
    engine.analyze_tasks.return_value = {
        "task_requirements": [
            {"task_id": "task_1", "tools": ["coder_tool"], "guardrails": [], "description": "task 1 desc"},
            {"task_id": "task_2", "tools": ["tester_tool"], "guardrails": [], "description": "task 2 desc"},
        ],
        "execution_order": ["task_1", "task_2"],
        "dependencies": {},
    }
    return engine


@pytest.fixture
def mock_sub_agent_manager():
    """Fixture for a mocked SubAgentManager."""
    manager = MagicMock(spec=SubAgentManager)
    mock_agent = MagicMock() 
    mock_agent.run = AsyncMock(return_value={"output": "mock result"})
    manager.mock_agent_instance = mock_agent
    manager.get_or_create_agent.return_value = mock_agent
    return manager


@pytest.fixture
def orchestrator(mock_planning_engine, mock_sub_agent_manager):
    """Fixture for MetaAgentOrchestrator with mocked dependencies."""
    return MetaAgentOrchestrator(mock_planning_engine, mock_sub_agent_manager)


def test_orchestrator_initialization(orchestrator, mock_planning_engine, mock_sub_agent_manager):
    """Test that the orchestrator initializes correctly with its components."""
    assert orchestrator.planning_engine is mock_planning_engine
    assert orchestrator.sub_agent_manager is mock_sub_agent_manager


def test_decompose_spec_stub(orchestrator):
    """Test the current stub implementation of decompose_spec."""
    dummy_spec = {"name": "Test Spec"}
    decomposed = orchestrator.decompose_spec(dummy_spec)
    assert "subtasks" in decomposed
    assert isinstance(decomposed["subtasks"], list)
    assert len(decomposed["subtasks"]) > 0
    assert "id" in decomposed["subtasks"][0]
    assert "description" in decomposed["subtasks"][0]


@pytest.mark.asyncio
async def test_run_orchestration_flow(orchestrator, mock_planning_engine, mock_sub_agent_manager):
    """Test the basic orchestration flow using mocks."""
    dummy_spec = {"name": "Test Spec"}

    decomposed_tasks_output = {
        "subtasks": [{"id": "task_1", "description": "..."}, {"id": "task_2", "description": "..."}]
    }
    orchestrator.decompose_spec = MagicMock(return_value=decomposed_tasks_output)
    plan = mock_planning_engine.analyze_tasks.return_value

    results = await orchestrator.run(dummy_spec)

    orchestrator.decompose_spec.assert_called_once_with(dummy_spec)
    mock_planning_engine.analyze_tasks.assert_called_once_with(decomposed_tasks_output)

    assert mock_sub_agent_manager.get_or_create_agent.call_count == len(plan["execution_order"])
    manager_expected_calls = [call(req) for req in plan["task_requirements"]]
    mock_sub_agent_manager.get_or_create_agent.assert_has_calls(manager_expected_calls, any_order=True)

    mock_agent_instance = mock_sub_agent_manager.mock_agent_instance
    assert mock_agent_instance.run.call_count == len(plan["execution_order"])

    # Extract the 'specification' from each run call's kwargs
    actual_specs = [c.kwargs.get("specification") for c in mock_agent_instance.run.call_args_list]
    assert len(actual_specs) == len(plan["execution_order"])
    actual_task_ids_in_order = [spec.get("task_id") for spec in actual_specs]
    expected_task_ids_in_order = plan["execution_order"]
    assert actual_task_ids_in_order == expected_task_ids_in_order, \
        f"Expected agent.run calls for task IDs {expected_task_ids_in_order}, but got {actual_task_ids_in_order}"

    # Results should be the raw task_result returned by each agent
    assert isinstance(results, dict)
    assert len(results) == len(plan["execution_order"])
    for task_id in plan["execution_order"]:
        assert task_id in results
        assert results[task_id] == {"output": "mock result"}


@pytest.mark.asyncio
async def test_run_orchestration_agent_creation_fails(orchestrator, mock_planning_engine, mock_sub_agent_manager):
    """Test the flow when sub_agent_manager fails to return an agent."""
    dummy_spec = {"name": "Test Spec Fail"}

    decomposed_tasks_output = {"subtasks": [{"id": "task_1", "description": "..."}]}
    orchestrator.decompose_spec = MagicMock(return_value=decomposed_tasks_output)

    plan = {
        "task_requirements": [{"task_id": "task_1", "tools": ["some_tool"], "description": "..."}],
        "execution_order": ["task_1"],
        "dependencies": {},
    }
    mock_planning_engine.analyze_tasks.return_value = plan

    original_mock_agent_ref = mock_sub_agent_manager.mock_agent_instance

    mock_sub_agent_manager.get_or_create_agent.return_value = None

    results = await orchestrator.run(dummy_spec)

    orchestrator.decompose_spec.assert_called_once_with(dummy_spec)
    mock_planning_engine.analyze_tasks.assert_called_once_with(decomposed_tasks_output)
    mock_sub_agent_manager.get_or_create_agent.assert_called_once_with(plan["task_requirements"][0])

    assert original_mock_agent_ref.run.call_count == 0

    assert isinstance(results, dict)
    assert "task_1" in results
    assert results["task_1"]["status"] == "failed"
    assert "Sub-agent creation/retrieval failed" in results["task_1"]["error"]
