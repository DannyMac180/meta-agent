"""
Meta Agent - A meta agent that creates OpenAI Agents SDK agents

This package implements a meta agent that can design and generate other agents
using the OpenAI Agents SDK based on natural language specifications.
"""

__version__ = "0.1.0"

from meta_agent.agent_generator import generate_agent

__all__ = ["generate_agent"]
