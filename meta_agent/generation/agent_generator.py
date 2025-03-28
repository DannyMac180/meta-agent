"""
Agent creation code generator for the meta-agent package.

This module contains the main meta agent that orchestrates the whole agent generation process.
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from agents import Agent
from meta_agent.decorators import function_tool as meta_function_tool
from meta_agent.models.agent import AgentSpecification, Agent

# Import all specialized agents
from meta_agent.design.analyzer import analyze_agent_specification
from meta_agent.design.tool_designer import design_agent_tools
from meta_agent.design.output_designer import design_output_type
from meta_agent.generation.tool_generator import generate_tool_code
from meta_agent.generation.output_generator import generate_output_type_code
from meta_agent.generation.agent_code_generator import generate_agent_creation_code
from meta_agent.generation.runner_generator import generate_runner_code
from meta_agent.generation.assembler import assemble_agent_implementation

# Import models for type hinting in tools
from meta_agent.models import AgentSpecification, ToolDefinition, OutputTypeDefinition, GuardrailDefinition, AgentImplementation, AgentCode


class AgentSpec(BaseModel):
    """Specification for agent creation"""
    name: str
    instructions: str
    model: Optional[str] = "gpt-4o"
    tools: List[Dict[str, Any]] = []
    output_type: Optional[str] = None
    guardrails: List[Dict[str, Any]] = []
    handoffs: List[Dict[str, Any]] = []


# The main meta agent that orchestrates the whole process
# This agent uses function calling to structure its output for each step.
agent_generator = Agent(
    name="MetaAgentGenerator",
    instructions="""
    You are an expert Python programmer specializing in the OpenAI Agents SDK. Your task is to generate a complete, runnable Python agent implementation based on a user's natural language specification.
    You must follow the structure and patterns of the OpenAI Agents SDK precisely, as shown in the provided documentation examples (like the weather agent).
    The final output should be a single Python file containing the agent definition, necessary tools defined with `@function_tool`, imports, and a simple runner (`async def main(): ...`).

    **IMPORTANT: You MUST use the provided function tools to structure your output for each step. DO NOT generate code directly in your responses.**

    **CRITICAL: When using a tool, you MUST ONLY return the tool's output. DO NOT add any additional text before or after the tool output.**

    **Workflow:**

    1.  **Analyze Specification:** Use the `analyze_agent_specification` tool to parse the user's request and create a structured `AgentSpecification`. The tool expects a string input and returns a JSON string.
    
    2.  **Design Tools:** Based on the `AgentSpecification`, use the `design_agent_tools` tool to define the necessary tools, including their names, descriptions, parameters (with types and required status), and return types. The tool returns a JSON string with a "tools" array.
    
    3.  **Design Output Type (Optional):** If the specification requires structured output, use the `design_output_type` tool to define a Pydantic model for it. The tool returns a JSON string.
    
    4.  **Generate Tool Code:** For each `ToolDefinition` from step 2, use the `generate_tool_code` tool to generate the full Python function code, including the `@function_tool` decorator, type hints, docstring, and a placeholder implementation comment (`# TODO: Implement actual logic`). The tool returns a JSON string with a "code" field.
    
    5.  **Generate Output Type Code (Optional):** If an `OutputTypeDefinition` was created in step 3, use the `generate_output_type_code` tool to generate the Pydantic class definition. The tool returns a JSON string with a "code" field.
    
    6.  **Generate Agent Definition Code:** Use the `generate_agent_creation_code` tool to generate the Python code that defines the `Agent` instance, including its name, instructions, and the list of tool *function names* (not the code itself). Include the `output_type` if defined. The tool returns a JSON string with a "code" field.
    
    7.  **Generate Runner Code:** Use the `generate_runner_code` tool to generate a standard `async def main(): ...` block that initializes a `Runner` and runs the agent with sample input or in an interactive loop. The tool returns a JSON string with a "code" field.
    
    8.  **Assemble Implementation:** Use the `assemble_agent_implementation` tool, providing all the generated code pieces (imports, tool code, output type code, agent definition code, runner code) to construct the final `AgentImplementation` object. The tool returns a JSON string.

    **Output Requirements:**

    *   All tool outputs MUST be valid JSON strings.
    *   DO NOT generate code directly in your responses.
    *   Use the provided tools for all code generation.
    *   Each tool's output will be used as input for subsequent steps.
    *   The final implementation must be runnable Python code.
    *   NEVER add any text before or after a tool's output.
    
    Remember: ALWAYS use the tools to generate code. NEVER output code directly in your responses.
    """,
    model="gpt-4o", # Use a capable model
    tools=[
        analyze_agent_specification,
        design_agent_tools,
        design_output_type,
        # design_guardrails, # Temporarily disable guardrails for simplicity
        generate_tool_code,
        generate_output_type_code,
        # generate_guardrail_code, # Temporarily disable guardrails for simplicity
        generate_agent_creation_code,
        generate_runner_code,
        assemble_agent_implementation
        # validate_agent_implementation # Validation can be added back later
    ]
)
