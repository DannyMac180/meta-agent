import os
from typing import Any, Callable, Dict, List


class Template:
    def __init__(
        self, text: str, name: str = "", globals: Dict[str, Any] | None = None
    ) -> None:
        self.text = text
        self.name = name
        self.globals = globals or {}

    def render(self, *_, **kwargs: Any) -> str:
        if self.name.endswith("tool_template.py.j2"):
            map_type = kwargs.get("map_type") or self.globals.get("map_type")
            return _render_tool_template(kwargs.get("spec"), map_type)
        if self.name.endswith("agent_default.j2"):
            return _render_agent_default(kwargs)
        return self.text


def _render_tool_template(
    spec: Dict[str, Any] | None, map_type: Callable[[str], str] | None
) -> str:
    if spec is None:
        return ""
    if not isinstance(spec, dict):
        if hasattr(spec, "model_dump"):
            spec = spec.model_dump()
        elif hasattr(spec, "dict"):
            spec = spec.dict()
        else:
            spec = vars(spec)
    if map_type is None:

        def map_type(t: str) -> str:
            return t

    lines: List[str] = []
    lines.append("import logging")
    lines.append("from typing import Any")
    lines.append("")
    lines.append("logger = logging.getLogger(__name__)")
    lines.append("")
    lines.append(f"# {spec.get('purpose', '')}")
    lines.append(f"def {spec.get('name')}(")
    params = spec.get("input_parameters") or []
    for i, p in enumerate(params):
        line = f"    {p['name']}: {map_type(p['type_'])}"
        if not p.get("required", True):
            line += " = None"
        if i < len(params) - 1:
            line += ","
        lines.append(line)
    lines.append(f") -> {map_type(spec.get('output_format'))}:")
    lines.append(f"    \"\"\"{spec.get('purpose')}\"")
    lines.append("")
    lines.append("    Args:")
    for p in params:
        desc = p.get("description") or "No description provided."
        req = "(Required)" if p.get("required", True) else "(Optional)"
        lines.append(f"        {p['name']}: {desc} {req}")
    lines.append("")
    lines.append("    Returns:")
    lines.append(
        f"        {map_type(spec.get('output_format'))}: {spec.get('output_format')}"
    )
    lines.append('    """')
    lines.append(f"    logger.info(f'Running tool: {spec.get('name')}')")
    lines.append("    result = None")
    lines.append("    logger.warning('Tool logic not yet implemented!')")
    lines.append("    return result")
    return "\n".join(lines)


def _render_agent_default(ctx: Dict[str, Any]) -> str:
    tools = ctx.get("tools") or []
    guardrails = ctx.get("guardrails") or []
    lines: List[str] = []
    lines.append('"""')
    lines.append("Auto-generated agent implementation")
    lines.append('"""')
    lines.append("from agents import Agent")
    lines.append("")
    cls = ctx.get("agent_class_name", "AgentImpl")
    lines.append(f"class {cls}(Agent):")
    lines.append("    def __init__(self):")
    lines.append("        super().__init__(")
    lines.append(f"            name=\"{ctx.get('name')}\",")
    lines.append(f"            instructions=\"\"\"{ctx.get('instructions')}\"\"\",")
    lines.append("        )")
    lines.append("")
    lines.append("    def run(self, input):")
    core_logic = ctx.get("core_logic", "")
    for line in str(core_logic).splitlines():
        lines.append(f"        {line}")
    lines.append("")
    lines.append("    # Tools")
    for tool in tools:
        for tl in str(tool).splitlines():
            lines.append(f"    {tl}")
    lines.append("")
    lines.append("    # Guardrails")
    for g in guardrails:
        for gl in str(g).splitlines():
            lines.append(f"    {gl}")
    return "\n".join(lines)


class FileSystemLoader:
    def __init__(self, searchpath: str) -> None:
        self.searchpath = searchpath

    def get_source(self, _environment: Any, template: str) -> str:
        path = os.path.join(self.searchpath, template)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()


def select_autoescape(*_args: Any, **_kwargs: Any) -> bool:
    return False


class Environment:
    def __init__(
        self, loader: FileSystemLoader, autoescape: Any = None, **_kwargs: Any
    ) -> None:
        self.loader = loader
        self.globals: Dict[str, Any] = {}

    def get_template(self, name: str) -> Template:
        text = self.loader.get_source(self, name)
        return Template(text, name, globals=self.globals)
