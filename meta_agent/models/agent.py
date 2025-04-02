"""
Models for agent specifications.

This module contains the Pydantic models used to represent agent specifications
and their components.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


# ===================== DATA MODELS =====================

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


class OutputTypeField(BaseModel):
    """Field in an output type."""
    name: str = Field(description="Name of the field")
    type: str = Field(description="Type of the field")
    description: str = Field(description="Description of the field")
    required: bool = Field(default=True, description="Whether the field is required")


class OutputTypeDefinition(BaseModel):
    """Definition of a structured output type."""
    name: str = Field(description="Name of the output type")
    fields: List[OutputTypeField] = Field(default_factory=list, description="Fields in the output type")


class GuardrailDefinition(BaseModel):
    """Definition of a guardrail for an agent."""
    description: str = Field(description="Description of the guardrail")
    type: str = Field(default="output", description="Type of guardrail (input or output)")


class AgentSpecification(BaseModel):
    """Input specification for an agent to be created."""
    name: str = Field(description="Name of the agent")
    description: str = Field(description="Brief description of the agent's purpose")
    instructions: str = Field(description="Detailed instructions for the agent")
    tools: List[ToolDefinition] = Field(default_factory=list, description="List of tools the agent needs")
    output_type: Optional[OutputTypeDefinition] = Field(default=None, description="Output type if using structured output")
    guardrails: List[GuardrailDefinition] = Field(default_factory=list, description="List of guardrails to implement")


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
