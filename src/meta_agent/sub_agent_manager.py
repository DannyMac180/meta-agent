"""
Defines the SubAgentManager class responsible for creating and managing specialized sub-agents.
"""

import logging
from typing import Dict, Any, Optional, Type
from agents import Agent, Tool, Runner
from meta_agent.models.generated_tool import GeneratedTool
import ast
import subprocess
import tempfile
import os

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

# --- Tool Designer Sub-Agent --- #

class ToolDesignerAgent(Agent):
    """Agent specialized for generating tool code using the o4-mini-high model."""
    def __init__(self):
        super().__init__(name="ToolDesignerAgent", tools=[])

    async def run(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"ToolDesignerAgent running with spec: {specification.get('description')}")
        try:
            generated = await self.generate_tool(specification)
            # Validate Python syntax
            try:
                ast.parse(generated.code)
            except SyntaxError as e:
                return {'status': 'failed', 'error': f'Syntax error: {e}', 'code': generated.code}
            # Validate with mypy
            with tempfile.NamedTemporaryFile('w', delete=False, suffix='.py') as f:
                f.write(generated.code)
                code_path = f.name
            try:
                mypy_result = subprocess.run(['mypy', code_path], capture_output=True, text=True)
                if mypy_result.returncode != 0:
                    return {'status': 'failed', 'error': mypy_result.stdout, 'code': generated.code}
            finally:
                os.unlink(code_path)
            # Success
            return {'status': 'success', 'tool': generated.model_dump()}
        except Exception as e:
            logger.error(f"ToolDesignerAgent generation failed: {e}", exc_info=True)
            return {'status': 'failed', 'error': str(e)}

    async def generate_tool(self, specification: Dict[str, Any]) -> GeneratedTool:
        # Hosted tool decision logic
        desc = specification.get('description', '') or specification.get('task_description', '')
        desc_lc = desc.lower()
        # Hosted tool: WebSearchTool
        if any(kw in desc_lc for kw in ['search', 'retrieve', 'web browser', 'lookup', 'google', 'docs', 'documentation']):
            code = (
                'from agents.tools import WebSearchTool\n'
                'from agents import function_tool\n\n'
                '@function_tool\n'
                'def search_web(query: str) -> str:\n'
                '    """Search the web for the given query and return a summary."""\n'
                '    return WebSearchTool()(query)\n'
            )
            tests = (
                'import pytest\n\n'
                'def test_search_web():\n'
                '    result = search_web("openai agents sdk")\n'
                '    assert isinstance(result, str)\n'
            )
            docs = (
                '# search_web\n\n'
                'Searches the web for a query using the hosted WebSearchTool.\n'
                'Returns a summary string.\n'
            )
            return GeneratedTool(code=code, tests=tests, docs=docs)
        # Hosted tool: FileSearchTool (stub)
        if any(kw in desc_lc for kw in ['file', 'vector', 'embedding', 'document search', 'semantic search']):
            code = (
                'from agents.tools import FileSearchTool\n'
                'from agents import function_tool\n\n'
                '@function_tool\n'
                'def search_files(query: str) -> str:\n'
                '    """Search indexed files or vectors for the given query and return a summary."""\n'
                '    return FileSearchTool()(query)\n'
            )
            tests = (
                'import pytest\n\n'
                'def test_search_files():\n'
                '    result = search_files("project requirements")\n'
                '    assert isinstance(result, str)\n'
            )
            docs = (
                '# search_files\n\n'
                'Searches indexed files/vectors for a query using the hosted FileSearchTool.\n'
                'Returns a summary string.\n'
            )
            return GeneratedTool(code=code, tests=tests, docs=docs)
        # Otherwise: custom tool (use LLM)
        spec = specification.copy()
        spec['model'] = 'o4-mini-high'
        spec['temperature'] = 0.0
        spec['max_tokens'] = 4096
        result = await Runner.run(self, spec)
        code = result.get('code', '')
        tests = result.get('tests', '')
        docs = result.get('docs', '')
        return GeneratedTool(code=code, tests=tests, docs=docs)


# --- SubAgentManager --- #

class SubAgentManager:
    """Manages the lifecycle and delegation to specialized sub-agents."""

    AGENT_TOOL_MAP: Dict[str, Type[Agent]] = {
        "coder_tool": CoderAgent,
        "tester_tool": TesterAgent,
        "reviewer_tool": ReviewerAgent,
        "tool_designer_tool": ToolDesignerAgent,
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
