"""
Unit tests for the CodeValidator class.
"""

import pytest
from unittest.mock import MagicMock, patch

from meta_agent.generators.code_validator import CodeValidator
from meta_agent.models.validation_result import ValidationResult


class TestCodeValidator:
    """Tests for the CodeValidator class."""

    @pytest.fixture
    def validator(self):
        """Fixture for a CodeValidator instance."""
        return CodeValidator()

    @pytest.fixture
    def mock_tool_spec(self):
        """Fixture for a mock tool specification."""
        spec = MagicMock()
        spec.input_params = [
            {"name": "param1", "required": True},
            {"name": "param2", "required": False}
        ]
        return spec

    def test_initialization(self, validator):
        """Test that the CodeValidator initializes correctly."""
        assert hasattr(validator, 'security_patterns')
        assert len(validator.security_patterns) > 0
        assert hasattr(validator, 'logger')

    def test_validate_syntax_valid(self, validator):
        """Test syntax validation with valid code."""
        code = "def test_function():\n    return 'Hello, World!'"
        validation_result = ValidationResult()

        result = validator._validate_syntax(code, validation_result)

        assert result is True
        # The _validate_syntax method doesn't set syntax_valid directly
        # It only returns True/False and adds errors if needed
        assert len(validation_result.syntax_errors) == 0

    def test_validate_syntax_invalid(self, validator):
        """Test syntax validation with invalid code."""
        code = "def test_function():\n    return 'Hello, World!"  # Missing closing quote
        validation_result = ValidationResult()

        result = validator._validate_syntax(code, validation_result)

        assert result is False
        assert validation_result.syntax_valid is False
        assert len(validation_result.syntax_errors) > 0

    def test_validate_security_no_issues(self, validator):
        """Test security validation with no security issues."""
        code = "def test_function(param):\n    return param.upper()"
        validation_result = ValidationResult()

        result = validator._validate_security(code, validation_result)

        assert result is True
        assert len(validation_result.security_issues) == 0

    def test_validate_security_with_issues(self, validator):
        """Test security validation with security issues."""
        code = "def test_function(param):\n    return os.system(param)"
        validation_result = ValidationResult()

        result = validator._validate_security(code, validation_result)

        assert result is False
        assert len(validation_result.security_issues) > 0
        assert "Direct OS command execution" in validation_result.security_issues[0]

    def test_validate_security_with_socket(self, validator):
        """Test security validation with socket usage."""
        code = "import socket\n\ndef test_function(param):\n    s = socket.socket()\n    s.connect((param, 80))"
        validation_result = ValidationResult()

        result = validator._validate_security(code, validation_result)

        assert result is False
        assert len(validation_result.security_issues) > 0
        assert "Direct socket connection" in validation_result.security_issues[0]

    def test_validate_spec_compliance_all_good(self, validator, mock_tool_spec):
        """Test spec compliance validation with all requirements met."""
        code = """
        def test_function(param1, param2=None):
            '''
            This is a docstring.
            '''
            if param1 is None:
                raise ValueError("param1 cannot be None")
            try:
                return param1 + (param2 or 0)
            except Exception as e:
                raise ValueError(f"Error: {e}")
        """
        validation_result = ValidationResult()

        # Mock the private methods to return True
        with patch.object(validator, '_check_missing_parameters', return_value=set()):
            with patch.object(validator, '_check_error_handling', return_value=True):
                with patch.object(validator, '_check_input_validation', return_value=True):
                    with patch.object(validator, '_check_type_hints', return_value=True):
                        with patch.object(validator, '_check_docstrings', return_value=True):
                            result = validator._validate_spec_compliance(code, mock_tool_spec, validation_result)

        assert result is True
        assert len(validation_result.compliance_issues) == 0

    def test_validate_spec_compliance_missing_params(self, validator, mock_tool_spec):
        """Test spec compliance validation with missing parameters."""
        code = "def test_function(param2=None):\n    return param2"
        validation_result = ValidationResult()

        # Mock only _check_missing_parameters to return a non-empty set
        with patch.object(validator, '_check_missing_parameters', return_value={'param1'}):
            with patch.object(validator, '_check_error_handling', return_value=True):
                with patch.object(validator, '_check_input_validation', return_value=True):
                    with patch.object(validator, '_check_type_hints', return_value=True):
                        with patch.object(validator, '_check_docstrings', return_value=True):
                            result = validator._validate_spec_compliance(code, mock_tool_spec, validation_result)

        assert result is False
        assert len(validation_result.compliance_issues) > 0
        assert "Required parameter 'param1' not used in the code" in validation_result.compliance_issues[0]

    def test_check_missing_parameters(self, validator):
        """Test checking for missing parameters."""
        code = "def test_function(param1, param3):\n    return param1 + param3"
        required_params = {'param1', 'param2'}

        result = validator._check_missing_parameters(code, required_params)

        assert result == {'param2'}

    def test_check_error_handling_present(self, validator):
        """Test checking for error handling when present."""
        code = "def test_function():\n    try:\n        return 1\n    except Exception:\n        return 0"

        result = validator._check_error_handling(code)

        assert result is True

    def test_check_error_handling_absent(self, validator):
        """Test checking for error handling when absent."""
        code = "def test_function():\n    return 1"

        result = validator._check_error_handling(code)

        assert result is False

    def test_check_input_validation_present(self, validator):
        """Test checking for input validation when present."""
        code = "def test_function(param):\n    if param is None:\n        raise ValueError('param cannot be None')"
        param_names = {'param'}

        result = validator._check_input_validation(code, param_names)

        assert result is True

    def test_check_input_validation_absent(self, validator):
        """Test checking for input validation when absent."""
        code = "def test_function(param):\n    return param"
        param_names = {'param'}

        result = validator._check_input_validation(code, param_names)

        assert result is False

    def test_check_input_validation_with_isinstance(self, validator):
        """Test checking for input validation with isinstance."""
        code = "def test_function(param):\n    if isinstance(param, str):\n        return param.upper()"
        param_names = {'param'}

        result = validator._check_input_validation(code, param_names)

        assert result is True

    def test_check_type_hints_present(self, validator):
        """Test checking for type hints when present."""
        code = "def test_function(param: str) -> str:\n    return param.upper()"

        result = validator._check_type_hints(code)

        assert result is True

    def test_check_type_hints_absent(self, validator):
        """Test checking for type hints when absent."""
        code = "def test_function(param):\n    return param.upper()"

        result = validator._check_type_hints(code)

        assert result is False

    def test_check_docstrings_present(self, validator):
        """Test checking for docstrings when present."""
        code = 'def test_function():\n    """This is a docstring."""\n    return 1'

        result = validator._check_docstrings(code)

        assert result is True

    def test_check_docstrings_absent(self, validator):
        """Test checking for docstrings when absent."""
        code = "def test_function():\n    return 1"

        result = validator._check_docstrings(code)

        assert result is False

    def test_validate_full_integration(self, validator, mock_tool_spec):
        """Test the full validate method integration."""
        code = "def test_function(param1: str, param2: int = 0) -> str:\n    '''\n    This is a docstring.\n    \n    Args:\n        param1: The first parameter\n        param2: The second parameter\n        \n    Returns:\n        A string result\n    '''\n    if param1 is None:\n        raise ValueError(\"param1 cannot be None\")\n    \n    try:\n        return str(param1) + str(param2)\n    except Exception as e:\n        raise ValueError(f\"Error: {e}\")\n"

        result = validator.validate(code, mock_tool_spec)

        assert result.is_valid
        assert result.syntax_valid
        assert result.security_valid
        assert result.spec_compliance
        assert len(result.get_all_issues()) == 0

    def test_validate_with_syntax_error(self, validator, mock_tool_spec):
        """Test validate method with syntax error."""
        code = "def test_function(param1, param2)\n    return param1 + param2"  # Missing colon

        result = validator.validate(code, mock_tool_spec)

        assert not result.is_valid
        assert not result.syntax_valid
        assert len(result.syntax_errors) > 0

    def test_validate_with_security_issue(self, validator, mock_tool_spec):
        """Test validate method with security issue."""
        code = "def test_function(param1, param2=None):\n    '''\n    This is a docstring.\n    '''\n    if param1 is None:\n        raise ValueError(\"param1 cannot be None\")\n    try:\n        return eval(param1)\n    except Exception as e:\n        raise ValueError(f\"Error: {e}\")\n"

        result = validator.validate(code, mock_tool_spec)

        assert not result.is_valid
        assert result.syntax_valid
        assert not result.security_valid
        assert len(result.security_issues) > 0
        assert "Eval function usage" in result.security_issues[0]
