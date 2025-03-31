import asyncio
from typing import Dict, List, Any, Optional
from agents import Agent, Runner, function_tool

def create_agent():
    """
    Create a GreetingAgent agent based on the specification.
    
    Returns:
        An initialized Agent instance
    """
    # Agent configuration
    agent = Agent(
        name="GreetingAgent",
        description="",
        instructions="""
    Name: GreetingAgent
    
    Description: A simple agent that responds to greetings in different languages.
    
    Instructions: You are a friendly greeting agent. When users greet you in any language,
    respond with an appropriate greeting in the same language. If you're not sure what
    language is being used, respond in English. Be warm and welcoming in your responses.
    
    Tools:
    1. detect_language: Detects the language of the input text
       - language_text (string, required): The text to detect language for
       - Returns: Language code (e.g., "en", "es", "fr")
    
    2. translate_greeting: Translates a greeting to the specified language
       - greeting (string, required): The greeting to translate
       - language_code (string, required): The language code to translate to
       - Returns: Translated greeting
    
    Output type: A simple text response
    
    Guardrails:
    - Ensure responses are appropriate and respectful
    - Validate that language codes are valid ISO codes
    """,
        tools=[
            detect_language,
            translate_greeting,
        ],
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