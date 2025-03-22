"""
Meta Agent - A package for generating OpenAI Agents SDK agents.

This package provides tools for creating agents based on natural language specifications
using the OpenAI Agents SDK.
"""

from meta_agent.core import generate_agent
from meta_agent.models import (
    AgentSpecification,
    ToolDefinition,
    OutputTypeDefinition,
    GuardrailDefinition,
    AgentDesign,
    AgentCode,
    AgentImplementation
)

__version__ = "0.1.0"

__all__ = [
    'generate_agent',
    'AgentSpecification',
    'ToolDefinition',
    'OutputTypeDefinition',
    'GuardrailDefinition',
    'AgentDesign',
    'AgentCode',
    'AgentImplementation',
]
