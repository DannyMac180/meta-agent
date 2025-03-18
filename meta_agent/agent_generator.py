"""
Agent Generator - A meta agent that creates OpenAI Agents SDK agents

This module implements a meta agent that can design and generate other agents
using the OpenAI Agents SDK based on natural language specifications.
"""

import asyncio
import json
import os
from typing import Any, List, Optional, Dict, Union, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from agents import (
    Agent, 
    Runner,
    function_tool,
    output_guardrail,
    GuardrailFunctionOutput
)


# Load environment variables from .env file
load_dotenv()

# Configure OpenAI API key
# Get API key from environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY environment variable not set.")
    print("Please set your OpenAI API key in the .env file or as an environment variable:")
    print("export OPENAI_API_KEY='your-api-key'")


# ===================== DATA MODELS =====================

class AgentSpecification(BaseModel):
    """Input specification for an agent to be created."""
    name: str = Field(description="Name of the agent")
    description: str = Field(description="Brief description of the agent's purpose")
    instructions: str = Field(description="Detailed instructions for the agent")
    tools: List[Dict[str, Any]] = Field(description="List of tools the agent needs")
    output_type: Optional[str] = None
    guardrails: List[Dict[str, Any]] = Field(description="List of guardrails to implement")
    handoffs: List[Dict[str, Any]] = Field(description="List of handoffs to other agents")
    
    model_config = {
        "json_schema_extra": lambda schema: schema.pop("required", None)
    }
    
    def __init__(self, **data):
        if 'tools' not in data:
            data['tools'] = []
        if 'guardrails' not in data:
            data['guardrails'] = []
        if 'handoffs' not in data:
            data['handoffs'] = []
        super().__init__(**data)


class ToolDefinition(BaseModel):
    """Definition of a tool for an agent."""
    name: str = Field(description="Name of the tool")
    description: str = Field(description="Description of what the tool does")
    parameters: List[Dict[str, Any]] = Field(description="Parameters for the tool")
    return_type: str = Field(description="Return type of the tool")
    implementation: str = Field(description="Python code implementation of the tool")


class OutputTypeDefinition(BaseModel):
    """Definition of a structured output type."""
    name: str = Field(description="Name of the output type")
    fields: List[Dict[str, Any]] = Field(description="Fields in the output type")
    code: str = Field(description="Python code defining the output type")


class GuardrailDefinition(BaseModel):
    """Definition of a guardrail for an agent."""
    name: str = Field(description="Name of the guardrail")
    type: Literal["input", "output"] = Field(description="Type of guardrail (input or output)")
    validation_logic: str = Field(description="Logic for validating input or output")
    implementation: str = Field(description="Python code implementing the guardrail")


class AgentDesign(BaseModel):
    """Complete design for an agent."""
    specification: AgentSpecification = Field(description="Basic agent specification")
    tools: List[ToolDefinition] = Field(description="Detailed tool definitions")
    output_type: Optional[OutputTypeDefinition] = None
    guardrails: List[GuardrailDefinition] = Field(description="Detailed guardrail definitions")
    
    model_config = {
        "json_schema_extra": lambda schema: schema.pop("required", None)
    }
    
    def __init__(self, **data):
        if 'tools' not in data:
            data['tools'] = []
        if 'guardrails' not in data:
            data['guardrails'] = []
        super().__init__(**data)


class AgentCode(BaseModel):
    """Generated agent code and related files."""
    main_code: str = Field(description="Main Python code implementing the agent")
    imports: List[str] = Field(description="Required imports")
    tool_implementations: List[str] = Field(description="Code for tool implementations")
    output_type_implementation: Optional[str] = None
    guardrail_implementations: List[str] = Field(description="Code for guardrail implementations")
    agent_creation: str = Field(description="Code that creates the agent instance")
    runner_code: str = Field(description="Code that runs the agent")
    
    model_config = {
        "json_schema_extra": lambda schema: schema.pop("required", None)
    }
    
    def __init__(self, **data):
        if 'tool_implementations' not in data:
            data['tool_implementations'] = []
        if 'guardrail_implementations' not in data:
            data['guardrail_implementations'] = []
        super().__init__(**data)


class AgentImplementation(BaseModel):
    """Complete agent implementation with all files."""
    main_file: str = Field(description="Content of the main Python file")
    additional_files: Dict[str, str] = Field(description="Additional files needed (filename: content)")
    installation_instructions: str = Field(description="Instructions for installing dependencies")
    usage_examples: str = Field(description="Examples of how to use the agent")
    
    model_config = {
        "json_schema_extra": lambda schema: schema.pop("required", None)
    }
    
    def __init__(self, **data):
        if 'additional_files' not in data:
            data['additional_files'] = {}
        super().__init__(**data)


# ===================== TOOLS =====================

@function_tool
async def analyze_agent_specification(specification_text: str) -> AgentSpecification:
    """
    Analyze a natural language description to extract agent specifications.
    
    Args:
        specification_text: Natural language description of the agent design
        
    Returns:
        Structured agent specification
    """
    # Implementation will be provided by the OpenAI model
    pass


@function_tool
async def design_agent_tools(specification: Dict[str, Any]) -> List[ToolDefinition]:
    """
    Design tools for an agent based on its specification.
    
    Args:
        specification: Structured agent specification
        
    Returns:
        List of tool definitions
    """
    # Implementation will be provided by the OpenAI model
    pass


@function_tool
async def design_output_type(specification: Dict[str, Any]) -> Optional[OutputTypeDefinition]:
    """
    Design a structured output type for an agent if needed.
    
    Args:
        specification: Structured agent specification
        
    Returns:
        Output type definition or None if not needed
    """
    # Implementation will be provided by the OpenAI model
    pass


@function_tool
async def design_guardrails(specification: Dict[str, Any]) -> List[GuardrailDefinition]:
    """
    Design guardrails for an agent based on its specification.
    
    Args:
        specification: Structured agent specification
        
    Returns:
        List of guardrail definitions
    """
    # Implementation will be provided by the OpenAI model
    pass


@function_tool
async def generate_tool_code(tool_definition: Dict[str, Any]) -> str:
    """
    Generate code for a tool based on its definition.
    
    Args:
        tool_definition: Tool definition
        
    Returns:
        Python code implementing the tool
    """
    # Implementation will be provided by the OpenAI model
    pass


@function_tool
async def generate_output_type_code(output_type_definition: Dict[str, Any]) -> str:
    """
    Generate code for an output type based on its definition.
    
    Args:
        output_type_definition: Output type definition
        
    Returns:
        Python code defining the output type
    """
    # Implementation will be provided by the OpenAI model
    pass


@function_tool
async def generate_guardrail_code(guardrail_definition: Dict[str, Any]) -> str:
    """
    Generate code for a guardrail based on its definition.
    
    Args:
        guardrail_definition: Guardrail definition
        
    Returns:
        Python code implementing the guardrail
    """
    # Implementation will be provided by the OpenAI model
    pass


@function_tool
async def generate_agent_creation_code(agent_design: Dict[str, Any]) -> str:
    """
    Generate code that creates an agent instance based on its design.
    
    Args:
        agent_design: Complete agent design
        
    Returns:
        Python code that creates the agent
    """
    # Implementation will be provided by the OpenAI model
    pass


@function_tool
async def generate_runner_code(agent_design: Dict[str, Any]) -> str:
    """
    Generate code that runs the agent.
    
    Args:
        agent_design: Complete agent design
        
    Returns:
        Python code that runs the agent
    """
    # Implementation will be provided by the OpenAI model
    pass


@function_tool
async def assemble_agent_implementation(agent_code: Dict[str, Any]) -> AgentImplementation:
    """
    Assemble the complete agent implementation.
    
    Args:
        agent_code: Generated agent code components
        
    Returns:
        Complete agent implementation with all files
    """
    # Implementation will be provided by the OpenAI model
    pass


@function_tool
async def validate_agent_implementation(implementation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the agent implementation.
    
    Args:
        implementation: Complete agent implementation
        
    Returns:
        Validation results
    """
    # Implementation will be provided by the OpenAI model
    pass


# ===================== META AGENT =====================

# Create the meta agent
agent = Agent(
    name="AgentGenerator",
    description="A meta agent that designs and generates other agents",
    instructions="""
    You are a meta agent designed to create other agents using the OpenAI Agents SDK.
    Your task is to analyze natural language specifications for agents and generate
    complete, functional agent implementations that conform to the OpenAI Agents SDK.
    
    Follow these steps to create an agent:
    1. Analyze the specification to extract the agent's requirements
    2. Design appropriate tools based on the specification
    3. Design a structured output type if needed
    4. Design appropriate guardrails for input/output validation
    5. Generate code for all components
    6. Assemble the complete implementation
    7. Validate the implementation
    
    Be thorough and ensure that the generated agent meets all the requirements
    specified in the natural language description.
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
        validate_agent_implementation
    ]
)


# Create a runner for the agent
runner = Runner(agent)


async def generate_agent(specification: str) -> AgentImplementation:
    """
    Generate an agent based on a natural language specification.
    
    Args:
        specification: Natural language description of the agent to create
        
    Returns:
        Complete agent code
    """
    # Run the agent with the specification
    result = await runner.run(specification)
    
    # Parse the result
    try:
        # Extract imports
        imports = [
            "import os",
            "import asyncio",
            "import json",
            "from typing import Dict, List, Optional, Any",
            "from pydantic import BaseModel, Field",
            "from dotenv import load_dotenv",
            "from agents import Agent, Runner, function_tool, output_guardrail, GuardrailFunctionOutput"
        ]
        
        # Extract agent specification from result
        agent_spec = result.get("agent_specification", {})
        
        # Extract tool definitions from result
        tool_defs = result.get("tool_definitions", [])
        
        # Extract output type definition from result
        output_type_def = result.get("output_type_definition")
        
        # Extract guardrail definitions from result
        guardrail_defs = result.get("guardrail_definitions", [])
        
        # Create agent design
        agent_design = AgentDesign(
            specification=AgentSpecification(**agent_spec),
            tools=[ToolDefinition(**tool) for tool in tool_defs],
            output_type=OutputTypeDefinition(**output_type_def) if output_type_def else None,
            guardrails=[GuardrailDefinition(**guardrail) for guardrail in guardrail_defs]
        )
        
        # Generate tool code
        tool_implementations = []
        for tool in agent_design.tools:
            tool_code = await generate_tool_code(tool.dict())
            tool_implementations.append(tool_code)
        
        # Generate output type code
        output_type_implementation = None
        if agent_design.output_type:
            output_type_implementation = await generate_output_type_code(
                agent_design.output_type.dict()
            )
        
        # Generate guardrail code
        guardrail_implementations = []
        for guardrail in agent_design.guardrails:
            guardrail_code = await generate_guardrail_code(guardrail.dict())
            guardrail_implementations.append(guardrail_code)
        
        # Generate agent creation code
        agent_creation = await generate_agent_creation_code(agent_design.dict())
        
        # Generate runner code
        runner_code = await generate_runner_code(agent_design.dict())
        
        # Create agent code
        agent_code = AgentCode(
            main_code="",  # Will be assembled later
            imports=imports,
            tool_implementations=tool_implementations,
            output_type_implementation=output_type_implementation,
            guardrail_implementations=guardrail_implementations,
            agent_creation=agent_creation,
            runner_code=runner_code
        )
        
        # Assemble the implementation
        implementation = await assemble_agent_implementation(agent_code.dict())
        
        # Validate the implementation
        validation_result = await validate_agent_implementation(implementation.dict())
        
        # Check validation result
        if validation_result.get("valid", False):
            return implementation
        else:
            raise ValueError(f"Agent validation failed: {validation_result.get('errors', [])}")
    
    except Exception as e:
        raise Exception(f"Error generating agent: {str(e)}")


async def main():
    """Main function to run the agent generator."""
    # Example specification
    specification = """
    Create a simple agent that responds to greetings.
    
    Name: GreetingAgent
    
    Description: A simple agent that responds to greetings in different languages.
    
    Instructions: You are a friendly greeting agent. When users greet you in any language,
    respond with an appropriate greeting in the same language. If you're not sure what
    language is being used, respond in English. Be warm and welcoming in your responses.
    
    Tools needed:
    1. detect_language: Detects the language of the input text
       - Parameters: text (string, required)
       - Returns: Language code (e.g., "en", "es", "fr")
    
    2. translate_greeting: Translates a greeting to the specified language
       - Parameters: greeting (string, required), language_code (string, required)
       - Returns: Translated greeting
    
    Output type: A simple text response
    
    Guardrails:
    - Ensure responses are appropriate and respectful
    - Validate that language codes are valid ISO codes
    """
    
    try:
        # Generate the agent
        implementation = await generate_agent(specification)
        
        # Print the implementation
        print("Agent implementation generated successfully!")
        print("\nMain file:")
        print(implementation.main_file[:500] + "..." if len(implementation.main_file) > 500 else implementation.main_file)
        
        print("\nAdditional files:")
        for filename, content in implementation.additional_files.items():
            print(f"\n{filename}:")
            print(content[:200] + "..." if len(content) > 200 else content)
        
        print("\nInstallation instructions:")
        print(implementation.installation_instructions)
        
        print("\nUsage examples:")
        print(implementation.usage_examples)
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
