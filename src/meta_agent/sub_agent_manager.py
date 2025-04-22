"""
Defines the SubAgentManager class responsible for creating and managing specialized sub-agents.
"""

import logging
from typing import Dict, Any, Optional, Type
from agents import Agent, Tool

logger = logging.getLogger(__name__)

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


# --- SubAgentManager --- #

class SubAgentManager:
    """Manages the lifecycle and delegation to specialized sub-agents."""

    AGENT_TOOL_MAP: Dict[str, Type[Agent]] = {
        "coder_tool": CoderAgent,
        "tester_tool": TesterAgent,
        "reviewer_tool": ReviewerAgent,
        # Add other tool-to-agent mappings here
    }

    def __init__(self):
        """Initializes the SubAgentManager."""
        self._agents: Dict[str, Agent] = {}  # Cache for agent instances (by type/config)
        logger.info("SubAgentManager initialized.")

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
            if agent_type_name in self._agents:
                 logger.debug(f"Reusing existing {agent_type_name} for task {task_id}")
                 return self._agents[agent_type_name]
            else:
                logger.info(f"Creating new {agent_type_name} for task {task_id} based on tool '{selected_tool}'")
                try:
                    # Instantiate the agent
                    new_agent = agent_class()
                    self._agents[agent_type_name] = new_agent # Cache it
                    return new_agent
                except Exception as e:
                    logger.error(f"Failed to create agent {agent_type_name}: {e}", exc_info=True)
                    return None # Or raise?
        else:
            logger.warning(f"No specific agent class found for tools {tools} for task {task_id}. Falling back to BaseAgent.")
            # Fallback to a generic agent if no specific tool/agent mapping found
            if BaseAgent.__name__ not in self._agents:
                 self._agents[BaseAgent.__name__] = BaseAgent()
            return self._agents[BaseAgent.__name__]

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Retrieves an agent by its ID."""
        return self._agents.get(agent_id)

    def list_agents(self) -> Dict[str, Agent]:
        """Lists all managed agents."""
        return self._agents
