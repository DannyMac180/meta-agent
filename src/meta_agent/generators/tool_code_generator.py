import ast
import logging
import re
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from meta_agent.parsers.tool_spec_parser import ToolSpecification

TYPE_MAP = {
    "string": "str",
    "integer": "int",
    "float": "float",
    "boolean": "bool",
    "list": "List",
    "dict": "Dict",
    "any": "Any",
}


def map_type(spec_type: str) -> str:
    """Recursively map specification type string to Python type hint string."""
    # Handle nested generics like Dict[str, List[int]]
    match = re.match(r"^(\w+)\[(.+)\]$", spec_type.strip())
    if match:
        base = match.group(1).lower()
        inner = match.group(2)
        # Support multiple inner types (e.g., Dict[str, int])
        inner_types = [map_type(x.strip()) for x in inner.split(",")]
        base_py = TYPE_MAP.get(base, base.capitalize())
        return f"{base_py}[{', '.join(inner_types)}]"
    return TYPE_MAP.get(spec_type.lower(), "Any")


class CodeGenerationError(Exception):
    pass


class ToolCodeGenerator:
    """Generates Python code for a tool based on its specification."""

    _env: Environment | None = None
    _template: Template | None = None

    def __init__(self, specification: ToolSpecification):
        self.specification = specification
        if not ToolCodeGenerator._env:
            template_dir = Path(__file__).parent.parent / "templates"
            ToolCodeGenerator._env = Environment(
                loader=FileSystemLoader(searchpath=str(template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            ToolCodeGenerator._env.globals["map_type"] = map_type
        if not ToolCodeGenerator._template:
            ToolCodeGenerator._template = ToolCodeGenerator._env.get_template(
                "tool_template.py.j2"
            )

    def generate(self) -> str:
        try:
            generated_code = ToolCodeGenerator._template.render(spec=self.specification)
            try:
                ast.parse(generated_code)
            except SyntaxError as se:
                logging.error(f"Syntax error in generated code: {se}")
                raise CodeGenerationError(
                    f"Syntax error in generated code: {se}\n\n{generated_code}"
                )
            return generated_code
        except Exception as e:
            logging.exception("Error during code generation")
            raise CodeGenerationError(f"Error generating code: {e}")
