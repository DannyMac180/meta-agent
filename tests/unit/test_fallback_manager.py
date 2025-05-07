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
