"""
Agent-related data models for the meta-agent package.

This module contains the AgentSpecification model that defines the structure
of an agent to be created.
"""

from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field


class AgentSpecification(BaseModel):
    """Input specification for an agent to be created."""
    name: str = Field(description="Name of the agent")
    description: str = Field(description="Brief description of the agent's purpose", default="")
    instructions: str = Field(description="Detailed instructions for the agent", default="")
    tools: List[Dict[str, Any]] = Field(description="List of tools the agent needs", default_factory=list)
    output_type: Optional[str] = None
    guardrails: List[Dict[str, Any]] = Field(description="List of guardrails to implement", default_factory=list)
    handoffs: List[Dict[str, Any]] = Field(description="List of handoffs to other agents", default_factory=list)
    
    model_config = {
        "json_schema_extra": lambda schema: schema.pop("required", None)
    }
    
    def __init__(self, **data):
        if 'name' not in data:
            data['name'] = "DefaultAgent"
        if 'description' not in data:
            data['description'] = ""
        if 'instructions' not in data:
            data['instructions'] = ""
        if 'tools' not in data:
            data['tools'] = []
        if 'guardrails' not in data:
            data['guardrails'] = []
        if 'handoffs' not in data:
            data['handoffs'] = []
        super().__init__(**data)
