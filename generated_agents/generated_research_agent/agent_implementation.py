import asyncio
from typing import Dict, List, Any, Optional
from agents import Agent, Runner, function_tool

def create_agent():
    """
    Create a ResearchAgent agent based on the specification.
    
    Returns:
        An initialized Agent instance
    """
    # Agent configuration
    agent = Agent(
        name="ResearchAgent",
        description="An agent that performs web research on topics",
        instructions="""You are a research assistant that helps users find information on various topics. Use the search tool to find relevant information and summarize it concisely.""",
        tools=[
            search_web,
        ],
        output_type=string,
    )
    return agent

async def main():
    # Create the agent
    agent = create_agent()

    # Example usage
    result = await Runner.run(agent, "Hello, I need your assistance.")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())