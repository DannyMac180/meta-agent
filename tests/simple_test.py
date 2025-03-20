import asyncio
from meta_agent.agent_generator import generate_agent

async def main():
    try:
        print("Testing agent generator...")
        result = await generate_agent("""
        Name: SimpleTestAgent
        Instructions: You are a simple test agent that just responds with 'Hello, world!'
        """)
        print("Agent generated successfully!")
        print(result.main_code)
    except Exception as e:
        print(f"Error generating agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())
