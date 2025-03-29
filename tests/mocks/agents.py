"""
Mock implementation of the OpenAI Agents SDK for testing.
"""

import json  # Ensure json is imported
# Import models used in expected outputs
from meta_agent.models import AgentSpecification, ToolDefinition, OutputTypeDefinition, AgentImplementation
# DEPRECATED: from tests.mocks.decorators import function_tool
# We will now mock the actual 'agents' package using unittest.mock

class Agent:
    """Mock Agent class for testing."""
    
    def __init__(self, name=None, instructions=None, tools=None):
        self.name = name
        self.instructions = instructions
        self.tools = tools or []
    
    def tool(self, func=None):
        """Mock tool decorator."""
        def decorator(f):
            self.tools.append(f)
            return f
        
        if func is None:
            return decorator
        return decorator(func)


# Mock RunResult class
class RunResult:
    """Mock RunResult class for testing."""
    def __init__(self, final_output=None, tool_outputs=None):
        # Keep both final_output and tool_outputs
        self.final_output = final_output
        self.tool_outputs = tool_outputs if tool_outputs is not None else [final_output]  # Use final_output as default tool output


# This mock Runner class is NO LONGER USED.
# We will use unittest.mock.patch to mock agents.Runner.run directly in tests.
class Runner:  # KEEP THE CLASS DEFINITION FOR OLD IMPORTS, BUT IT WON'T BE USED
    """DEPRECATED Mock Runner class for testing."""

    def __init__(self):
        pass

    @staticmethod
    async def run(agent, specification_or_prompt):
        """Mock run method that returns different results based on the prompt."""
        # This will be mocked using unittest.mock.patch in tests
        raise NotImplementedError("MockRunner.run should be patched in tests, not called directly")
