"""
Code-related data models for the meta-agent package.

This module contains the AgentCode model that defines the structure of
generated agent code and related files.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class AgentCode(BaseModel):
    """Generated agent code and related files."""
    main_code: str = Field(description="Main Python code implementing the agent")
    imports: List[str] = Field(description="Required imports")
    tool_implementations: List[str] = Field(description="Code for tool implementations")
    output_type_implementation: Optional[str] = None
    guardrail_implementations: List[str] = Field(description="Code for guardrail implementations")
    agent_creation: str = Field(description="Code that creates the agent instance")
    runner_code: str = Field(description="Code that runs the agent")
    
    model_config = {
        "json_schema_extra": lambda schema: schema.pop("required", None)
    }
    
    def __init__(self, **data):
        if 'tool_implementations' not in data:
            data['tool_implementations'] = []
        if 'guardrail_implementations' not in data:
            data['guardrail_implementations'] = []
        super().__init__(**data)
