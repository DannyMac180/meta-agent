from typing import Any, Dict, Tuple
from jinja2 import Environment, FileSystemLoader, Template
import os
import ast


class TemplateEngine:
    """
    Combines sub-agent outputs into a final agent implementation using Jinja2 templates.
    """

    def __init__(self, templates_dir: str | None = None):
        if templates_dir is None:
            templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        self.default_template_name = "agent_default.j2"

    def assemble_agent(
        self, sub_agent_outputs: Dict[str, Any], template_name: str = None
    ) -> str:
        """
        Combine sub-agent outputs using the specified template.
        sub_agent_outputs: dict with keys like 'tools', 'guardrails', 'core_logic', etc.
        template_name: which template to use (defaults to agent_default.j2)
        Returns the assembled agent code as a string.
        """
        if template_name is None:
            template_name = self.default_template_name
        template: Template = self.env.get_template(template_name)
        return template.render(**sub_agent_outputs)


def validate_agent_code(code: str) -> Tuple[bool, str]:
    """
    Validate that the assembled code is valid Python and contains an Agent subclass with a run method.
    Returns (True, "") if valid, else (False, error_message).
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error: {e}"

    # Look for a class that subclasses Agent and has a 'run' method
    agent_class_found = False
    run_method_found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if (isinstance(base, ast.Name) and base.id == "Agent") or (
                    isinstance(base, ast.Attribute) and base.attr == "Agent"
                ):
                    agent_class_found = True
                    # Check for run method
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name == "run":
                            run_method_found = True
    if not agent_class_found:
        return False, "No class subclassing 'Agent' found."
    if not run_method_found:
        return False, "No 'run' method found in Agent subclass."
    return True, ""
