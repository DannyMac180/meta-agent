"""
Unit tests for the FallbackManager class.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from meta_agent.generators.fallback_manager import FallbackManager
from meta_agent.models.validation_result import ValidationResult


class TestFallbackManager:
    """Tests for the FallbackManager class."""

    @pytest.fixture
    def llm_service(self):
        """Fixture for a mock LLM service."""
        service = AsyncMock()
        service.generate_code = AsyncMock(return_value="def fixed_function():\n    return 'fixed'")
        return service

    @pytest.fixture
    def llm_service_with_exception(self):
        """Fixture for a mock LLM service that raises an exception."""
        service = AsyncMock()
        service.generate_code = AsyncMock(side_effect=Exception("LLM service error"))
        return service

    @pytest.fixture
    def prompt_builder(self):
        """Fixture for a mock prompt builder."""
        builder = MagicMock()
        builder.build_prompt = MagicMock(return_value="Fixed prompt")
        return builder

    @pytest.fixture
    def manager(self, llm_service, prompt_builder):
        """Fixture for a FallbackManager instance."""
        return FallbackManager(llm_service, prompt_builder)

    @pytest.fixture
    def manager_with_exception(self, llm_service_with_exception, prompt_builder):
        """Fixture for a FallbackManager instance with an LLM service that raises exceptions."""
        return FallbackManager(llm_service_with_exception, prompt_builder)

    @pytest.fixture
    def validation_result_syntax_error(self):
        """Fixture for a validation result with syntax errors."""
        result = ValidationResult()
        result.syntax_valid = False
        result.syntax_errors = ["Missing closing parenthesis on line 5"]
        return result

    @pytest.fixture
    def validation_result_security_issue(self):
        """Fixture for a validation result with security issues."""
        result = ValidationResult()
        result.syntax_valid = True
        result.security_valid = False
        result.security_issues = ["Eval function usage detected"]
        return result

    @pytest.fixture
    def validation_result_compliance_issue(self):
        """Fixture for a validation result with compliance issues."""
        result = ValidationResult()
        result.syntax_valid = True
        result.security_valid = True
        result.spec_compliance = False
        result.compliance_issues = ["Missing required parameter 'param1'"]
        return result

    @pytest.fixture
    def tool_spec(self):
        """Fixture for a mock tool specification."""
        spec = MagicMock()
        spec.name = "test_tool"
        spec.description = "A test tool"
        spec.input_params = [
            {"name": "param1", "type": "string", "description": "First parameter", "required": True},
            {"name": "param2", "type": "integer", "description": "Second parameter", "required": False}
        ]
        return spec

    @pytest.mark.asyncio
    async def test_handle_failure_syntax_error(self, manager, validation_result_syntax_error, tool_spec):
        """Test handling a syntax error failure."""
        # Mock the _handle_syntax_error method
        with patch.object(manager, '_handle_syntax_error', new=AsyncMock(return_value="def fixed_function():\n    return 'fixed'")):
            # Call the method
            fixed_code = await manager.handle_failure(
                validation_result_syntax_error,
                tool_spec,
                "Original prompt",
                {"context": "data"}
            )

            # Check that the correct handler was called
            manager._handle_syntax_error.assert_called_once_with(
                validation_result_syntax_error,
                tool_spec,
                "Original prompt",
                {"context": "data"}
            )

            # Check the result
            assert fixed_code == "def fixed_function():\n    return 'fixed'"

    @pytest.mark.asyncio
    async def test_handle_failure_security_issue(self, manager, validation_result_security_issue, tool_spec):
        """Test handling a security issue failure."""
        # Mock the _handle_security_issue method
        with patch.object(manager, '_handle_security_issue', new=AsyncMock(return_value="def fixed_function():\n    return 'fixed'")):
            # Call the method
            fixed_code = await manager.handle_failure(
                validation_result_security_issue,
                tool_spec,
                "Original prompt",
                {"context": "data"}
            )

            # Check that the correct handler was called
            manager._handle_security_issue.assert_called_once_with(
                validation_result_security_issue,
                tool_spec,
                "Original prompt",
                {"context": "data"}
            )

            # Check the result
            assert fixed_code == "def fixed_function():\n    return 'fixed'"

    @pytest.mark.asyncio
    async def test_handle_failure_compliance_issue(self, manager, validation_result_compliance_issue, tool_spec):
        """Test handling a compliance issue failure."""
        # Mock the _handle_spec_compliance_issue method
        with patch.object(manager, '_handle_spec_compliance_issue', new=AsyncMock(return_value="def fixed_function():\n    return 'fixed'")):
            # Call the method
            fixed_code = await manager.handle_failure(
                validation_result_compliance_issue,
                tool_spec,
                "Original prompt",
                {"context": "data"}
            )

            # Check that the correct handler was called
            manager._handle_spec_compliance_issue.assert_called_once_with(
                validation_result_compliance_issue,
                tool_spec,
                "Original prompt",
                {"context": "data"}
            )

            # Check the result
            assert fixed_code == "def fixed_function():\n    return 'fixed'"

    @pytest.mark.asyncio
    async def test_handle_failure_unknown_issue(self, manager, tool_spec):
        """Test handling an unknown issue failure."""
        # Create a validation result with an unknown issue
        result = ValidationResult()
        result.syntax_valid = True
        result.security_valid = True
        result.spec_compliance = True
        result.is_valid = False  # Still invalid for some reason

        # Mock the _generate_simple_implementation method
        with patch.object(manager, '_generate_simple_implementation', new=AsyncMock(return_value="def fixed_function():\n    return 'fixed'")):
            # Call the method
            fixed_code = await manager.handle_failure(
                result,
                tool_spec,
                "Original prompt",
                {"context": "data"}
            )

            # Check that the correct handler was called
            manager._generate_simple_implementation.assert_called_once_with(tool_spec)

            # Check the result
            assert fixed_code == "def fixed_function():\n    return 'fixed'"

    @pytest.mark.asyncio
    async def test_handle_exception(self, manager, tool_spec):
        """Test handling an exception during code generation."""
        # Create an exception
        exception = Exception("Code generation failed")

        # Mock the methods used in handle_exception
        with patch.object(manager, '_create_simplified_prompt', return_value="Simplified prompt"):
            with patch.object(manager, '_simplify_context', return_value={"simplified": "context"}):
                # Call the method
                fixed_code = await manager.handle_exception(exception, tool_spec, "Original prompt", {"context": "data"})

                # Check that the LLM service was called with the simplified prompt and context
                manager.llm_service.generate_code.assert_called_once_with("Simplified prompt", {"simplified": "context"})

                # Check the result
                assert fixed_code == "def fixed_function():\n    return 'fixed'"

    @pytest.mark.asyncio
    async def test_handle_exception_with_fallback(self, manager_with_exception, tool_spec):
        """Test handling an exception with fallback to template-based implementation."""
        # Create an exception
        exception = Exception("Code generation failed")

        # Mock the methods used in handle_exception
        with patch.object(manager_with_exception, '_create_simplified_prompt', return_value="Simplified prompt"):
            with patch.object(manager_with_exception, '_simplify_context', return_value={"simplified": "context"}):
                with patch.object(manager_with_exception, '_create_template_based_implementation', return_value="def template_function():\n    return 'template'"):
                    # Call the method
                    fixed_code = await manager_with_exception.handle_exception(exception, tool_spec, "Original prompt", {"context": "data"})

                    # Check that the LLM service was called with the simplified prompt and context
                    manager_with_exception.llm_service.generate_code.assert_called_once_with("Simplified prompt", {"simplified": "context"})

                    # Check that the template-based implementation was used
                    manager_with_exception._create_template_based_implementation.assert_called_once_with(tool_spec)

                    # Check the result
                    assert fixed_code == "def template_function():\n    return 'template'"

    @pytest.mark.asyncio
    async def test_create_simplified_prompt(self, manager, tool_spec):
        """Test creating a simplified prompt."""
        # Call the method
        simplified_prompt = manager._create_simplified_prompt(tool_spec)

        # Check that the simplified prompt contains the tool name and is a string
        assert isinstance(simplified_prompt, str)
        assert tool_spec.name in simplified_prompt

    def test_simplify_context(self, manager):
        """Test simplifying the context."""
        # Create a complex context
        context = {
            "tool_purpose": "A complex tool purpose with lots of details",
            "input_output_formats": {
                "inputs": [
                    {"name": "param1", "type": "string", "description": "First parameter", "required": True},
                    {"name": "param2", "type": "integer", "description": "Second parameter", "required": False}
                ],
                "output": {"description": "Output description", "type": "string"}
            },
            "similar_examples": ["Example 1", "Example 2", "Example 3"],
            "best_practices": ["Practice 1", "Practice 2", "Practice 3"],
            "constraints": ["Constraint 1", "Constraint 2"]
        }

        # Call the method
        simplified_context = manager._simplify_context(context)

        # Check that the simplified context is simpler than the original
        assert isinstance(simplified_context, dict)
        assert len(simplified_context) <= len(context)

        # Check that essential fields are preserved
        if "tool_purpose" in context:
            assert "tool_purpose" in simplified_context
        if "constraints" in context:
            assert "constraints" in simplified_context

    def test_create_template_based_implementation(self, manager, tool_spec):
        """Test creating a template-based implementation."""
        # Set up the tool spec with API-related keywords
        tool_spec.name = "api_tool"
        tool_spec.description = "A tool that makes API requests"
        tool_spec.input_params = [{"name": "url", "required": True}]

        # Call the method
        implementation = manager._create_template_based_implementation(tool_spec)

        # Check that the implementation is a string and contains the expected elements
        assert isinstance(implementation, str)
        assert "import requests" in implementation
        assert "def execute" in implementation
        assert "url: str" in implementation

    def test_create_data_processor_template(self, manager, tool_spec):
        """Test creating a data processor template."""
        # Set up the tool spec with data processing keywords
        tool_spec.name = "data_processor"
        tool_spec.description = "A tool that processes data"
        tool_spec.input_params = [{"name": "data", "required": True}]

        # Call the method
        implementation = manager._create_data_processor_template(tool_spec, ["data"])

        # Check that the implementation is a string and contains the expected elements
        assert isinstance(implementation, str)
        assert "def execute" in implementation
        assert "data: Any" in implementation

    def test_create_file_manipulator_template(self, manager, tool_spec):
        """Test creating a file manipulator template."""
        # Set up the tool spec with file manipulation keywords
        tool_spec.name = "file_tool"
        tool_spec.description = "A tool that manipulates files"
        tool_spec.input_params = [{"name": "file_path", "required": True}]

        # Call the method
        implementation = manager._create_file_manipulator_template(tool_spec, ["file_path"])

        # Check that the implementation is a string and contains the expected elements
        assert isinstance(implementation, str)
        assert "def execute" in implementation
        assert "file_path: str" in implementation

    def test_create_default_template(self, manager, tool_spec):
        """Test creating a default template."""
        # Set up the tool spec with generic keywords
        tool_spec.name = "generic_tool"
        tool_spec.description = "A generic tool"
        tool_spec.input_params = [{"name": "input", "required": True}]

        # Call the method
        implementation = manager._create_default_template(tool_spec, ["input"])

        # Check that the implementation is a string and contains the expected elements
        assert isinstance(implementation, str)
        assert "def execute" in implementation
        assert "input: Any" in implementation
