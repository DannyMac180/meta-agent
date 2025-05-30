import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from meta_agent.generators.llm_code_generator import LLMCodeGenerator
from meta_agent.generators.prompt_builder import PromptBuilder
from meta_agent.generators.context_builder import ContextBuilder
from meta_agent.generators.code_validator import CodeValidator
from meta_agent.generators.implementation_injector import ImplementationInjector
from meta_agent.generators.fallback_manager import FallbackManager
from meta_agent.models.validation_result import ValidationResult


class TestLLMCodeGenerationIntegration:
    """Integration tests for the LLM-backed code generation pipeline."""

    @pytest.fixture(scope="function")
    def mock_llm_service(self, request):
        """Create a mock LLM service that returns predefined responses."""
        # Use patch as a function instead of a context manager to ensure proper cleanup
        patcher = patch('meta_agent.services.llm_service.LLMService', autospec=True)
        mock_service_cls = patcher.start()
        
        # Add finalizer to ensure patch is stopped after the test
        request.addfinalizer(patcher.stop)
        
        mock_service = AsyncMock()
        mock_service_cls.return_value = mock_service
        
        # Configure the mock to return different responses based on the prompt
        async def mock_generate_code(prompt, context):
            if "api_caller" in prompt.lower():
                return """  
import requests
from typing import Dict, Any, Optional

def execute(url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    '''
    Make an API request to the specified URL.
    
    Args:
        url: The URL to make the request to
        headers: Optional headers to include in the request
        
    Returns:
        Dict containing the API response data
    '''
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return {
            "status": "success",
            "data": response.json(),
            "status_code": response.status_code
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "error": str(e),
            "status_code": getattr(e.response, "status_code", None)
        }
"""
            elif "syntax_error" in prompt.lower():
                return """  
def execute(file_path:
    # Missing closing parenthesis
    with open(file_path, 'r') as f:
        content = f.read()
    return content
"""
            elif "security_issue" in prompt.lower():
                return """  
import os

def execute(command: str):
    # Potential security risk with os.system
    return os.system(command)
"""
            elif "greet_user" in prompt.lower():
                return """  
from typing import Dict, Any

def execute(name: str) -> Dict[str, Any]:
    '''
    Greet the user by name.
    
    Args:
        name: The name of the user to greet
        
    Returns:
        Dict containing the greeting message
    '''
    return {
        "status": "success",
        "message": f"Hello, {name}!"
    }
"""
            else:
                return """  
from typing import Dict, Any

def execute(name: str) -> Dict[str, Any]:
    '''
    Greet the user by name. (Default fallback)
    
    Args:
        name: The name of the user to greet
        
    Returns:
        Dict containing the greeting message
    '''
    return {
        "status": "success",
        "message": f"Hello, {name}!"
    }
"""
        
        mock_service.generate_code.side_effect = mock_generate_code
        return mock_service

    @pytest.fixture
    def template_engine(self):
        """Create a mock template engine."""
        mock_engine = MagicMock()
        mock_engine.render.side_effect = lambda template_name, data: f"# Generated Tool: {data['name']}\n\n{data['implementation']}"
        return mock_engine

    @pytest.fixture
    def llm_components(self, mock_llm_service, template_engine):
        """Create and wire all the LLM-backed code generation components."""
        mock_prompt_builder = MagicMock(spec=PromptBuilder)
        mock_context_builder = MagicMock(spec=ContextBuilder)
        mock_code_validator = MagicMock(spec=CodeValidator)
        mock_implementation_injector = MagicMock(spec=ImplementationInjector)
        # FallbackManager has async methods like handle_failure and handle_exception
        mock_fallback_manager = AsyncMock(spec=FallbackManager)
        
        # Configure build_prompt to generate tool-specific triggers for mock service
        def build_prompt_side_effect(tool_spec):
            name = getattr(tool_spec, 'name', '')
            if name == 'api_requester':
                return 'api_caller'
            if name == 'greeter':
                return 'greet_user'
            if name == 'syntax_error_tool':
                return 'syntax_error'
            if name == 'security_issue_tool':
                return 'security_issue'
            return ''
        mock_prompt_builder.build_prompt.side_effect = build_prompt_side_effect
        
        mock_context_builder.build_context.return_value = {"default_context_key": "default_context_value"}
        
        valid_result = ValidationResult()
        valid_result.syntax_valid = True
        valid_result.security_valid = True
        valid_result.spec_compliance = True  # ensure overall validity is True to skip fallback
        valid_result.update_validity()
        mock_code_validator.validate.return_value = valid_result
        
        # Define the side effect for mock_implementation_injector.inject
        # It should use the 'template_engine' fixture to mimic real behavior
        def mock_inject_side_effect(implementation_code: str, tool_spec):
            # Extract name from spec object or dict
            if hasattr(tool_spec, 'name'):
                name = tool_spec.name
            else:
                name = tool_spec.get('name')
            return template_engine.render(
                "tool_template.py.jinja",
                {"name": name, "implementation": implementation_code}
            )
        mock_implementation_injector.inject.side_effect = mock_inject_side_effect
        
        # Default behavior for fallback manager's async methods if needed
        # These return values will be used unless overridden in a specific test
        # Default fallback for validation failures (syntax errors)
        mock_fallback_manager.handle_failure.return_value = "def execute(file_path: str): return 'Fixed implementation'"
        mock_fallback_manager.handle_exception.return_value = "Default Fallback Exception Code From Fixture"

        llm_code_generator = LLMCodeGenerator(
            llm_service=mock_llm_service,  # This is the AsyncMock instance from the mock_llm_service fixture
            prompt_builder=mock_prompt_builder,
            context_builder=mock_context_builder,
            code_validator=mock_code_validator,
            implementation_injector=mock_implementation_injector,
            fallback_manager=mock_fallback_manager
        )
        return {
            "llm_code_generator": llm_code_generator,
            "llm_service": mock_llm_service, 
            "prompt_builder": mock_prompt_builder,
            "context_builder": mock_context_builder,
            "code_validator": mock_code_validator,
            "implementation_injector": mock_implementation_injector,
            "template_engine": template_engine,
            "fallback_manager": mock_fallback_manager,
        }

    @pytest.fixture
    def api_tool_spec(self):
        """Create a specification for an API tool."""
        class ToolSpec:
            def __init__(self):
                self.name = "api_requester"
                self.description = "Makes HTTP requests to APIs"
                self.input_params = [
                    {"name": "url", "type": "string", "description": "API endpoint URL", "required": True},
                    {"name": "headers", "type": "dict", "description": "HTTP headers", "required": False}
                ]
                self.output_format = "JSON response data"
                self.constraints = ["Handle API errors gracefully", "Implement timeout"]
        
        return ToolSpec()

    @pytest.fixture
    def greeting_tool_spec(self):
        """Create a specification for a simple greeting tool."""
        class ToolSpec:
            def __init__(self):
                self.name = "greeter"
                self.description = "Greets the user by name"
                self.input_params = [
                    {"name": "name", "type": "string", "description": "User's name", "required": True}
                ]
                self.output_format = "Greeting message"
                self.constraints = ["Be polite", "Handle empty names"]
        
        return ToolSpec()

    @pytest.fixture
    def syntax_error_tool_spec(self):
        """Create a specification for a tool that will trigger syntax errors."""
        class ToolSpec:
            def __init__(self):
                self.name = "syntax_error_tool"
                self.description = "This tool will have syntax errors in its implementation"
                self.input_params = [
                    {"name": "file_path", "type": "string", "description": "Path to a file", "required": True}
                ]
                self.output_format = "File contents"
                self.constraints = ["Handle file not found errors"]
        
        return ToolSpec()

    @pytest.fixture
    def security_issue_tool_spec(self):
        """Create a specification for a tool that will trigger security issues."""
        class ToolSpec:
            def __init__(self):
                self.name = "security_issue_tool"
                self.description = "This tool will have security issues in its implementation"
                self.input_params = [
                    {"name": "command", "type": "string", "description": "Command to execute", "required": True}
                ]
                self.output_format = "Command output"
                self.constraints = ["Be secure", "Validate inputs"]
        
        return ToolSpec()

    @pytest.mark.asyncio
    async def test_generate_api_tool_code(self, llm_components, api_tool_spec):
        """Test generating code for an API tool."""
        # Act
        generated_code = await llm_components["llm_code_generator"].generate_code(api_tool_spec)
        
        # Assert
        assert generated_code is not None
        assert "# Generated Tool: api_requester" in generated_code
        assert "import requests" in generated_code
        assert "def execute(url:" in generated_code
        assert "response = requests.get" in generated_code
        assert "raise_for_status" in generated_code
        assert "try:" in generated_code
        assert "except" in generated_code

    @pytest.mark.asyncio
    async def test_generate_greeting_tool_code(self, llm_components, greeting_tool_spec):
        """Test generating code for a simple greeting tool."""
        # Act
        generated_code = await llm_components["llm_code_generator"].generate_code(greeting_tool_spec)
        
        # Assert
        assert generated_code is not None
        assert "# Generated Tool: greeter" in generated_code
        assert "def execute(name:" in generated_code
        assert "Hello" in generated_code

    @pytest.mark.asyncio
    async def test_handle_syntax_error(self, llm_components, syntax_error_tool_spec):
        """Test handling syntax errors in generated code."""
        # Arrange - patch the code validator to simulate a syntax error
        with patch.object(llm_components["code_validator"], "validate") as mock_validate:
            invalid_result = ValidationResult()
            invalid_result.syntax_valid = False
            invalid_result.add_syntax_error("Missing closing parenthesis on line 1")
            invalid_result.update_validity()
            mock_validate.return_value = invalid_result
            
            # Also patch the fallback manager to return a fixed implementation
            llm_components["fallback_manager"].handle_failure.return_value = "def execute(file_path: str): return 'Fixed implementation'"
            
            # Act
            generated_code = await llm_components["llm_code_generator"].generate_code(syntax_error_tool_spec)
            
            # Assert
            assert generated_code is not None
            assert generated_code == "def execute(file_path: str): return 'Fixed implementation'"
            llm_components["fallback_manager"].handle_failure.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_security_issue(self, llm_components, security_issue_tool_spec):
        """Test handling security issues in generated code."""
        # Arrange - patch the code validator to simulate a security issue
        with patch.object(llm_components["code_validator"], "validate") as mock_validate:
            invalid_result = ValidationResult()
            invalid_result.syntax_valid = True
            invalid_result.security_valid = False
            invalid_result.add_security_issue("Direct OS command execution detected")
            invalid_result.update_validity()
            mock_validate.return_value = invalid_result
            
            # Also patch the fallback manager to return a fixed implementation
            llm_components["fallback_manager"].handle_failure.return_value = "def execute(command: str): return f'Would execute: {command}'"
            
            # Act
            generated_code = await llm_components["llm_code_generator"].generate_code(security_issue_tool_spec)
            
            # Assert
            assert generated_code is not None
            assert generated_code == "def execute(command: str): return f'Would execute: {command}'"
            llm_components["fallback_manager"].handle_failure.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_llm_service_exception(self, llm_components, greeting_tool_spec):
        """Test handling exceptions from the LLM service."""
        # Arrange - patch the LLM service to raise an exception
        llm_components["llm_service"].generate_code.side_effect = Exception("API rate limit exceeded")
        llm_components["fallback_manager"].handle_exception.return_value = "def execute(name: str): return {'message': 'Hello from fallback'}"
        
        # Act
        generated_code = await llm_components["llm_code_generator"].generate_code(greeting_tool_spec)
        
        # Assert
        assert generated_code is not None
        assert generated_code == "def execute(name: str): return {'message': 'Hello from fallback'}"
        llm_components["fallback_manager"].handle_exception.assert_called_once()

    @pytest.mark.asyncio
    async def test_end_to_end_code_generation(self, llm_components, api_tool_spec):
        """Test the complete end-to-end code generation pipeline."""
        # Act
        generated_code = await llm_components["llm_code_generator"].generate_code(api_tool_spec)
        
        # Assert - verify all components were called in the correct order
        llm_components["prompt_builder"].build_prompt.assert_called_once_with(api_tool_spec)
        llm_components["context_builder"].build_context.assert_called_once_with(api_tool_spec)
        llm_components["llm_service"].generate_code.assert_called_once()
        llm_components["code_validator"].validate.assert_called_once()
        llm_components["implementation_injector"].inject.assert_called_once()
        
        # Verify the generated code
        assert generated_code is not None
        assert "# Generated Tool: api_requester" in generated_code
        assert "import requests" in generated_code
