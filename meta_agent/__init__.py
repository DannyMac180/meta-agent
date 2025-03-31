"""
Meta Agent - A tool for generating agents using the OpenAI Agents SDK.

This package provides functionality to generate agent implementations
based on natural language specifications.
"""

from meta_agent.core import generate_agent, generate_agent_sync

__version__ = "0.1.0"

__all__ = ["generate_agent", "generate_agent_sync"]