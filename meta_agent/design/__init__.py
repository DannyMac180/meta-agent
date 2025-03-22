"""
Design package for the meta-agent.

This package contains functions for designing various aspects of an agent.
"""

from meta_agent.design.analyzer import analyze_agent_specification
from meta_agent.design.tool_designer import design_agent_tools
from meta_agent.design.output_designer import design_output_type
from meta_agent.design.guardrail_designer import design_guardrails

__all__ = [
    'analyze_agent_specification',
    'design_agent_tools',
    'design_output_type',
    'design_guardrails',
]