"""
Tool-related data models for the meta-agent package.

This module contains the ToolDefinition model that defines the structure
of a tool for an agent.
"""

from typing import Any, List, Dict
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    """Definition of a tool for an agent."""
    name: str = Field(description="Name of the tool")
    description: str = Field(description="Description of what the tool does")
    parameters: List[Dict[str, Any]] = Field(description="Parameters for the tool")
    return_type: str = Field(description="Return type of the tool")
    implementation: str = Field(description="Python code implementation of the tool")
