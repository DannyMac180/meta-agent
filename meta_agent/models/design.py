"""
Design-related data models for the meta-agent package.

This module contains the AgentDesign model that defines the complete design
for an agent, including its specification, tools, output type, and guardrails.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from meta_agent.models.agent import AgentSpecification
from meta_agent.models.tool import ToolDefinition
from meta_agent.models.output import OutputTypeDefinition
from meta_agent.models.guardrail import GuardrailDefinition


class AgentDesign(BaseModel):
    """Complete design for an agent."""
    specification: AgentSpecification = Field(description="Basic agent specification")
    tools: List[ToolDefinition] = Field(description="Detailed tool definitions")
    output_type: Optional[OutputTypeDefinition] = None
    guardrails: List[GuardrailDefinition] = Field(description="Detailed guardrail definitions")
    
    model_config = {
        "json_schema_extra": lambda schema: schema.pop("required", None)
    }
    
    def __init__(self, **data):
        if 'tools' not in data:
            data['tools'] = []
        if 'guardrails' not in data:
            data['guardrails'] = []
        super().__init__(**data)
