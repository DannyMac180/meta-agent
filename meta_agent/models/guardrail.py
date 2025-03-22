"""
Guardrail-related data models for the meta-agent package.

This module contains the GuardrailDefinition model that defines the structure
of a guardrail for an agent.
"""

from typing import Literal
from pydantic import BaseModel, Field


class GuardrailDefinition(BaseModel):
    """Definition of a guardrail for an agent."""
    name: str = Field(description="Name of the guardrail")
    type: Literal["input", "output"] = Field(description="Type of guardrail (input or output)")
    validation_logic: str = Field(description="Logic for validating input or output")
    implementation: str = Field(description="Python code implementing the guardrail")
