"""
Core functionality for the meta-agent package.

This module implements the main generate_agent function that orchestrates
the agent generation process.
"""

import asyncio
from typing import Dict, Any

from agents import Agent, Runner

from meta_agent.models import (
    AgentSpecification,
    AgentDesign,
    AgentCode,
    AgentImplementation
)
from meta_agent.design import (
    analyze_agent_specification,
    design_agent_tools,
    design_output_type,
    design_guardrails
)
from meta_agent.generation import (
    generate_tool_code,
    generate_output_type_code,
    generate_guardrail_code,
    generate_agent_creation_code,
    generate_runner_code,
    assemble_agent_implementation
)
from meta_agent.validation import validate_agent_implementation
from meta_agent.utils import load_config, check_api_key, print_api_key_warning


async def generate_agent(specification: str) -> AgentImplementation:
    """
    Generate an agent based on a natural language specification.
    
    Args:
        specification: Natural language description of the agent to create
        
    Returns:
        Complete agent implementation
    """
    # Load configuration
    load_config()
    
    # Check for API key
    if not check_api_key():
        print_api_key_warning()
    
    # Create the meta agent
    meta_agent = Agent(
        name="MetaAgent",
        instructions="""
        You are a meta agent that creates other agents using the OpenAI Agents SDK.
        Your task is to analyze a natural language specification and generate a complete
        agent implementation based on it.
        """,
        tools=[
            analyze_agent_specification,
            design_agent_tools,
            design_output_type,
            design_guardrails,
            generate_tool_code,
            generate_output_type_code,
            generate_guardrail_code,
            generate_agent_creation_code,
            generate_runner_code,
            assemble_agent_implementation,
            validate_agent_implementation,
        ]
    )
    
    # Initialize the runner
    runner = Runner()
    
    # Step 1: Analyze the specification
    print("Step 1: Analyzing agent specification...")
    agent_spec_result = await Runner.run(
        meta_agent,
        f"Analyze this agent specification and extract structured information: {specification}"
    )
    agent_spec_dict = agent_spec_result if isinstance(agent_spec_result, dict) else {}
    agent_specification = AgentSpecification(**agent_spec_dict)
    
    # Step 2: Design the tools
    print("Step 2: Designing agent tools...")
    tools_result = await Runner.run(
        meta_agent,
        f"Design tools for this agent: {agent_specification.model_dump_json()}"
    )
    tools = tools_result if isinstance(tools_result, list) else []
    
    # Step 3: Design the output type (if needed)
    print("Step 3: Designing output type (if needed)...")
    output_type_result = await Runner.run(
        meta_agent,
        f"Design an output type for this agent if needed: {agent_specification.model_dump_json()}"
    )
    output_type = output_type_result if output_type_result else None
    
    # Step 4: Design the guardrails
    print("Step 4: Designing guardrails...")
    guardrails_result = await Runner.run(
        meta_agent,
        f"Design guardrails for this agent: {agent_specification.model_dump_json()}"
    )
    guardrails = guardrails_result if isinstance(guardrails_result, list) else []
    
    # Create the agent design
    agent_design = AgentDesign(
        specification=agent_specification,
        tools=tools,
        output_type=output_type,
        guardrails=guardrails
    )
    
    # Step 5: Generate tool code
    print("Step 5: Generating tool code...")
    tool_code_list = []
    for tool in agent_design.tools:
        tool_code = await Runner.run(
            meta_agent,
            f"Generate code for this tool: {tool.model_dump_json()}"
        )
        if tool_code:
            tool_code_list.append(tool_code)
    
    # Step 6: Generate output type code (if needed)
    print("Step 6: Generating output type code (if needed)...")
    output_type_code = None
    if agent_design.output_type:
        output_type_code = await Runner.run(
            meta_agent,
            f"Generate code for this output type: {agent_design.output_type.model_dump_json()}"
        )
    
    # Step 7: Generate guardrail code
    print("Step 7: Generating guardrail code...")
    guardrail_code_list = []
    for guardrail in agent_design.guardrails:
        guardrail_code = await Runner.run(
            meta_agent,
            f"Generate code for this guardrail: {guardrail.model_dump_json()}"
        )
        if guardrail_code:
            guardrail_code_list.append(guardrail_code)
    
    # Step 8: Generate agent creation code
    print("Step 8: Generating agent creation code...")
    agent_creation_code = await Runner.run(
        meta_agent,
        f"Generate code that creates an agent instance based on this design: {agent_design.model_dump_json()}"
    )
    
    # Step 9: Generate runner code
    print("Step 9: Generating runner code...")
    runner_code = await Runner.run(
        meta_agent,
        f"Generate code that runs the agent: {agent_design.model_dump_json()}"
    )
    
    # Create the agent code
    agent_code = AgentCode(
        main_code="",  # Will be assembled later
        imports=[
            "import os",
            "import asyncio",
            "from dotenv import load_dotenv",
            "from agents import Agent, Runner, function_tool, output_guardrail, GuardrailFunctionOutput",
            "from typing import Dict, List, Any, Optional",
            "from pydantic import BaseModel, Field"
        ],
        tool_implementations=tool_code_list,
        output_type_implementation=output_type_code,
        guardrail_implementations=guardrail_code_list,
        agent_creation=agent_creation_code,
        runner_code=runner_code
    )
    
    # Step 10: Assemble the implementation
    print("Step 10: Assembling agent implementation...")
    implementation_result = await Runner.run(
        meta_agent,
        f"Assemble the complete agent implementation: {agent_code.model_dump_json()}"
    )
    implementation_dict = implementation_result if isinstance(implementation_result, dict) else {}
    agent_implementation = AgentImplementation(**implementation_dict)
    
    # Step 11: Validate the implementation
    print("Step 11: Validating agent implementation...")
    validation_result = await Runner.run(
        meta_agent,
        f"Validate this agent implementation: {agent_implementation.model_dump_json()}"
    )
    
    # Print validation results
    if isinstance(validation_result, dict) and validation_result.get("valid", False):
        print("Validation successful!")
    else:
        print("Validation failed:")
        print(validation_result)
    
    return agent_implementation
