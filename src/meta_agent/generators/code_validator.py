"""
Code Validator for LLM-generated Tool Implementations.

This module provides the CodeValidator class which validates generated code
for syntax errors, security issues, and compliance with tool specifications.
"""

import ast
import logging
import re
from typing import Any, Set

from ..models.validation_result import ValidationResult


class CodeValidator:
    """
    Validates generated code against tool specifications.
    
    This class is responsible for ensuring that generated code is syntactically
    correct, free of security issues, and complies with the tool specification.
    """
    
    def __init__(self):
        """Initialize the CodeValidator."""
        self.logger = logging.getLogger(__name__)
        
        # Patterns that might indicate security issues
        self.security_patterns = [
            (r"os\.system\(", "Direct OS command execution"),
            (r"subprocess\.", "Subprocess execution"),
            (r"eval\(", "Eval function usage"),
            (r"exec\(", "Exec function usage"),
            (r"__import__\(", "Dynamic import"),
            (r"open\([^)]*['\"]w['\"]", "File writing without validation"),
            (r"input\(", "Direct user input in tool implementation"),
            (r"pickle\.load", "Pickle loading (potential security risk)"),
            (r"yaml\.load\([^)]*Loader=None", "Unsafe YAML loading"),
            (r"request\.get\([^)]*verify=False", "SSL verification disabled"),
        ]
    
    def validate(self, generated_code: str, tool_specification: Any) -> ValidationResult:
        """
        Validate the generated code against the tool specification.
        
        This method performs comprehensive validation of the generated code,
        checking for syntax errors, security issues, and compliance with the
        tool specification.
        
        Args:
            generated_code: The generated code to validate
            tool_specification: The specification for the tool
            
        Returns:
            ValidationResult: Object containing validation results
        """
        self.logger.info("Validating generated code")
        validation_result = ValidationResult()
        
        # Validate syntax
        validation_result.syntax_valid = self._validate_syntax(generated_code, validation_result)
        
        # Only proceed with further validation if syntax is valid
        if validation_result.syntax_valid:
            # Validate security
            validation_result.security_valid = self._validate_security(generated_code, validation_result)
            
            # Validate specification compliance
            validation_result.spec_compliance = self._validate_spec_compliance(
                generated_code, tool_specification, validation_result
            )
        
        # Update overall validity
        validation_result.update_validity()
        
        if validation_result.is_valid:
            self.logger.info("Code validation passed")
        else:
            self.logger.warning(
                f"Code validation failed: {validation_result.get_all_issues()}"
            )
        
        return validation_result
    
    def _validate_syntax(self, generated_code: str, validation_result: ValidationResult) -> bool:
        """
        Validate the syntax of the generated code.
        
        This method uses Python's ast module to parse the code and check for
        syntax errors.
        
        Args:
            generated_code: The generated code to validate
            validation_result: The validation result object to update
            
        Returns:
            bool: True if syntax is valid, False otherwise
        """
        self.logger.debug("Validating code syntax")
        try:
            ast.parse(generated_code)
            return True
        except SyntaxError as e:
            error_msg = f"Syntax error at line {e.lineno}, column {e.offset}: {e.msg}"
            self.logger.error(error_msg)
            validation_result.add_syntax_error(error_msg)
            return False
        except Exception as e:
            error_msg = f"Unexpected error during syntax validation: {str(e)}"
            self.logger.error(error_msg)
            validation_result.add_syntax_error(error_msg)
            return False
    
    def _validate_security(self, generated_code: str, validation_result: ValidationResult) -> bool:
        """
        Validate the security of the generated code.
        
        This method checks for potentially dangerous patterns in the code that
        might indicate security issues.
        
        Args:
            generated_code: The generated code to validate
            validation_result: The validation result object to update
            
        Returns:
            bool: True if no security issues found, False otherwise
        """
        self.logger.debug("Validating code security")
        
        # Check for security patterns
        for pattern, description in self.security_patterns:
            matches = re.findall(pattern, generated_code)
            if matches:
                issue = f"Security issue: {description} detected"
                self.logger.warning(issue)
                validation_result.add_security_issue(issue)
        
        # Check for other security issues
        if "import socket" in generated_code and "connect" in generated_code:
            issue = "Security issue: Direct socket connection detected"
            self.logger.warning(issue)
            validation_result.add_security_issue(issue)
        
        return len(validation_result.security_issues) == 0
    
    def _validate_spec_compliance(self, generated_code: str, 
                                 tool_specification: Any, 
                                 validation_result: ValidationResult) -> bool:
        """
        Validate compliance with the tool specification.
        
        This method checks if the generated code handles the specified inputs
        and produces the expected outputs according to the tool specification.
        
        Args:
            generated_code: The generated code to validate
            tool_specification: The specification for the tool
            validation_result: The validation result object to update
            
        Returns:
            bool: True if code complies with the specification, False otherwise
        """
        self.logger.debug("Validating specification compliance")
        
        # Get input parameters from the specification
        input_params = getattr(tool_specification, 'input_params', [])
        param_names = {param.get('name', '') for param in input_params if param.get('name')}
        required_params = {param.get('name', '') for param in input_params 
                          if param.get('name') and param.get('required', False)}
        
        # Check if all required parameters are used in the code
        missing_params = self._check_missing_parameters(generated_code, required_params)
        for param in missing_params:
            issue = f"Required parameter '{param}' not used in the code"
            self.logger.warning(issue)
            validation_result.add_compliance_issue(issue)
        
        # Check if the code includes error handling
        if not self._check_error_handling(generated_code):
            issue = "No error handling detected in the code"
            self.logger.warning(issue)
            validation_result.add_compliance_issue(issue)
        
        # Check if the code includes input validation
        if not self._check_input_validation(generated_code, param_names):
            issue = "No input validation detected in the code"
            self.logger.warning(issue)
            validation_result.add_compliance_issue(issue)
        
        # Check if the code includes type hints
        if not self._check_type_hints(generated_code):
            issue = "No type hints detected in the code"
            self.logger.warning(issue)
            validation_result.add_compliance_issue(issue)
        
        # Check if the code includes docstrings
        if not self._check_docstrings(generated_code):
            issue = "No docstrings detected in the code"
            self.logger.warning(issue)
            validation_result.add_compliance_issue(issue)
        
        return len(validation_result.compliance_issues) == 0
    
    def _check_missing_parameters(self, generated_code: str, required_params: Set[str]) -> Set[str]:
        """
        Check if all required parameters are used in the code.
        
        Args:
            generated_code: The generated code to check
            required_params: Set of required parameter names
            
        Returns:
            Set[str]: Set of missing parameter names
        """
        missing_params = set()
        for param in required_params:
            # Check if the parameter name appears in the code
            if param not in generated_code:
                missing_params.add(param)
        return missing_params
    
    def _check_error_handling(self, generated_code: str) -> bool:
        """
        Check if the code includes error handling.
        
        Args:
            generated_code: The generated code to check
            
        Returns:
            bool: True if error handling is detected, False otherwise
        """
        # Check for try-except blocks
        return "try:" in generated_code and "except" in generated_code
    
    def _check_input_validation(self, generated_code: str, param_names: Set[str]) -> bool:
        """
        Check if the code includes input validation.
        
        Args:
            generated_code: The generated code to check
            param_names: Set of parameter names to check for validation
            
        Returns:
            bool: True if input validation is detected, False otherwise
        """
        # Simple heuristic: check if any parameter is checked with if statements
        for param in param_names:
            if f"if {param}" in generated_code or f"if not {param}" in generated_code:
                return True
        
        # Check for other validation patterns
        validation_patterns = [
            r"isinstance\([^,]+,\s*[^)]+\)",  # isinstance checks
            r"type\([^)]+\)\s*==",  # type checks
            r"if\s+[^:]+\s+is\s+None",  # None checks
            r"if\s+not\s+[^:]+",  # Emptiness checks
            r"if\s+len\([^)]+\)",  # Length checks
        ]
        
        for pattern in validation_patterns:
            if re.search(pattern, generated_code):
                return True
        
        return False
    
    def _check_type_hints(self, generated_code: str) -> bool:
        """
        Check if the code includes type hints.
        
        Args:
            generated_code: The generated code to check
            
        Returns:
            bool: True if type hints are detected, False otherwise
        """
        # Check for function definitions with type hints
        type_hint_pattern = r"def\s+[^(]+\([^)]*:\s*[A-Za-z][A-Za-z0-9_]*(\[[^]]+\])?"
        return bool(re.search(type_hint_pattern, generated_code))
    
    def _check_docstrings(self, generated_code: str) -> bool:
        """
        Check if the code includes docstrings.
        
        Args:
            generated_code: The generated code to check
            
        Returns:
            bool: True if docstrings are detected, False otherwise
        """
        # Check for triple-quoted strings that could be docstrings
        docstring_patterns = [r'"""[^"]*"""', r"'''[^']*'''"]
        for pattern in docstring_patterns:
            if re.search(pattern, generated_code, re.DOTALL):
                return True
        return False
