"""Data model for tools produced by the ToolDesignerAgent."""

from typing import Any, Dict, Optional


from pydantic import BaseModel


class GeneratedTool(BaseModel):
    """Model representing a dynamically generated tool (code, docs, tests)."""

    # Descriptive metadata
    name: str
    description: Optional[str] = None
    specification: Optional[Dict[str, Any]] = None
    code: str  # Python source
    tests: Optional[str] = None  # pytest source
    docs: Optional[str] = None   # markdown docs
