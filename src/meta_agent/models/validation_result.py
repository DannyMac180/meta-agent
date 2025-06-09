from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValidationResult:
    """
    Represents the result of validating generated code.

    This class tracks various aspects of code validation, including syntax
    correctness, security issues, and compliance with the tool specification.
    """

    # Initialize with default values
    syntax_valid: bool = False
    security_valid: bool = False
    spec_compliance: bool = False
    is_valid: bool = False

    # Detailed error information
    syntax_errors: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)
    compliance_issues: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    # For validation.py compatibility
    success: bool = False
    errors: List[str] = field(default_factory=list)
    coverage: float = 0.0


    def update_validity(self):
        """
        Update the overall validity based on individual validation results.
        """
        self.is_valid = (
            self.syntax_valid and
            self.security_valid and
            self.spec_compliance
        )
        return self.is_valid

    def add_syntax_error(self, error: str):
        """Add a syntax error and update syntax_valid."""
        self.syntax_errors.append(error)
        self.syntax_valid = False
        self.update_validity()

    def add_security_issue(self, issue: str):
        """Add a security issue and update security_valid."""
        self.security_issues.append(issue)
        self.security_valid = False
        self.update_validity()

    def add_compliance_issue(self, issue: str):
        """Add a compliance issue and update spec_compliance."""
        self.compliance_issues.append(issue)
        self.spec_compliance = False
        self.update_validity()

    def get_all_issues(self) -> List[str]:
        """Get a list of all issues found during validation."""
        all_issues = []
        all_issues.extend(self.syntax_errors)
        all_issues.extend(self.security_issues)
        all_issues.extend(self.compliance_issues)
        if self.error_message:
            all_issues.append(self.error_message)
        return all_issues
