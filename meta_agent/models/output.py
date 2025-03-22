"""
Output-related data models for the meta-agent package.

This module contains the OutputTypeDefinition model that defines the structure
of an output type for an agent.
"""

from typing import Any, List, Dict
from pydantic import BaseModel, Field


class OutputTypeDefinition(BaseModel):
    """Definition of a structured output type."""
    name: str = Field(description="Name of the output type")
    fields: List[Dict[str, Any]] = Field(description="Fields in the output type")
    code: str = Field(description="Python code defining the output type")
