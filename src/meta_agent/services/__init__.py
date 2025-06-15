"""
Package initialiser for ``meta_agent.services``.

It simply re‑exports the local stub tool classes so library code can write
``from meta_agent.services import WebSearchTool`` or
``from meta_agent.services.tool_stubs import WebSearchTool`` interchangeably
without upsetting static type checkers.
"""

from .tool_stubs import WebSearchTool, FileSearchTool

__all__: list[str] = ["WebSearchTool", "FileSearchTool"]