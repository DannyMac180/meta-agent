# integration_test.py
import asyncio
import sys
import os
import shutil
from meta_agent import generate_agent
from agents import Runner

async def test_agent_generation_and_execution():
    # Test directory
    test_dir = "./test_agent"
    
    # Clean up previous test
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
    
    # Simple agent specification
    specification = """
    Name: EchoAgent
    
    Description: A simple agent that echoes back user input with a prefix.
    
    Instructions: You are an echo agent. When users send you a message, respond by adding "Echo: " before their message.
    """
    
    # Generate the agent
    print("Generating agent...")
    implementation = await generate_agent(specification, output_dir=test_dir)
    
    # Add the test directory to the path
    sys.path.append(test_dir)
    
    # Import the generated agent
    print("Importing generated agent...")
    from agent_implementation import create_agent
    
    # Create the agent
    agent = create_agent()
    
    # Test messages
    test_messages = [
        "Hello world!",
        "Testing the echo agent",
        "Does this work correctly?"
    ]
    
    # Run tests
    print("\nRunning tests:")
    for message in test_messages:
        print(f"\nInput: {message}")
        result = await Runner.run(agent, message)
        print(f"Output: {result.final_output}")
        
        # Simple verification
        if "Echo:" in result.final_output and message in result.final_output:
            print("✅ Test passed")
        else:
            print("❌ Test failed")
    
    # Clean up
    sys.path.remove(test_dir)
    print("\nTests completed.")

if __name__ == "__main__":
    asyncio.run(test_agent_generation_and_execution())
