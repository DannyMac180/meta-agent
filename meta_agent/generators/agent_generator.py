"""
Agent generator module.

This module contains functions for generating agent code based on agent specifications.
"""

from typing import Optional
from meta_agent.models import AgentSpecification, AgentImplementation
from meta_agent.generators.tool_generator import generate_tools_code


def generate_agent_code(spec: AgentSpecification) -> str:
    """
    Generate Python code for an agent based on its specification.
    
    Args:
        spec: The agent specification
        
    Returns:
        Python code implementing the agent using the openai-agents SDK
    """
    # Generate imports
    imports = [
        "import asyncio",
        "from typing import Dict, List, Any, Optional",
        "from agents import Agent, Runner, function_tool",
        ""
    ]
    
    # Generate agent initialization
    agent_code = [
        f"def create_agent():",
        f'    """',
        f'    Create a {spec.name} agent based on the specification.',
        f'    ',
        f'    Returns:',
        f'        An initialized Agent instance',
        f'    """',
        f'    # Agent configuration',
        f'    agent = Agent(',
        f'        name="{spec.name}",',
        f'        description="{spec.description}",',
        f'        instructions="""{spec.instructions}""",',
    ]
    
    # Add tools if present
    if spec.tools:
        agent_code.append(f'        tools=[')
        for tool in spec.tools:
            agent_code.append(f'            {tool.name},')
        agent_code.append(f'        ],')
    
    # Add output type if specified
    if spec.output_type:
        agent_code.append(f'        output_type={spec.output_type},')
    
    # Close agent initialization
    agent_code.append(f'    )')
    agent_code.append(f'    return agent')
    
    # Generate main function
    main_code = [
        "",
        "async def main():",
        "    # Create the agent",
        "    agent = create_agent()",
        "",
        "    # Example usage",
        '    result = await Runner.run(agent, "Hello, I need your assistance.")',
        "    print(result.final_output)",
        "",
        'if __name__ == "__main__":',
        "    asyncio.run(main())"
    ]
    
    # Combine all code sections
    return "\n".join(imports + agent_code + main_code)


def generate_agent_implementation(spec: AgentSpecification) -> AgentImplementation:
    """
    Generate a complete agent implementation based on its specification.
    
    Args:
        spec: The agent specification
        
    Returns:
        A complete agent implementation with all necessary files
    """
    # Generate tools code if tools are specified
    additional_files = {}
    if spec.tools:
        tools_code = generate_tools_code(spec.tools)
        additional_files["tools.py"] = tools_code
    
    # Generate main agent code
    main_file = generate_agent_code(spec)
    
    # Generate usage examples
    usage_examples = f"""
# Basic usage
import asyncio
from agent_implementation import create_agent
from agents import Runner

async def run_agent():
    agent = create_agent()
    result = await Runner.run(agent, "Your query here")
    print(result.final_output)

asyncio.run(run_agent())
"""
    
    # Create the implementation
    return AgentImplementation(
        main_file=main_file,
        additional_files=additional_files,
        installation_instructions="pip install openai-agents==0.0.7",
        usage_examples=usage_examples
    )
