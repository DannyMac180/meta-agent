"""
Stub types for hosted tools (WebSearchTool, FileSearchTool) for type-checking and fallback import resolution.
"""
from typing import Any

class WebSearchTool:
    """Typed fallback when the real hosted tool is missing."""
    def __call__(self, query: str, *args: Any, **kwargs: Any) -> str:
        return "Hosted tool unavailable in this environment."

class FileSearchTool:
    """Typed fallback when the real hosted tool is missing."""
    def __call__(self, query: str, *args: Any, **kwargs: Any) -> str:
        return "Hosted tool unavailable in this environment."

# --------------------------------------------------------------------------- #
# Make these names visible to static analysers so that
#     from meta_agent.services.tool_stubs import WebSearchTool
# resolves without a "unknown import symbol" error.
# --------------------------------------------------------------------------- #

__all__: list[str] = ["WebSearchTool", "FileSearchTool"]