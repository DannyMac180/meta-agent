"""
Agent implementation assembler for the meta-agent package.

This module contains functions for assembling the complete agent implementation.
"""

from typing import List, Optional, Dict, Any
from agents import function_tool
from pydantic import BaseModel, Field
from meta_agent.models.implementation import AgentImplementation
from meta_agent.utils.string_utils import snake_to_pascal
from meta_agent.decorators import function_tool

class AssemblerInput(BaseModel):
    agent_name: str = Field(description="The name of the agent being generated.")
    tool_implementations: List[str] = Field(description="List of Python code strings, each implementing a tool function with the @function_tool decorator.")
    output_type_implementation: Optional[str] = Field(description="Python code string defining the Pydantic output type class, if any.", default=None)
    agent_creation_code: str = Field(description="Python code string that creates the Agent instance.")
    runner_code: str = Field(description="Python code string for the `async def main(): ...` runner block.")

@function_tool()
def assemble_agent_implementation(
    agent_name: str,
    tool_implementations: List[str],
    output_type_implementation: Optional[str],
    agent_creation_code: str,
    runner_code: str
) -> AgentImplementation:
    """
    Assembles the generated code components into a complete, runnable Python file
    and provides standard installation/usage instructions.

    Args:
        agent_name: The name of the agent.
        tool_implementations: List of code strings for tool functions.
        output_type_implementation: Code string for the Pydantic output class, if any.
        agent_creation_code: Code string defining the Agent instance.
        runner_code: Code string for the async main runner block.

    Returns:
        Complete agent implementation including the main file content and instructions.
    """
    # Basic imports - can be refined by LLM if needed
    imports = [
        "import asyncio",
        "from agents import Agent, Runner, function_tool",
        "from pydantic import BaseModel, Field",
        "from typing import Optional, List, Dict, Any" # Add other common imports
    ]

    # Assemble the main file content
    main_file_parts = [
        "\n".join(imports),
        output_type_implementation if output_type_implementation else "",
        "\n\n".join(tool_implementations),
        agent_creation_code,
        runner_code
    ]
    main_file_content = "\n\n\n".join(filter(None, main_file_parts)).strip() + "\n"

    # Standard requirements, installation, and usage
    return AgentImplementation(
        main_file=main_file_content,
        additional_files={
            "requirements.txt": "openai-agents>=0.0.7\npydantic>=2.0\npython-dotenv>=1.0.0" # Common dependencies
        },
        installation_instructions="# Installation\n\n1. Install dependencies: `pip install -r requirements.txt`",
        usage_examples=f"# Usage\n\nRun the agent script directly:\n```bash\npython {agent_name.lower()}.py\n```\n\nOr import and run the main function:\n```python\nimport asyncio\nfrom {agent_name.lower()} import main\n\nasyncio.run(main())\n```"
    )
