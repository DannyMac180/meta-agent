"""Data model for tools produced by the ToolDesignerAgent."""

from typing import Any, Dict, Optional

from pydantic import BaseModel

class GeneratedTool(BaseModel):
    """Representation of a generated tool."""

    # Basic metadata about the tool.  These are optional so that the minimal
    # structure returned by ``ToolDesignerAgent.run`` (which only provides code
    # and placeholder docs/tests) still validates.
    name: Optional[str] = None
    description: Optional[str] = None

    # Full tool specification used when registering the tool.  Defaults to an
    # empty dict so callers can omit it in simple cases.
    specification: Dict[str, Any] = {}

    # Generated artefacts
    code: str  # Python source
    tests: Optional[str] = None  # pytest source
    docs: Optional[str] = None   # markdown docs
