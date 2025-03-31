# test_research_agent.py
import asyncio
import os
from meta_agent import generate_agent

async def main():
    # Read the research agent specification from file
    with open("agent_spec/research_agent_spec.txt", "r") as f:
        specification = f.read()
    
    # Generate the agent
    implementation = await generate_agent(specification, output_dir="./generated_research_agent_from_spec")
    
    # Print the implementation
    print("Agent implementation generated successfully!")
    print("\nMain file preview:")
    print(implementation.main_file[:500] + "..." if len(implementation.main_file) > 500 else implementation.main_file)

if __name__ == "__main__":
    asyncio.run(main())
