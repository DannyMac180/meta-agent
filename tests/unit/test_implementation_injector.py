"""
Unit tests for the ImplementationInjector class.
"""

import pytest
from unittest.mock import MagicMock

from meta_agent.generators.implementation_injector import ImplementationInjector


class TestImplementationInjector:
    """Tests for the ImplementationInjector class."""

    @pytest.fixture
    def template_engine(self):
        """Fixture for a mock template engine."""
        engine = MagicMock()
        template_mock = MagicMock()
        template_mock.render.return_value = "def complete_tool():\\n    # Template code\\n    return implementation()"
        engine.get_template.return_value = template_mock
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
        generated_code = "def implementation():\\n    return 'Hello, World!'"

        # Call the method
        result = injector.inject(generated_code, tool_spec)

        # Check that the template engine was called correctly
        template_engine.get_template.assert_called_once_with("tool_template.j2")
        
        # Get the template mock and check it was called to render
        template_mock = template_engine.get_template.return_value
        template_mock.render.assert_called_once()
        
        # Get the render call args to check template_data
        args, kwargs = template_mock.render.call_args
        template_data = args[0] if args else kwargs
        assert "implementation" in template_data
        assert template_data["implementation"] == generated_code
        assert template_data["name"] == tool_spec.name

        # Check the result
        assert result == "def complete_tool():\\n    # Template code\\n    return implementation()"

    def test_inject_with_custom_template(self, injector, template_engine, tool_spec):
        """Test injection with a custom template."""
        generated_code = "def implementation():\\n    return 'Hello, World!'"

        # Call the method with a custom template
        result = injector.inject_with_custom_template(generated_code, tool_spec, "custom_template.py.j2")

        # Check that the template engine was called with the custom template
        template_engine.get_template.assert_called_once_with("custom_template.py.j2")
        
        # Get the template mock and check it was called to render
        template_mock = template_engine.get_template.return_value
        template_mock.render.assert_called_once()

        # Check the result
        assert result == "def complete_tool():\\n    # Template code\\n    return implementation()"

    def test_inject_empty_code(self, injector, tool_spec):
        """Test injection with empty generated code."""
        # Call the method with empty code and expect an exception
        with pytest.raises(ValueError) as excinfo:
            injector.inject("", tool_spec)

        # Check the exception message
        assert "Generated code is empty" in str(excinfo.value)

    def test_inject_template_error(self, injector, template_engine, tool_spec):
        """Test injection with template rendering error."""
        generated_code = "def implementation():\\n    return 'Hello, World!'"

        # Configure the template engine to raise an exception
        template_engine.get_template.side_effect = Exception("Template rendering failed")

        # Call the method and expect an exception
        with pytest.raises(RuntimeError) as excinfo:
            injector.inject(generated_code, tool_spec)

        # Check the exception message
        assert "Failed to render tool template" in str(excinfo.value)
        assert "Template rendering failed" in str(excinfo.value)

    def test_inject_with_custom_template_error(self, injector, template_engine, tool_spec):
        """Test injection with custom template rendering error."""
        generated_code = "def implementation():\\n    return 'Hello, World!'"

        # Configure the template engine to raise an exception
        template_engine.get_template.side_effect = Exception("Template rendering failed")

        # Call the method and expect an exception
        with pytest.raises(RuntimeError) as excinfo:
            injector.inject_with_custom_template(generated_code, tool_spec, "custom_template.py.j2")

        # Check the exception message
        assert "Failed to render custom template" in str(excinfo.value)
        assert "Template rendering failed" in str(excinfo.value)