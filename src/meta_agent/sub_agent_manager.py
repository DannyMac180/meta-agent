"""
Defines the SubAgentManager class responsible for creating and managing specialized sub-agents.
"""

import logging
from typing import Dict, Any, Optional, Type
import logging
try:
    from agents import Agent, Tool, Runner, WebSearchTool, FileSearchTool
except (ImportError, AttributeError):
    logging.warning("Hosted tools unavailable: patching stubs into 'agents' package.")

    import sys, types, agents as _agents_pkg  # type: ignore

    class _StubHostedTool:  # pylint: disable=too-few-public-methods
        """Minimal stand‑in when WebSearchTool / FileSearchTool aren't shipped.

        `Tool()` → returns instance; instance is **callable** so that
        `WebSearchTool()(query)` works without raising TypeError.
        """

        def __call__(self, *_, **__):  # noqa: D401,E501
            return "Hosted tool unavailable in this environment."

    # expose the stubs both locally *and* inside the real `agents` module
    WebSearchTool = _StubHostedTool()  # type: ignore
    FileSearchTool = _StubHostedTool()  # type: ignore
    _agents_pkg.WebSearchTool = WebSearchTool  # type: ignore
    _agents_pkg.FileSearchTool = FileSearchTool  # type: ignore
    from agents import Agent, Tool, Runner

from meta_agent.models.generated_tool import GeneratedTool
from meta_agent.template_engine import TemplateEngine
import ast
import subprocess
import tempfile
import os
import json
import re

logger = logging.getLogger(__name__)

# --- Imports for Agent Logic ---
from agents import Agent, Tool, Runner, RunConfig
from agents.run import RunResult
from agents import function_tool # Added for decorator

# --- Logging Setup ---
import logging

# --- Placeholder Sub-Agent Classes --- #

class BaseAgent(Agent):
    """A generic base agent for tasks without specific tools."""
    def __init__(self):
        super().__init__(name="BaseAgent", tools=[])

    async def run(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"BaseAgent running with spec: {specification.get('description')}")
        # Simulate work
        return {"status": "simulated_success", "output": f"Result from BaseAgent for {specification.get('task_id')}"}

class CoderAgent(Agent):
    """Agent specialized for coding tasks."""
    def __init__(self):
        super().__init__(name="CoderAgent", tools=[])

    async def run(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"CoderAgent running with spec: {specification.get('description')}")
        # Simulate coding work
        return {"status": "simulated_success", "output": f"Generated code by CoderAgent for {specification.get('task_id')}"}

class TesterAgent(Agent):
    """Agent specialized for testing tasks."""
    def __init__(self):
        super().__init__(name="TesterAgent", tools=[])

    async def run(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"TesterAgent running with spec: {specification.get('description')}")
        # Simulate testing work
        return {"status": "simulated_success", "output": f"Test results from TesterAgent for {specification.get('task_id')}"}

class ReviewerAgent(Agent):
    """Agent specialized for review tasks."""
    def __init__(self):
        super().__init__(name="ReviewerAgent", tools=[])

    async def run(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"ReviewerAgent running with spec: {specification.get('description')}")
        # Simulate review work
        return {"status": "simulated_success", "output": f"Review comments from ReviewerAgent for {specification.get('task_id')}"}

# --- Import the actual ToolDesignerAgent --- #
# TODO: Ideally, CoderAgent, TesterAgent, ReviewerAgent should also be imported
# from their own files in the agents directory if they exist.
from meta_agent.agents.tool_designer_agent import ToolDesignerAgent

# --- SubAgentManager --- #

class SubAgentManager:
    """Manages the lifecycle and delegation to specialized sub-agents."""

    AGENT_TOOL_MAP: Dict[str, Type[Agent]] = {
        "coder_tool": CoderAgent, # Assumes CoderAgent is defined above or imported
        "tester_tool": TesterAgent, # Assumes TesterAgent is defined above or imported
        "reviewer_tool": ReviewerAgent, # Assumes ReviewerAgent is defined above or imported
        "tool_designer_tool": ToolDesignerAgent, # Use the imported ToolDesignerAgent
        # Add other tool-to-agent mappings here
    }

    def __init__(self):
        """Initializes the SubAgentManager."""
        self.active_agents: Dict[str, Agent] = {}
        logger.info("SubAgentManager initialized.")

    def get_agent(self, tool_requirement: str, **kwargs) -> Optional[Agent]:
        """Get or create an agent instance based on the tool requirement.

        Args:
            tool_requirement: The name of the tool the agent should provide.
            **kwargs: Additional keyword arguments to pass to the agent's constructor.

        Returns:
            An instance of the required agent, or None if not found.
        """
        agent_cls = self.AGENT_TOOL_MAP.get(tool_requirement)
        if agent_cls:
            # Simple caching strategy: return existing instance if available
            # Could be expanded with more complex lifecycle management
            if tool_requirement not in self.active_agents:
                try:
                    # Pass kwargs to the agent constructor
                    self.active_agents[tool_requirement] = agent_cls(**kwargs)
                    logger.info(f"Instantiated agent {agent_cls.__name__} for tool '{tool_requirement}' with config: {kwargs}")
                except Exception as e:
                    logger.error(f"Failed to instantiate agent {agent_cls.__name__} with config {kwargs}: {e}", exc_info=True)
                    return None
            return self.active_agents[tool_requirement]
        else:
            logger.warning(f"No agent found for tool requirement: {tool_requirement}")
            return None

    def get_or_create_agent(self, task_requirements: Dict[str, Any]) -> Optional[Agent]:
        """
        Retrieves or creates a sub-agent based on task requirements.
        Uses a simple mapping from the first tool found.

        Args:
            task_requirements: A dictionary containing 'task_id', 'tools',
                               'guardrails', and 'description'.

        Returns:
            An instance of the appropriate Agent, or a BaseAgent/None if no
            specific agent type is determined.
        """
        task_id = task_requirements.get("task_id", "unknown")
        tools = task_requirements.get("tools", [])
        logger.info(f"Getting/creating agent for task {task_id} with tools: {tools}")

        agent_class: Optional[Type[Agent]] = None
        selected_tool = None

        if tools:
            # Simple approach: Use the first tool to determine agent type
            selected_tool = tools[0]
            agent_class = self.AGENT_TOOL_MAP.get(selected_tool)

        if agent_class:
            agent_type_name = agent_class.__name__
            # Basic caching: Check if an agent of this type already exists
            if agent_type_name in self.active_agents:
                logger.debug(f"Reusing existing {agent_type_name} for task {task_id}")
                agent = self.active_agents[agent_type_name]
                # Also cache by tool requirement for get_agent() to find it
                if selected_tool and selected_tool not in self.active_agents:
                    self.active_agents[selected_tool] = agent
                return agent

            logger.info(f"Creating new {agent_type_name} for task {task_id} based on tool '{selected_tool}'")
            try:
                # Instantiate the agent
                new_agent = agent_class()
                self.active_agents[agent_type_name] = new_agent # Cache by class name
                # Also cache by tool requirement for get_agent() to find it
                if selected_tool:
                    self.active_agents[selected_tool] = new_agent
                return new_agent
            except Exception as e:
                logger.error(f"Failed to create agent {agent_type_name}: {e}", exc_info=True)
                return None # Or raise?
        else:
            logger.warning(f"No specific agent class found for tools {tools} for task {task_id}. Falling back to BaseAgent.")
            # Fallback to a generic agent if no specific tool/agent mapping found
            if BaseAgent.__name__ not in self.active_agents:
                self.active_agents[BaseAgent.__name__] = BaseAgent()
            return self.active_agents[BaseAgent.__name__]

    def list_agents(self) -> Dict[str, Agent]:
        """Lists all managed agents by their class name."""
        # Filter out tool requirement keys, keeping only class name keys
        return {k: v for k, v in self.active_agents.items()
                if k in [cls.__name__ for cls in self.AGENT_TOOL_MAP.values()] or k == BaseAgent.__name__}
