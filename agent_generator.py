"""
Agent Generator - A meta agent that creates OpenAI Agents SDK agents

This script implements a meta agent that can design and generate other agents
using the OpenAI Agents SDK based on natural language specifications.
"""

import asyncio
import json
import os
from typing import Any, List, Optional, Dict, Union, Literal
from pydantic import BaseModel, Field

from agents import (
    Agent, 
    Runner,
    function_tool,
    output_guardrail,
    GuardrailFunctionOutput
)


# Configure OpenAI API key
# Try to get API key from environment variable
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY environment variable not set.")
    print("Please set your OpenAI API key using:")
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
def analyze_agent_specification(specification_text: str) -> Dict[str, Any]:
    """
    Analyze a natural language description to extract agent specifications.
    
    Args:
        specification_text: Natural language description of the agent design
        
    Returns:
        Structured agent specification
    """
    # This is a placeholder - in real implementation, the LLM would analyze the text
    # and extract the specification details
    return {"analyzed": True}


@function_tool
def design_agent_tools(specification: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Design tools for an agent based on its specification.
    
    Args:
        specification: Structured agent specification
        
    Returns:
        List of tool definitions
    """
    # This is a placeholder - in real implementation, the LLM would design
    # appropriate tools based on the specification
    return [{"tool_designed": True}]


@function_tool
def design_output_type(specification: Dict[str, Any]) -> Dict[str, Any]:
    """
    Design a structured output type for an agent if needed.
    
    Args:
        specification: Structured agent specification
        
    Returns:
        Output type definition or None if not needed
    """
    # This is a placeholder - in real implementation, the LLM would design
    # an appropriate output type based on the specification
    return {"output_type_designed": True}


@function_tool
def design_guardrails(specification: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Design guardrails for an agent based on its specification.
    
    Args:
        specification: Structured agent specification
        
    Returns:
        List of guardrail definitions
    """
    # This is a placeholder - in real implementation, the LLM would design
    # appropriate guardrails based on the specification
    return [{"guardrail_designed": True}]


@function_tool
def generate_tool_code(tool_definition: Dict[str, Any]) -> str:
    """
    Generate code for a tool based on its definition.
    
    Args:
        tool_definition: Tool definition
        
    Returns:
        Python code implementing the tool
    """
    # This is a placeholder - in real implementation, the LLM would generate
    # actual Python code for the tool
    return "# Tool code would be generated here"


@function_tool
def generate_output_type_code(output_type_definition: Dict[str, Any]) -> str:
    """
    Generate code for an output type based on its definition.
    
    Args:
        output_type_definition: Output type definition
        
    Returns:
        Python code defining the output type
    """
    # This is a placeholder - in real implementation, the LLM would generate
    # actual Python code for the output type
    return "# Output type code would be generated here"


@function_tool
def generate_guardrail_code(guardrail_definition: Dict[str, Any]) -> str:
    """
    Generate code for a guardrail based on its definition.
    
    Args:
        guardrail_definition: Guardrail definition
        
    Returns:
        Python code implementing the guardrail
    """
    # This is a placeholder - in real implementation, the LLM would generate
    # actual Python code for the guardrail
    return "# Guardrail code would be generated here"


@function_tool
def generate_agent_creation_code(agent_design: Dict[str, Any]) -> str:
    """
    Generate code that creates an agent instance based on its design.
    
    Args:
        agent_design: Complete agent design
        
    Returns:
        Python code that creates the agent
    """
    # This is a placeholder - in real implementation, the LLM would generate
    # actual Python code that creates the agent
    return "# Agent creation code would be generated here"


@function_tool
def generate_runner_code(agent_design: Dict[str, Any]) -> str:
    """
    Generate code that runs the agent.
    
    Args:
        agent_design: Complete agent design
        
    Returns:
        Python code that runs the agent
    """
    # This is a placeholder - in real implementation, the LLM would generate
    # actual Python code that runs the agent
    return "# Runner code would be generated here"


@function_tool
def assemble_agent_implementation(agent_code: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assemble the complete agent implementation.
    
    Args:
        agent_code: Generated agent code components
        
    Returns:
        Complete agent implementation with all files
    """
    # This is a placeholder - in real implementation, the LLM would assemble
    # all the code components into a complete implementation
    return {"implementation_assembled": True}


@function_tool
def validate_agent_implementation(implementation: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the agent implementation.
    
    Args:
        implementation: Complete agent implementation
        
    Returns:
        Validation results
    """
    # This is a placeholder - in real implementation, the LLM would validate
    # the implementation for correctness
    return {"validation_result": "passed"}


# ===================== AGENT DEFINITIONS =====================

# Agent for analyzing specifications
specification_analyzer = Agent(
    name="specification_analyzer",
    instructions="""
    You are a specification analyzer agent. Your job is to analyze a natural language description
    of an agent and extract a structured specification.
    
    Extract the following information:
    1. Agent name and description
    2. Detailed instructions for the agent
    3. Tools the agent needs
    4. Output type if structured output is needed
    5. Guardrails that should be implemented
    6. Handoffs to other agents if needed
    
    Be thorough and make sure to capture all the important details.
    """,
    tools=[analyze_agent_specification]
)

# Agent for designing tools
tool_designer = Agent(
    name="tool_designer",
    instructions="""
    You are a tool designer agent. Your job is to design tools for an agent based on its specification.
    
    For each tool, define:
    1. Name and description
    2. Parameters with types and descriptions
    3. Return type
    4. Implementation logic
    
    Make sure the tools are well-designed and meet the agent's needs.
    """,
    tools=[design_agent_tools]
)

# Agent for designing output types
output_type_designer = Agent(
    name="output_type_designer",
    instructions="""
    You are an output type designer agent. Your job is to design a structured output type
    for an agent if needed based on its specification.
    
    If an output type is needed, define:
    1. Name of the output type
    2. Fields with types and descriptions
    3. Implementation as a Pydantic model
    
    If no output type is needed, return None.
    """,
    tools=[design_output_type]
)

# Agent for designing guardrails
guardrail_designer = Agent(
    name="guardrail_designer",
    instructions="""
    You are a guardrail designer agent. Your job is to design guardrails for an agent
    based on its specification.
    
    For each guardrail, define:
    1. Name and type (input or output)
    2. Validation logic
    3. Implementation as a guardrail function
    
    Make sure the guardrails effectively enforce the constraints specified.
    """,
    tools=[design_guardrails]
)

# Agent for generating tool code
tool_code_generator = Agent(
    name="tool_code_generator",
    instructions="""
    You are a tool code generator agent. Your job is to generate Python code
    for tools based on their definitions.
    
    Generate code that:
    1. Uses the @function_tool decorator
    2. Has proper parameter typing
    3. Implements the tool's functionality
    4. Includes docstrings and comments
    
    Make sure the code is correct and follows best practices.
    """,
    tools=[generate_tool_code]
)

# Agent for generating output type code
output_type_code_generator = Agent(
    name="output_type_code_generator",
    instructions="""
    You are an output type code generator agent. Your job is to generate Python code
    for output types based on their definitions.
    
    Generate code that:
    1. Defines a Pydantic model
    2. Has proper field typing and descriptions
    3. Includes docstrings and comments
    
    Make sure the code is correct and follows best practices.
    """,
    tools=[generate_output_type_code]
)

# Agent for generating guardrail code
guardrail_code_generator = Agent(
    name="guardrail_code_generator",
    instructions="""
    You are a guardrail code generator agent. Your job is to generate Python code
    for guardrails based on their definitions.
    
    Generate code that:
    1. Uses the @output_guardrail or @input_guardrail decorator
    2. Implements the validation logic
    3. Returns appropriate GuardrailFunctionOutput
    4. Includes docstrings and comments
    
    Make sure the code is correct and follows best practices.
    """,
    tools=[generate_guardrail_code]
)

# Agent for generating agent creation code
agent_creation_code_generator = Agent(
    name="agent_creation_code_generator",
    instructions="""
    You are an agent creation code generator. Your job is to generate Python code
    that creates an agent instance based on its design.
    
    Generate code that:
    1. Creates an Agent instance with the right parameters
    2. Sets up tools, output type, and guardrails
    3. Includes docstrings and comments
    
    Make sure the code is correct and follows best practices.
    """,
    tools=[generate_agent_creation_code]
)

# Agent for generating runner code
runner_code_generator = Agent(
    name="runner_code_generator",
    instructions="""
    You are a runner code generator. Your job is to generate Python code
    that runs an agent based on its design.
    
    Generate code that:
    1. Sets up an async main function
    2. Gets input from the user or another source
    3. Runs the agent using Runner.run
    4. Handles the output appropriately
    5. Includes docstrings and comments
    
    Make sure the code is correct and follows best practices.
    """,
    tools=[generate_runner_code]
)

# Agent for assembling the implementation
implementation_assembler = Agent(
    name="implementation_assembler",
    instructions="""
    You are an implementation assembler agent. Your job is to assemble all the code
    components into a complete agent implementation.
    
    Assemble:
    1. The main Python file with all necessary imports
    2. Any additional files needed
    3. Installation instructions
    4. Usage examples
    
    Make sure everything is properly organized and ready to use.
    """,
    tools=[assemble_agent_implementation]
)

# Agent for validating the implementation
implementation_validator = Agent(
    name="implementation_validator",
    instructions="""
    You are an implementation validator agent. Your job is to validate the
    complete agent implementation for correctness.
    
    Check for:
    1. Syntax errors
    2. Logical errors
    3. Compliance with OpenAI Agents SDK patterns
    4. Implementation of all specified features
    
    Provide a detailed validation report with any issues found and suggestions for improvement.
    """,
    tools=[validate_agent_implementation]
)

# The main meta agent that orchestrates the whole process
agent_generator = Agent(
    name="agent_generator",
    instructions="""
    You are an agent generator designed to create other agents using the OpenAI Agents SDK.
    You take a natural language description of an agent design and produce Python code
    for a fully functional agent.
    
    Your workflow:
    1. Analyze the natural language specification
    2. Design tools, output types, and guardrails
    3. Generate code for each component
    4. Assemble the complete implementation
    5. Validate the implementation
    
    You will use specialized agents for each step of the process.
    """,
    handoffs=[
        specification_analyzer,
        tool_designer,
        output_type_designer,
        guardrail_designer,
        tool_code_generator,
        output_type_code_generator,
        guardrail_code_generator,
        agent_creation_code_generator,
        runner_code_generator,
        implementation_assembler,
        implementation_validator
    ]
)


# ===================== MAIN FUNCTION =====================

async def generate_agent(specification: str) -> AgentImplementation:
    """
    Generate an agent based on a natural language specification.
    
    Args:
        specification: Natural language description of the agent to create
        
    Returns:
        Complete agent implementation
    """
    result = await Runner.run(agent_generator, input=specification)
    
    # Convert the result to AgentImplementation
    if isinstance(result, dict):
        # If the result is a dictionary, convert it to AgentImplementation
        return AgentImplementation(
            main_file=result.get("main_file", ""),
            additional_files=result.get("additional_files", {}),
            installation_instructions=result.get("installation_instructions", ""),
            usage_examples=result.get("usage_examples", "")
        )
    elif hasattr(result, "final_output") and isinstance(result.final_output, dict):
        # If the result has a final_output attribute and it's a dictionary
        return AgentImplementation(
            main_file=result.final_output.get("main_file", ""),
            additional_files=result.final_output.get("additional_files", {}),
            installation_instructions=result.final_output.get("installation_instructions", ""),
            usage_examples=result.final_output.get("usage_examples", "")
        )
    else:
        # If the result is something else, try to convert it to a string
        return AgentImplementation(
            main_file=str(result),
            additional_files={},
            installation_instructions="# No installation instructions available",
            usage_examples="# No usage examples available"
        )


async def main():
    """Main function to run the agent generator."""
    # Get the agent specification from the user
    print("Welcome to the OpenAI Agents SDK Agent Generator!")
    print("Please describe the agent you want to create:")
    specification = input("> ")
    
    print("\nGenerating agent based on your specification...")
    try:
        implementation = await generate_agent(specification)
        
        # Print the implementation details
        print("\nAgent generation complete!")
        print("\nMain file:")
        print(f"Length: {len(implementation.main_file)} characters")
        
        # Save the implementation files
        with open("generated_agent.py", "w") as f:
            f.write(implementation.main_file)
        print("\nSaved main file to generated_agent.py")
        
        for filename, content in implementation.additional_files.items():
            with open(filename, "w") as f:
                f.write(content)
            print(f"Saved additional file to {filename}")
        
        # Print installation and usage instructions
        print("\nInstallation Instructions:")
        print(implementation.installation_instructions)
        
        print("\nUsage Examples:")
        print(implementation.usage_examples)
        
    except Exception as e:
        print(f"Error generating agent: {e}")


if __name__ == "__main__":
    asyncio.run(main())
