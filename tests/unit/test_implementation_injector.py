"""
Unit tests for the ImplementationInjector class.
"""

import pytest
from unittest.mock import MagicMock, patch

from meta_agent.generators.implementation_injector import ImplementationInjector


class TestImplementationInjector:
    """Tests for the ImplementationInjector class."""

    @pytest.fixture
    def template_engine(self):
        """Fixture for a mock template engine."""
        engine = MagicMock()
        engine.render_template.return_value = "def complete_tool():\n    # Template code\n    return implementation()"
        return engine

    @pytest.fixture
    def injector(self, template_engine):
        """Fixture for an ImplementationInjector instance."""
        return ImplementationInjector(template_engine)

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

    def test_initialization(self, injector, template_engine):
        """Test that the ImplementationInjector initializes correctly."""
        assert injector.template_engine == template_engine
        assert hasattr(injector, 'logger')

    def test_inject_success(self, injector, template_engine, tool_spec):
        """Test successful injection of implementation code."""
        generated_code = "def implementation():\n    return 'Hello, World!'"
        
        # Call the method
        result = injector.inject(generated_code, tool_spec)
        
        # Check that the template engine was called with the correct parameters
        template_engine.render_template.assert_called_once()
        args, kwargs = template_engine.render_template.call_args
        assert args[0] == "tool.py.j2"  # Default template
        assert "tool_spec" in kwargs
        assert kwargs["tool_spec"] == tool_spec
        assert "implementation" in kwargs
        assert kwargs["implementation"] == generated_code
        
        # Check the result
        assert result == "def complete_tool():\n    # Template code\n    return implementation()"

    def test_inject_with_custom_template(self, injector, template_engine, tool_spec):
        """Test injection with a custom template."""
        generated_code = "def implementation():\n    return 'Hello, World!'"
        
        # Set a custom template on the tool spec
        tool_spec.template = "custom_template.py.j2"
        
        # Call the method
        result = injector.inject(generated_code, tool_spec)
        
        # Check that the template engine was called with the custom template
        template_engine.render_template.assert_called_once()
        args, kwargs = template_engine.render_template.call_args
        assert args[0] == "custom_template.py.j2"
        
        # Check the result
        assert result == "def complete_tool():\n    # Template code\n    return implementation()"

    def test_inject_empty_code(self, injector, tool_spec):
        """Test injection with empty generated code."""
        # Call the method with empty code and expect an exception
        with pytest.raises(ValueError) as excinfo:
            injector.inject("", tool_spec)
        
        # Check the exception message
        assert "Generated code is empty" in str(excinfo.value)

    def test_inject_template_error(self, injector, template_engine, tool_spec):
        """Test injection with template rendering error."""
        generated_code = "def implementation():\n    return 'Hello, World!'"
        
        # Configure the template engine to raise an exception
        template_engine.render_template.side_effect = Exception("Template rendering failed")
        
        # Call the method and expect an exception
        with pytest.raises(RuntimeError) as excinfo:
            injector.inject(generated_code, tool_spec)
        
        # Check the exception message
        assert "Failed to render template" in str(excinfo.value)
        assert "Template rendering failed" in str(excinfo.value)

    def test_inject_with_additional_context(self, injector, template_engine, tool_spec):
        """Test injection with additional context variables."""
        generated_code = "def implementation():\n    return 'Hello, World!'"
        additional_context = {"extra_var": "extra_value"}
        
        # Call the method with additional context
        result = injector.inject(generated_code, tool_spec, additional_context)
        
        # Check that the template engine was called with the additional context
        template_engine.render_template.assert_called_once()
        args, kwargs = template_engine.render_template.call_args
        assert "extra_var" in kwargs
        assert kwargs["extra_var"] == "extra_value"
        
        # Check the result
        assert result == "def complete_tool():\n    # Template code\n    return implementation()"
