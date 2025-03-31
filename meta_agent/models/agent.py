"""
Models for agent specifications.

This module contains the Pydantic models used to represent agent specifications
and their components.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Parameter for a tool."""
    name: str = Field(description="Name of the parameter")
    type: str = Field(description="Type of the parameter (string, integer, boolean, etc.)")
    description: str = Field(description="Description of the parameter")
    required: bool = Field(default=True, description="Whether the parameter is required")


class ToolDefinition(BaseModel):
    """Definition of a tool for an agent."""
    name: str = Field(description="Name of the tool")
    description: str = Field(description="Description of what the tool does")
    parameters: List[ToolParameter] = Field(default_factory=list, description="Parameters for the tool")
    return_type: str = Field(description="Return type of the tool")


class GuardrailDefinition(BaseModel):
    """Definition of a guardrail for an agent."""
    description: str = Field(description="Description of the guardrail")
    implementation: str = Field(description="Implementation details for the guardrail")


class AgentSpecification(BaseModel):
    """Input specification for an agent to be created."""
    name: str = Field(description="Name of the agent")
    description: str = Field(description="Brief description of the agent's purpose")
    instructions: str = Field(description="Detailed instructions for the agent")
    tools: List[ToolDefinition] = Field(default_factory=list, description="List of tools the agent needs")
    output_type: Optional[str] = Field(default=None, description="Output type for the agent")
    guardrails: List[GuardrailDefinition] = Field(default_factory=list, description="List of guardrails to implement")

    @classmethod
    def from_json(cls, json_data: Dict[str, Any]) -> "AgentSpecification":
        """Create an AgentSpecification from a JSON dictionary."""
        # Basic validation and extraction
        if not isinstance(json_data, dict):
            raise ValueError("Agent specification must be a JSON object")
        
        # Extract required fields
        name = json_data.get("name", "DefaultAgent")
        description = json_data.get("description", "")
        instructions = json_data.get("instructions", "")
        
        # Extract tools
        tools_data = json_data.get("tools", [])
        tools = []
        for tool_data in tools_data:
            if isinstance(tool_data, dict):
                # Extract tool parameters
                params_data = tool_data.get("parameters", [])
                parameters = []
                for param in params_data:
                    if isinstance(param, dict):
                        parameters.append(ToolParameter(
                            name=param.get("name", ""),
                            type=param.get("type", "string"),
                            description=param.get("description", ""),
                            required=param.get("required", True)
                        ))
                
                tools.append(ToolDefinition(
                    name=tool_data.get("name", ""),
                    description=tool_data.get("description", ""),
                    parameters=parameters,
                    return_type=tool_data.get("return_type", "string")
                ))
        
        # Extract output type
        output_type = json_data.get("output_type")
        
        # Extract guardrails
        guardrails_data = json_data.get("guardrails", [])
        guardrails = []
        for guardrail_data in guardrails_data:
            if isinstance(guardrail_data, dict):
                guardrails.append(GuardrailDefinition(
                    description=guardrail_data.get("description", ""),
                    implementation=guardrail_data.get("implementation", "")
                ))
        
        return cls(
            name=name,
            description=description,
            instructions=instructions,
            tools=tools,
            output_type=output_type,
            guardrails=guardrails
        )


class AgentImplementation(BaseModel):
    """Complete agent implementation with all files."""
    main_file: str = Field(description="Content of the main Python file")
    additional_files: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional files needed (filename: content)"
    )
    installation_instructions: str = Field(
        default="pip install openai-agents==0.0.7",
        description="Instructions for installing dependencies"
    )
    usage_examples: str = Field(
        default="",
        description="Examples of how to use the agent"
    )
