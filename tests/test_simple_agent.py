# test_simple_agent.py
import asyncio
from meta_agent import generate_agent

async def main():
    # Simple agent specification
    specification = """
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
    """
    
    # Generate the agent
    implementation = await generate_agent(specification, output_dir="./generated_greeting_agent")
    
    # Print the implementation
    print("Agent implementation generated successfully!")
    print("\nMain file preview:")
    print(implementation.main_file[:500] + "..." if len(implementation.main_file) > 500 else implementation.main_file)

if __name__ == "__main__":
    asyncio.run(main())