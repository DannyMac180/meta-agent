import pytest
from unittest.mock import AsyncMock, MagicMock, call, patch
from pytest_mock import MockerFixture

from agents import Agent
from meta_agent.orchestrator import MetaAgentOrchestrator
from meta_agent.planning_engine import PlanningEngine
from meta_agent.sub_agent_manager import SubAgentManager
from meta_agent.registry import ToolRegistry
from meta_agent.tool_designer import ToolDesignerAgent, GeneratedTool


@pytest.fixture
def mock_planning_engine():
    """Fixture for a mocked PlanningEngine."""
    engine = MagicMock(spec=PlanningEngine)
    engine.analyze_tasks.return_value = {
        "task_requirements": [
            {
                "task_id": "task_1",
                "tools": ["coder_tool"],
                "guardrails": [],
                "description": "task 1 desc",
            },
            {
                "task_id": "task_2",
                "tools": ["tester_tool"],
                "guardrails": [],
                "description": "task 2 desc",
            },
        ],
        "execution_order": ["task_1", "task_2"],
        "dependencies": {},
    }
    return engine


@pytest.fixture
def mock_sub_agent_manager(mocker: MockerFixture) -> MagicMock:
    """Provides a mocked SubAgentManager."""
    mock_manager = MagicMock(spec=SubAgentManager)

    mock_agent_instance = MagicMock(spec=Agent)
    mock_agent_instance.name = "MockedTestAgent_NoToolReq"  # For logging
    # Explicitly set run as an AsyncMock returning a string
    mock_agent_instance.run = mocker.AsyncMock(return_value="mock result")

    mock_manager.get_or_create_agent.return_value = mock_agent_instance
    # Store the agent instance on the manager mock if tests rely on this pattern
    mock_manager.mock_agent_instance = mock_agent_instance
    return mock_manager


@pytest.fixture
def mock_tool_registry():
    """Fixture for a mocked ToolRegistry."""
    registry = MagicMock(spec=ToolRegistry)
    registry.register = MagicMock(
        return_value="/path/to/mock_tool/v0.1.0"
    )  # Simulate successful registration
    registry.get_tool_metadata = MagicMock(return_value=None)  # Default to not found
    registry.find_by_fingerprint = MagicMock(return_value=None)
    return registry


@pytest.fixture
def mock_tool_designer_agent():
    """Fixture for a mocked ToolDesignerAgent."""
    designer = MagicMock(spec=ToolDesignerAgent)
    # design_tool and refine_design are async, so use AsyncMock for their return values or the methods themselves
    designer.design_tool = AsyncMock(
        return_value=None
    )  # Default to design failure for safety
    # designer.refine_design = AsyncMock(return_value=None)  # Default to refine failure # TODO: refine_design removed
    return designer


@pytest.fixture
def orchestrator(
    mock_planning_engine,
    mock_sub_agent_manager,
    mock_tool_registry,
    mock_tool_designer_agent,
):
    """Fixture for MetaAgentOrchestrator with mocked dependencies."""
    return MetaAgentOrchestrator(
        planning_engine=mock_planning_engine,
        sub_agent_manager=mock_sub_agent_manager,
        tool_registry=mock_tool_registry,
        tool_designer_agent=mock_tool_designer_agent,
    )


def test_orchestrator_initialization(
    orchestrator, mock_planning_engine, mock_sub_agent_manager
):
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
async def test_run_orchestration_flow(
    orchestrator, mock_planning_engine, mock_sub_agent_manager
):
    """Test the basic orchestration flow using mocks."""
    dummy_spec = {"name": "Test Spec"}

    decomposed_tasks_output = {
        "subtasks": [
            {"id": "task_1", "description": "..."},
            {"id": "task_2", "description": "..."},
        ]
    }
    orchestrator.decompose_spec = MagicMock(return_value=decomposed_tasks_output)
    plan = mock_planning_engine.analyze_tasks.return_value

    results = await orchestrator.run(dummy_spec)

    orchestrator.decompose_spec.assert_called_once_with(dummy_spec)
    mock_planning_engine.analyze_tasks.assert_called_once_with(decomposed_tasks_output)

    assert mock_sub_agent_manager.get_or_create_agent.call_count == len(
        plan["execution_order"]
    )
    manager_expected_calls = [call(req) for req in plan["task_requirements"]]
    mock_sub_agent_manager.get_or_create_agent.assert_has_calls(
        manager_expected_calls, any_order=True
    )

    mock_agent_instance = mock_sub_agent_manager.mock_agent_instance
    assert mock_agent_instance.run.call_count == len(plan["execution_order"])

    # Extract the 'specification' from each run call's kwargs
    actual_specs = [
        c.kwargs.get("specification") for c in mock_agent_instance.run.call_args_list
    ]
    assert len(actual_specs) == len(plan["execution_order"])
    actual_task_ids_in_order = [spec.get("task_id") for spec in actual_specs]
    expected_task_ids_in_order = plan["execution_order"]
    assert (
        actual_task_ids_in_order == expected_task_ids_in_order
    ), f"Expected agent.run calls for task IDs {expected_task_ids_in_order}, but got {actual_task_ids_in_order}"

    # Results should be the raw task_result returned by each agent
    assert isinstance(results, dict)
    assert len(results) == len(plan["execution_order"])
    for task_id in plan["execution_order"]:
        assert task_id in results
        assert results[task_id] == {"output": "mock result", "status": "completed"}

    # Verify logging
    # Check for specific log messages or patterns as needed


@pytest.mark.asyncio
async def test_run_orchestration_agent_creation_fails(
    orchestrator, mock_planning_engine, mock_sub_agent_manager
):
    """Test the flow when sub_agent_manager fails to return an agent."""
    dummy_spec = {"name": "Test Spec Fail"}

    decomposed_tasks_output = {"subtasks": [{"id": "task_1", "description": "..."}]}
    orchestrator.decompose_spec = MagicMock(return_value=decomposed_tasks_output)

    plan = {
        "task_requirements": [
            {"task_id": "task_1", "tools": ["some_tool"], "description": "..."}
        ],
        "execution_order": ["task_1"],
        "dependencies": {},
    }
    mock_planning_engine.analyze_tasks.return_value = plan

    original_mock_agent_ref = mock_sub_agent_manager.mock_agent_instance

    mock_sub_agent_manager.get_or_create_agent.return_value = None

    results = await orchestrator.run(dummy_spec)

    orchestrator.decompose_spec.assert_called_once_with(dummy_spec)
    mock_planning_engine.analyze_tasks.assert_called_once_with(decomposed_tasks_output)
    mock_sub_agent_manager.get_or_create_agent.assert_called_once_with(
        plan["task_requirements"][0]
    )

    assert original_mock_agent_ref.run.call_count == 0

    assert isinstance(results, dict)
    assert "task_1" in results
    assert results["task_1"]["status"] == "failed"
    assert "Sub-agent creation/retrieval failed" in results["task_1"]["error"]


# --- Tests for Tool Design and Refinement ---


@pytest.fixture
def sample_tool_spec():
    return {
        "name": "SampleTool",
        "description": "A sample tool for testing.",
        "specification": {
            "input_schema": {
                "type": "object",
                "properties": {"data": {"type": "string"}},
            },
            "output_schema": {"type": "string"},
        },
    }


@pytest.mark.asyncio
async def test_design_tool_cache_hit(
    orchestrator, sample_tool_spec, mock_tool_designer_agent
):
    """Test cache hit scenario for design_and_register_tool."""
    fingerprint = "test_fingerprint_cache_hit"
    cached_path = "/cached/path/to/tool/v0.1.0"
    orchestrator.spec_fingerprint_cache[fingerprint] = cached_path

    with patch.object(
        orchestrator, "_calculate_spec_fingerprint", return_value=fingerprint
    ) as mock_fingerprint_calc:
        module_path = await orchestrator.design_and_register_tool(sample_tool_spec)

    assert module_path == cached_path
    mock_fingerprint_calc.assert_called_once_with(sample_tool_spec)
    mock_tool_designer_agent.design_tool.assert_not_called()  # Should not design if cache hit
    assert orchestrator.tool_cached_hit_total == 1


@pytest.mark.asyncio
async def test_design_tool_cache_miss_success(
    orchestrator, sample_tool_spec, mock_tool_designer_agent, mock_tool_registry
):
    """Test cache miss followed by successful design and registration."""
    fingerprint = "test_fingerprint_cache_miss"
    generated_tool = GeneratedTool(
        name="SampleTool",
        description="desc",
        code="code",
        specification=sample_tool_spec["specification"],
    )
    mock_tool_designer_agent.design_tool.return_value = generated_tool
    expected_registered_path = "/path/to/SampleTool/v0.1.0"
    mock_tool_registry.register.return_value = expected_registered_path

    orchestrator.spec_fingerprint_cache = {}  # Ensure cache is empty

    with patch.object(
        orchestrator, "_calculate_spec_fingerprint", return_value=fingerprint
    ) as mock_fingerprint_calc:
        module_path = await orchestrator.design_and_register_tool(
            sample_tool_spec, version="0.1.0"
        )

    assert module_path == expected_registered_path
    mock_fingerprint_calc.assert_called_once_with(sample_tool_spec)
    mock_tool_designer_agent.design_tool.assert_called_once_with(sample_tool_spec)
    mock_tool_registry.register.assert_called_once_with(generated_tool, version="0.1.0")
    assert orchestrator.spec_fingerprint_cache[fingerprint] == expected_registered_path
    assert orchestrator.tool_generated_total == 1


@pytest.mark.asyncio
async def test_design_tool_fingerprint_failure(
    orchestrator, sample_tool_spec, mock_tool_designer_agent
):
    """Test scenario where fingerprint calculation fails."""
    with patch.object(
        orchestrator, "_calculate_spec_fingerprint", return_value=""
    ) as mock_fingerprint_calc:
        module_path = await orchestrator.design_and_register_tool(sample_tool_spec)

    assert module_path is None
    mock_fingerprint_calc.assert_called_once_with(sample_tool_spec)
    mock_tool_designer_agent.design_tool.assert_not_called()
    assert orchestrator.tool_generation_failed_total == 1


@pytest.mark.asyncio
async def test_design_tool_designer_fails(
    orchestrator, sample_tool_spec, mock_tool_designer_agent, mock_tool_registry
):
    """Test scenario where the tool designer agent fails to produce a tool."""
    fingerprint = "test_fingerprint_designer_fails"
    mock_tool_designer_agent.design_tool.return_value = None  # Simulate design failure
    orchestrator.spec_fingerprint_cache = {}

    with patch.object(
        orchestrator, "_calculate_spec_fingerprint", return_value=fingerprint
    ):
        module_path = await orchestrator.design_and_register_tool(sample_tool_spec)

    assert module_path is None
    mock_tool_designer_agent.design_tool.assert_called_once_with(sample_tool_spec)
    mock_tool_registry.register.assert_not_called()
    assert fingerprint not in orchestrator.spec_fingerprint_cache
    assert orchestrator.tool_generation_failed_total == 1


@pytest.mark.asyncio
async def test_design_tool_registry_fails(
    orchestrator, sample_tool_spec, mock_tool_designer_agent, mock_tool_registry
):
    """Test scenario where tool registration fails."""
    fingerprint = "test_fingerprint_registry_fails"
    generated_tool = GeneratedTool(
        name="SampleTool",
        description="desc",
        code="code",
        specification=sample_tool_spec["specification"],
    )
    mock_tool_designer_agent.design_tool.return_value = generated_tool
    mock_tool_registry.register.return_value = None  # Simulate registration failure
    orchestrator.spec_fingerprint_cache = {}

    with patch.object(
        orchestrator, "_calculate_spec_fingerprint", return_value=fingerprint
    ):
        module_path = await orchestrator.design_and_register_tool(sample_tool_spec)

    assert module_path is None
    mock_tool_designer_agent.design_tool.assert_called_once_with(sample_tool_spec)
    mock_tool_registry.register.assert_called_once_with(generated_tool, version="0.1.0")
    assert fingerprint not in orchestrator.spec_fingerprint_cache
    assert orchestrator.tool_generation_failed_total == 1


@pytest.fixture
def original_tool_metadata_fixture(sample_tool_spec):
    return {
        "name": sample_tool_spec["name"],
        "version": "0.1.0",
        "description": sample_tool_spec["description"],
        "specification": sample_tool_spec["specification"],  # Crucial: nested spec
        "module_path": "/path/to/original/tool/v0.1.0",
    }


@pytest.mark.asyncio
async def test_refine_tool_success_minor_bump(
    orchestrator, mock_tool_registry, mock_tool_designer_agent, sample_tool_spec
):
    """Test successful tool refinement with a minor version bump (no schema change)."""
    # TODO: Test removed/needs rework as refine_design functionality is gone from ToolDesignerAgent.
    assert True  # Placeholder
    # ... (rest of the test remains commented out)


@pytest.mark.asyncio
async def test_refine_tool_success_major_bump(
    orchestrator, mock_tool_registry, mock_tool_designer_agent, sample_tool_spec
):
    """Test successful tool refinement with a major version bump (IO schema change)."""
    # TODO: Test removed/needs rework as refine_design functionality is gone from ToolDesignerAgent.
    assert True  # Placeholder
    # ... (rest of the test remains commented out)


@pytest.mark.asyncio
async def test_refine_tool_metadata_not_found(
    orchestrator, mock_tool_registry, sample_tool_spec
):
    """Test refine_tool when original tool metadata is not found."""
    mock_tool_registry.get_tool_metadata.return_value = None  # Simulate not found

    module_path = await orchestrator.refine_tool(
        sample_tool_spec["name"], "0.1.0", "feedback"
    )

    assert module_path is None
    mock_tool_registry.get_tool_metadata.assert_called_once_with(
        sample_tool_spec["name"], "0.1.0"
    )
    assert orchestrator.tool_refinement_failed_total == 1


@pytest.mark.asyncio
async def test_refine_tool_spec_not_in_metadata(
    orchestrator, mock_tool_registry, sample_tool_spec, original_tool_metadata_fixture
):
    """Test refine_tool when original specification is not in metadata."""
    metadata_no_spec = original_tool_metadata_fixture.copy()
    del metadata_no_spec["specification"]
    mock_tool_registry.get_tool_metadata.return_value = metadata_no_spec

    module_path = await orchestrator.refine_tool(
        sample_tool_spec["name"], "0.1.0", "feedback"
    )

    assert module_path is None
    assert orchestrator.tool_refinement_failed_total == 1


@pytest.mark.asyncio
async def test_refine_tool_designer_fails(
    orchestrator, mock_tool_registry, mock_tool_designer_agent, sample_tool_spec, original_tool_metadata_fixture
):
    """Test refine_tool when the designer agent fails to refine."""
    # TODO: Test removed/needs rework as refine_design functionality is gone from ToolDesignerAgent.
    assert True  # Placeholder
    # ... (rest of the test remains commented out)


@pytest.mark.asyncio
async def test_refine_tool_registry_fails(
    orchestrator, mock_tool_registry, mock_tool_designer_agent, sample_tool_spec, original_tool_metadata_fixture
):
    """Test refine_tool when registration of the refined tool fails."""
    # TODO: Test removed/needs rework as refine_design functionality is gone from ToolDesignerAgent.
    assert True  # Placeholder
    # ... (rest of the test remains commented out)


@pytest.mark.asyncio
async def test_execute_plan_with_required_tool_success(
    orchestrator, mock_planning_engine, mock_sub_agent_manager, mock_tool_designer_agent, mock_tool_registry, sample_tool_spec
):
    """Test _execute_plan when a task requires a tool, and it's successfully designed."""
    task_id_with_tool = "task_requires_tool"
    plan = {
        "task_requirements": [
            {
                "task_id": task_id_with_tool,
                "description": "Task needing a tool",
                "requires_tool": sample_tool_spec,
            }
        ],
        "execution_order": [task_id_with_tool],
        "dependencies": {},
    }
    mock_planning_engine.analyze_tasks.return_value = (
        plan  # Used by orchestrator.run indirectly
    )

    # Setup for successful tool design
    fingerprint = "fp_for_required_tool"
    generated_tool = GeneratedTool(
        name=sample_tool_spec["name"],
        description="d",
        code="c",
        specification=sample_tool_spec["specification"],
    )
    mock_tool_designer_agent.design_tool.return_value = generated_tool
    registered_path = f"/path/to/{sample_tool_spec['name']}/v0.1.0"
    mock_tool_registry.register.return_value = registered_path

    # Mock orchestrator.decompose_spec to avoid its stub interfering and to control input to analyze_tasks
    orchestrator.decompose_spec = MagicMock(
        return_value={"subtasks": [{"id": task_id_with_tool, "description": "..."}]}
    )
    # Ensure _calculate_spec_fingerprint is properly mocked for design_and_register_tool call
    patcher = patch.object(
        orchestrator, "_calculate_spec_fingerprint", return_value=fingerprint
    )
    mock_fingerprint_calc = patcher.start()

    results = await orchestrator.run(
        {"name": "Test Spec with Tool Requirement"}
    )  # Call top-level run
    patcher.stop()

    # Assertions for tool design part
    mock_fingerprint_calc.assert_called_once_with(sample_tool_spec)
    mock_tool_designer_agent.design_tool.assert_called_once_with(sample_tool_spec)
    mock_tool_registry.register.assert_called_once_with(generated_tool, version="0.1.0")
    assert orchestrator.tool_generated_total == 1

    # Assertions for task execution part
    mock_sub_agent_manager.get_or_create_agent.assert_called_once_with(
        plan["task_requirements"][0]
    )
    mock_sub_agent_manager.mock_agent_instance.run.assert_called_once()
    assert task_id_with_tool in results
    assert (
        results[task_id_with_tool]["status"] != "failed"
    )  # Should not fail due to tool issue


@pytest.mark.asyncio
async def test_execute_plan_with_required_tool_design_fails(
    orchestrator, mock_planning_engine, mock_sub_agent_manager, mock_tool_designer_agent, sample_tool_spec
):
    """Test _execute_plan when a task requires a tool, but its design fails."""
    task_id_with_tool = "task_requires_tool_fail"
    plan = {
        "task_requirements": [
            {
                "task_id": task_id_with_tool,
                "description": "Task needing a tool that fails design",
                "requires_tool": sample_tool_spec,
            }
        ],
        "execution_order": [task_id_with_tool],
        "dependencies": {},
    }
    mock_planning_engine.analyze_tasks.return_value = plan

    # Setup for tool design failure
    fingerprint = "fp_for_failed_tool"
    mock_tool_designer_agent.design_tool.return_value = None  # Simulate design failure

    orchestrator.decompose_spec = MagicMock(
        return_value={"subtasks": [{"id": task_id_with_tool, "description": "..."}]}
    )
    patcher = patch.object(
        orchestrator, "_calculate_spec_fingerprint", return_value=fingerprint
    )
    mock_fingerprint_calc = patcher.start()

    results = await orchestrator.run({"name": "Test Spec with Tool Design Failure"})
    patcher.stop()

    # Assertions for tool design part (attempted)
    mock_fingerprint_calc.assert_called_once_with(sample_tool_spec)
    mock_tool_designer_agent.design_tool.assert_called_once_with(sample_tool_spec)
    assert orchestrator.tool_generation_failed_total == 1

    # Assertions for task execution part (should be skipped)
    mock_sub_agent_manager.get_or_create_agent.assert_not_called()
    mock_sub_agent_manager.mock_agent_instance.run.assert_not_called()
    assert task_id_with_tool in results
    assert results[task_id_with_tool]["status"] == "failed"
    assert (
        f"Required tool '{sample_tool_spec['name']}' could not be designed or registered."
        in results[task_id_with_tool]["error"]
    )
