from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, Template
import os

class TemplateEngine:
    """
    Combines sub-agent outputs into a final agent implementation using Jinja2 templates.
    """
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        self.default_template_name = "agent_default.j2"

    def assemble_agent(self, sub_agent_outputs: Dict[str, Any], template_name: str = None) -> str:
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
