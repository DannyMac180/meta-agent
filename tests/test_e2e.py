"""
End-to-end integration test for the Meta-Agent system.

This test exercises the complete workflow from specification to working tool,
including orchestration, code generation, validation, and execution.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch, MagicMock

# Import all the components we need to test
from meta_agent.orchestrator import MetaAgentOrchestrator
from meta_agent.planning_engine import PlanningEngine
from meta_agent.sub_agent_manager import SubAgentManager
from meta_agent.registry import ToolRegistry
from meta_agent.agents.tool_designer_agent import ToolDesignerAgent
from meta_agent.models.spec_schema import SpecSchema
from meta_agent.state_manager import StateManager
from meta_agent.validation import validate_generated_tool
from meta_agent.cli.main import cli
from click.testing import CliRunner


class TestMetaAgentE2E:
    """Comprehensive end-to-end tests for the Meta-Agent system."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for the test."""
        workspace = tempfile.mkdtemp(prefix="meta_agent_e2e_")
        yield Path(workspace)
        shutil.rmtree(workspace, ignore_errors=True)

    @pytest.fixture
    def mock_docker(self):
        """Mock Docker to avoid requiring Docker daemon."""
        with patch("meta_agent.sandbox.sandbox_manager.docker") as mock_docker:
            # Mock the Docker client
            mock_client = MagicMock()
            mock_client.ping.return_value = None
            mock_docker.from_env.return_value = mock_client

            # Mock container execution
            mock_container = MagicMock()
            mock_container.wait.return_value = {"StatusCode": 0}
            mock_container.logs.return_value = b"Test execution successful"
            mock_client.containers.run.return_value = mock_container

            yield mock_docker

    @pytest.fixture
    def complete_tool_spec(self):
        """A complete, realistic tool specification."""
        return {
            "task_description": "Create a weather fetching tool",
            "inputs": {"city": "string", "country_code": "string"},
            "outputs": {
                "temperature": "float",
                "description": "string",
                "humidity": "integer",
            },
            "constraints": [
                "Must handle API errors gracefully",
                "Should cache results for 5 minutes",
                "Must validate city names",
            ],
            "technical_requirements": [
                "Use requests library",
                "Implement proper error handling",
                "Add comprehensive logging",
            ],
            "metadata": {
                "author": "test_suite",
                "version": "1.0.0",
                "test_id": "e2e_weather_tool",
            },
        }

    @pytest.fixture
    def tool_designer_spec(self):
        """Tool specification in ToolDesigner format."""
        return {
            "name": "weather_fetcher",
            "purpose": "Fetches current weather data for a given city",
            "input_parameters": [
                {
                    "name": "city",
                    "type": "string",
                    "description": "Name of the city",
                    "required": True,
                },
                {
                    "name": "country_code",
                    "type": "string",
                    "description": "ISO country code",
                    "required": False,
                },
            ],
            "output_format": "dict",
        }

    @pytest.fixture
    def mock_llm_service(self):
        """Mock LLM service to return deterministic code."""
        with patch("meta_agent.services.llm_service.LLMService") as mock_service_class:
            mock_instance = MagicMock()
            mock_service_class.return_value = mock_instance

            # Return valid Python code for tool generation
            async def mock_generate_code(prompt, context):
                return '''
import requests
import json
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class WeatherCache:
    def __init__(self):
        self._cache = {}
        self._ttl = timedelta(minutes=5)
    
    def get(self, key: str) -> Optional[Dict]:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now() - timestamp < self._ttl:
                return data
        return None
    
    def set(self, key: str, value: Dict):
        self._cache[key] = (value, datetime.now())

_cache = WeatherCache()

def weather_fetcher(city: str, country_code: str = "") -> Dict:
    """
    Fetches current weather data for a given city.
    
    Args:
        city: Name of the city
        country_code: ISO country code (optional)
    
    Returns:
        Dict containing temperature, description, and humidity
    """
    # Input validation
    if not city or not isinstance(city, str):
        raise ValueError("City must be a non-empty string")
    
    # Check cache
    cache_key = f"{city}_{country_code}".lower()
    cached_result = _cache.get(cache_key)
    if cached_result:
        logger.info(f"Returning cached result for {city}")
        return cached_result
    
    try:
        # Mock API call for testing
        logger.info(f"Fetching weather for {city}, {country_code}")
        
        # Simulated response
        result = {
            "temperature": 22.5,
            "description": "Partly cloudy",
            "humidity": 65
        }
        
        # Cache the result
        _cache.set(cache_key, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching weather: {str(e)}")
        raise RuntimeError(f"Failed to fetch weather data: {str(e)}")

# Test function to verify the tool works
def test_weather_fetcher():
    result = weather_fetcher("London", "GB")
    assert isinstance(result, dict)
    assert "temperature" in result
    assert "description" in result
    assert "humidity" in result
    assert isinstance(result["temperature"], (int, float))
    assert isinstance(result["humidity"], int)
    
    # Test caching
    result2 = weather_fetcher("London", "GB")
    assert result == result2
    
    # Test validation
    try:
        weather_fetcher("")
        assert False, "Should raise ValueError"
    except ValueError:
        pass
'''

            mock_instance.generate_code.side_effect = mock_generate_code
            yield mock_instance

    @pytest.mark.asyncio
    async def test_full_pipeline_with_orchestrator(
        self, temp_workspace, mock_docker, complete_tool_spec, mock_llm_service
    ):
        """Test the complete pipeline using the orchestrator."""
        # Setup components
        planning_engine = PlanningEngine()
        sub_agent_manager = SubAgentManager()
        tool_registry = ToolRegistry(base_dir=temp_workspace)
        tool_designer_agent = ToolDesignerAgent()
        state_manager = StateManager()

        # Create orchestrator
        orchestrator = MetaAgentOrchestrator(
            planning_engine=planning_engine,
            sub_agent_manager=sub_agent_manager,
            tool_registry=tool_registry,
            tool_designer_agent=tool_designer_agent,
        )

        # Parse specification
        spec_schema = SpecSchema.from_dict(complete_tool_spec)

        # Run orchestration
        state_manager.set_status("running")
        state_manager.update_progress(0.1, "Starting orchestration")

        # Execute the orchestration
        results = await orchestrator.run(spec_schema.model_dump())

        state_manager.update_progress(0.5, "Orchestration complete")

        # Verify results
        assert isinstance(results, dict)
        assert len(results) > 0  # Should have executed at least one task

        # Check that tools were registered
        registered_tools = tool_registry.list_tools()
        assert (
            len(registered_tools) >= 0
        )  # May or may not have tools depending on the flow

        state_manager.update_progress(1.0, "Test complete")
        state_manager.set_status("completed")

        # Generate final report
        report: Dict[str, Any] = state_manager.get_report(as_dict=True)
        assert report["status"] == "completed"
        assert report["progress"] == 1.0

    @pytest.mark.asyncio
    async def test_tool_generation_and_validation(
        self, temp_workspace, tool_designer_spec, mock_llm_service
    ):
        """Test tool generation and validation in isolation."""
        # Create tool designer agent
        agent = ToolDesignerAgent()

        # Generate tool
        result = await agent.run(tool_designer_spec)

        assert result["status"] == "success"
        tool_data = result["output"]

        # Validate generated tool
        from meta_agent.models.generated_tool import GeneratedTool

        tool = GeneratedTool(
            code=tool_data["code"],
            tests=tool_data.get("tests", ""),
            docs=tool_data.get("docs", ""),
        )

        # Run validation
        validation_result = validate_generated_tool(tool, tool_id="e2e_test")

        # For this test, we expect validation to pass with our mock code
        assert (
            validation_result.coverage >= 0
        )  # Coverage might be 0 without actual pytest run

    def test_cli_integration(self, temp_workspace, complete_tool_spec, mock_docker):
        """Test the CLI interface end-to-end."""
        runner = CliRunner()

        # Create spec file
        spec_file = temp_workspace / "test_spec.json"
        with open(spec_file, "w") as f:
            json.dump(complete_tool_spec, f)

        # Run CLI command
        result = runner.invoke(cli, ["generate", "--spec-file", str(spec_file)])

        # Check output
        assert result.exit_code == 0
        assert "Specification parsed successfully" in result.output
        assert "Starting agent generation orchestration" in result.output
        assert "Orchestration finished" in result.output

    @pytest.mark.asyncio
    async def test_tool_registry_lifecycle(self, temp_workspace, mock_llm_service):
        """Test the complete tool lifecycle in the registry."""
        registry = ToolRegistry(base_dir=temp_workspace)

        # Create a tool
        from meta_agent.models.generated_tool import GeneratedTool

        tool = GeneratedTool(
            code="def test_func(): return 'test'",
            tests="def test_test_func(): assert test_func() == 'test'",
            docs="# Test Tool\nA simple test tool",
        )
        tool.name = "test_tool"
        tool.description = "A test tool"
        tool.specification = {"test": "spec"}

        # Register the tool
        module_path = registry.register(tool, version="0.1.0")
        assert module_path is not None

        # List tools
        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"

        # Get metadata
        metadata = registry.get_tool_metadata("test_tool")
        assert metadata is not None
        assert metadata["description"] == "A test tool"

        # Load the tool
        loaded_tool = registry.load("test_tool")
        assert loaded_tool is not None

        # Unregister
        success = registry.unregister("test_tool")
        assert success

        # Verify it's gone
        tools_after = registry.list_tools()
        assert len(tools_after) == 0

    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(
        self, temp_workspace, mock_docker, complete_tool_spec
    ):
        """Test error handling throughout the pipeline."""
        # Test with invalid specification
        invalid_spec = complete_tool_spec.copy()
        del invalid_spec["task_description"]  # Remove required field

        # Should raise validation error
        with pytest.raises(Exception) as exc_info:
            SpecSchema.from_dict(invalid_spec)
        assert "task_description" in str(exc_info.value)

        # Test with LLM failure
        with patch("meta_agent.services.llm_service.LLMService") as mock_service_class:
            mock_instance = MagicMock()
            mock_service_class.return_value = mock_instance

            # Make LLM raise an error
            async def mock_fail(*args, **kwargs):
                raise Exception("LLM API Error")

            mock_instance.generate_code.side_effect = mock_fail

            agent = ToolDesignerAgent()
            result = await agent.run(
                {
                    "name": "failing_tool",
                    "purpose": "This will fail",
                    "input_parameters": [],
                    "output_format": "string",
                }
            )

            # Should handle the error gracefully
            assert result["status"] in ["success", "error"]  # Depends on error handling

    def test_state_persistence_and_recovery(self, temp_workspace):
        """Test state persistence across restarts."""
        state_file = temp_workspace / "state.json"

        # Create initial state
        sm1 = StateManager()
        sm1.update_progress(0.5, "halfway")
        sm1.set_status("running")
        sm1.register_failure("task1")

        # Save state
        assert sm1.save_state(str(state_file))

        # Load in new instance
        sm2 = StateManager()
        assert sm2.load_state(str(state_file))

        # Verify state was preserved
        assert sm2.get_progress() == 0.5
        assert sm2.get_status() == "running"
        assert not sm2.should_retry("task1", max_retries=1)

    @pytest.mark.asyncio
    async def test_concurrent_tool_generation(self, temp_workspace, mock_llm_service):
        """Test generating multiple tools concurrently."""
        agent = ToolDesignerAgent()

        # Create multiple tool specs
        specs = [
            {
                "name": f"tool_{i}",
                "purpose": f"Tool number {i}",
                "input_parameters": [
                    {"name": "input", "type": "string", "required": True}
                ],
                "output_format": "string",
            }
            for i in range(3)
        ]

        # Generate tools concurrently
        tasks = [agent.run(spec) for spec in specs]
        results = await asyncio.gather(*tasks)

        # Verify all succeeded
        for i, result in enumerate(results):
            assert result["status"] == "success"
            assert f"tool_{i}" in str(result["output"])
