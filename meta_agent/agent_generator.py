"""
Agent Generator - A meta agent that creates OpenAI Agents SDK agents

This module is maintained for backward compatibility.
All functionality has been moved to meta_agent.core and other submodules.
"""

import warnings
from meta_agent.core import generate_agent

# Show deprecation warning
warnings.warn(
    "The meta_agent.agent_generator module is deprecated. "
    "Please use meta_agent.core instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export the generate_agent function for backward compatibility
__all__ = ["generate_agent"]
