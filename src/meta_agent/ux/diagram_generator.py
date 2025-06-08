"""Mermaid diagram generation utilities."""

from __future__ import annotations

from typing import Mapping, Any

from .error_handler import DiagramGenerationError


class DiagramGenerator:
    """Generate Mermaid diagrams from agent specifications."""

    def __init__(self, default_direction: str = "TB") -> None:
        self.default_direction = default_direction

    def generate(
        self,
        spec: Mapping[str, Any],
        *,
        diagram_type: str = "flowchart",
        direction: str | None = None,
        node_styles: Mapping[str, str] | None = None,
    ) -> str:
        """Return a Mermaid diagram describing the agent.

        Parameters
        ----------
        spec:
            Mapping describing the agent (e.g. :class:`SpecSchema` dict).
        diagram_type:
            Mermaid diagram type such as ``flowchart`` or ``graph``.
        direction:
            Layout direction (``TB`` top-bottom, ``LR`` left-right, etc.).
        node_styles:
            Optional mapping of node identifiers to Mermaid style strings.

        Returns
        -------
        str
            Mermaid diagram definition.
        """
        if not isinstance(spec, Mapping):
            raise DiagramGenerationError("spec must be a mapping")

        direction = direction or self.default_direction

        lines: list[str] = [f"{diagram_type} {direction}"]

        inputs = spec.get("inputs") or {}
        outputs = spec.get("outputs") or {}
        task_desc = spec.get("task_description", "Agent")

        agent_id = "AGENT"
        lines.append(f"    {agent_id}[{task_desc}]")

        for name in inputs:
            node_id = f"IN_{name}".replace(" ", "_")
            lines.append(f"    {node_id}[{name}]")
            lines.append(f"    {node_id} --> {agent_id}")

        for name in outputs:
            node_id = f"OUT_{name}".replace(" ", "_")
            lines.append(f"    {agent_id} --> {node_id}")
            lines.append(f"    {node_id}[{name}]")

        if node_styles:
            for node, style in node_styles.items():
                lines.append(f"    style {node} {style}")

        return "\n".join(lines) + "\n"
