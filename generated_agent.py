"""
WeatherAgent - An agent that provides weather information for different locations

This is a self-contained agent implementation using the OpenAI Agents SDK v0.0.7.
"""

import asyncio
import os
from typing import Dict, List, Any, Optional

from pydantic import BaseModel, Field
from agents import Agent, Runner, function_tool, input_guardrail, output_guardrail, GuardrailFunctionOutput

# Check for OpenAI API key
if not os.environ.get("OPENAI_API_KEY"):
    print("Warning: OPENAI_API_KEY environment variable not set.")
    print("Please set it with: export OPENAI_API_KEY=your_api_key")

# Tool Definitions
from agents import function_tool

# The following imports might be needed depending on the tools

import os

import json

from typing import Dict, List, Any, Optional



@function_tool
def get_weather() -> str:
    """
Fetches current weather information for a location
   - location (string, required): The name of the location (city, country, etc.)
   - units (string, optional): The unit system to use (metric or imperial)
   - Returns: Weather information including temperature, conditions, and forecast


Returns:
    str: string result
"""
    import json
    try:
        params = {}
        return json.dumps(params)
    except Exception as e:
        return f"Error in generated tool: {str(e)}"

# Guardrail Definitions
@output_guardrail
def validate_ensure_responses_are_weather_r(output_text: str) -> GuardrailFunctionOutput:
    """
    Ensure responses are weather-related and helpful
    
    Args:
        output_text: The output text to validate
    
    Returns:
        GuardrailFunctionOutput indicating whether the output is valid
    """
    # TODO: Implement the guardrail validation logic
    # This is a placeholder implementation
    return GuardrailFunctionOutput(is_valid=True)

# Agent Creation
def create_agent():
    """
    Create a WeatherAgent agent.
    
    Returns:
        An initialized Agent instance
    """
    # Create the agent
    agent = Agent(
        name="WeatherAgent",
        instructions="""You are a helpful weather assistant. When users ask about the weather in a specific location, use the get_weather tool to fetch the current weather information and provide it in a friendly, conversational manner. If the user doesn't specify a location, ask them for one. You can also provide general weather-related advice.""",
        tools=[
            get_weather,
        ],
        output_guardrails=[
            validate_ensure_responses_are_weather_r,
        ],
    )
    return agent

# Agent Runner
async def run_agent(input_text: str):
    """
    Run the agent with the given input text.
    
    Args:
        input_text: The input text to send to the agent
    
    Returns:
        The agent's response
    """
    agent = create_agent()
    result = await Runner.run(agent, input_text)
    return result.final_output


async def main():
    """
    Main function to run the agent interactively.
    """
    print("Agent is ready. Type 'exit' to quit.")
    while True:
        user_input = input("> ")
        if user_input.lower() == 'exit':
            break
        
        try:
            agent_result = await run_agent(user_input)
            print(f"\nAgent: {agent_result}\n")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())