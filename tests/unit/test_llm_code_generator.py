import pytest
from unittest.mock import AsyncMock, MagicMock

from meta_agent.generators.llm_code_generator import LLMCodeGenerator
from meta_agent.models.validation_result import ValidationResult


class TestLLMCodeGenerator:
    """Tests for the LLMCodeGenerator class."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for LLMCodeGenerator."""
        llm_service = AsyncMock()
        prompt_builder = MagicMock()
        context_builder = MagicMock()
        code_validator = MagicMock()
        implementation_injector = MagicMock()
        fallback_manager = AsyncMock()
        
        # Configure default return values
        llm_service.generate_code.return_value = "def test_function(): return 'Hello, World!'"
        prompt_builder.build_prompt.return_value = "Generate code for test function"
        context_builder.build_context.return_value = {"purpose": "Test function"}
        
        validation_result = ValidationResult()
        validation_result.syntax_valid = True
        validation_result.security_valid = True
        validation_result.spec_compliance = True
        validation_result.is_valid = True
        code_validator.validate.return_value = validation_result
        
        implementation_injector.inject.return_value = "class TestTool:\n    def execute(self):\n        return 'Hello, World!'"
        
        return {
            "llm_service": llm_service,
            "prompt_builder": prompt_builder,
            "context_builder": context_builder,
            "code_validator": code_validator,
            "implementation_injector": implementation_injector,
            "fallback_manager": fallback_manager
        }
    
    @pytest.fixture
    def code_generator(self, mock_dependencies):
        """Create an LLMCodeGenerator with mock dependencies."""
        return LLMCodeGenerator(
            llm_service=mock_dependencies["llm_service"],
            prompt_builder=mock_dependencies["prompt_builder"],
            context_builder=mock_dependencies["context_builder"],
            code_validator=mock_dependencies["code_validator"],
            implementation_injector=mock_dependencies["implementation_injector"],
            fallback_manager=mock_dependencies["fallback_manager"]
        )
    
    @pytest.fixture
    def tool_specification(self):
        """Create a mock tool specification."""
        spec = MagicMock()
        spec.name = "test_tool"
        spec.description = "A test tool"
        spec.input_params = [{"name": "test_param", "type": "string", "description": "A test parameter"}]
        spec.output_format = "string"
        spec.constraints = ["No external API calls"]
        return spec
    
    @pytest.mark.asyncio
    async def test_successful_code_generation(self, code_generator, mock_dependencies, tool_specification):
        """Test successful code generation flow."""
        # Act
        result = await code_generator.generate_code(tool_specification)
        
        # Assert
        mock_dependencies["prompt_builder"].build_prompt.assert_called_once_with(tool_specification)
        mock_dependencies["context_builder"].build_context.assert_called_once_with(tool_specification)
        mock_dependencies["llm_service"].generate_code.assert_called_once_with(
            mock_dependencies["prompt_builder"].build_prompt.return_value,
            mock_dependencies["context_builder"].build_context.return_value
        )
        mock_dependencies["code_validator"].validate.assert_called_once_with(
            mock_dependencies["llm_service"].generate_code.return_value,
            tool_specification
        )
        mock_dependencies["implementation_injector"].inject.assert_called_once_with(
            mock_dependencies["llm_service"].generate_code.return_value,
            tool_specification
        )
        assert result == mock_dependencies["implementation_injector"].inject.return_value
        # Ensure fallback manager was not called
        mock_dependencies["fallback_manager"].handle_failure.assert_not_called()
        mock_dependencies["fallback_manager"].handle_exception.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_validation_failure(self, code_generator, mock_dependencies, tool_specification):
        """Test handling of validation failures."""
        # Arrange
        invalid_validation_result = ValidationResult()
        invalid_validation_result.syntax_valid = False
        invalid_validation_result.add_syntax_error("Invalid syntax at line 1")
        invalid_validation_result.update_validity()
        
        mock_dependencies["code_validator"].validate.return_value = invalid_validation_result
        mock_dependencies["fallback_manager"].handle_failure.return_value = "def fallback_function(): pass"
        
        # Act
        result = await code_generator.generate_code(tool_specification)
        
        # Assert
        mock_dependencies["fallback_manager"].handle_failure.assert_called_once_with(
            invalid_validation_result,
            tool_specification,
            mock_dependencies["prompt_builder"].build_prompt.return_value,
            mock_dependencies["context_builder"].build_context.return_value
        )
        # Injector should not be called on validation failure
        mock_dependencies["implementation_injector"].inject.assert_not_called()
        assert result == mock_dependencies["fallback_manager"].handle_failure.return_value
    
    @pytest.mark.asyncio
    async def test_exception_handling(self, code_generator, mock_dependencies, tool_specification):
        """Test handling of exceptions during code generation."""
        # Arrange
        mock_dependencies["llm_service"].generate_code.side_effect = Exception("API error")
        mock_dependencies["fallback_manager"].handle_exception.return_value = "def error_function(): pass"
        
        # Act
        result = await code_generator.generate_code(tool_specification)
        
        # Assert
        mock_dependencies["fallback_manager"].handle_exception.assert_called_once()
        assert isinstance(mock_dependencies["fallback_manager"].handle_exception.call_args[0][0], Exception)
        assert str(mock_dependencies["fallback_manager"].handle_exception.call_args[0][0]) == "API error"
        assert mock_dependencies["fallback_manager"].handle_exception.call_args[0][1] == tool_specification
        assert result == mock_dependencies["fallback_manager"].handle_exception.return_value
    
    @pytest.mark.asyncio
    async def test_security_validation_failure(self, code_generator, mock_dependencies, tool_specification):
        """Test handling of security validation failures."""
        # Arrange
        security_validation_result = ValidationResult()
        security_validation_result.syntax_valid = True
        security_validation_result.security_valid = False
        security_validation_result.add_security_issue("Use of eval() detected")
        security_validation_result.update_validity()
        
        mock_dependencies["code_validator"].validate.return_value = security_validation_result
        mock_dependencies["fallback_manager"].handle_failure.return_value = "def secure_function(): pass"
        
        # Act
        result = await code_generator.generate_code(tool_specification)
        
        # Assert
        mock_dependencies["fallback_manager"].handle_failure.assert_called_once_with(
            security_validation_result,
            tool_specification,
            mock_dependencies["prompt_builder"].build_prompt.return_value,
            mock_dependencies["context_builder"].build_context.return_value
        )
        # Injector should not be called on security validation failure
        mock_dependencies["implementation_injector"].inject.assert_not_called()
        assert result == mock_dependencies["fallback_manager"].handle_failure.return_value
    
    @pytest.mark.asyncio
    async def test_spec_compliance_failure(self, code_generator, mock_dependencies, tool_specification):
        """Test handling of specification compliance failures."""
        # Arrange
        compliance_validation_result = ValidationResult()
        compliance_validation_result.syntax_valid = True
        compliance_validation_result.security_valid = True
        compliance_validation_result.spec_compliance = False
        compliance_validation_result.add_compliance_issue("Missing required parameter")
        compliance_validation_result.update_validity()
        
        mock_dependencies["code_validator"].validate.return_value = compliance_validation_result
        mock_dependencies["fallback_manager"].handle_failure.return_value = "def compliant_function(required_param): pass"
        
        # Act
        result = await code_generator.generate_code(tool_specification)
        
        # Assert
        mock_dependencies["fallback_manager"].handle_failure.assert_called_once_with(
            compliance_validation_result,
            tool_specification,
            mock_dependencies["prompt_builder"].build_prompt.return_value,
            mock_dependencies["context_builder"].build_context.return_value
        )
        # Injector should not be called on spec compliance failure
        mock_dependencies["implementation_injector"].inject.assert_not_called()
        assert result == mock_dependencies["fallback_manager"].handle_failure.return_value
