"""
Example script demonstrating how to use the meta-agent package to create a simple agent.
"""

import asyncio
import os
from dotenv import load_dotenv
from meta_agent import generate_agent

# Load environment variables from .env file
load_dotenv()

# Check for API key
if not os.environ.get("OPENAI_API_KEY"):
    print("Error: OPENAI_API_KEY environment variable not set.")
    print("Please set your OpenAI API key in the .env file or as an environment variable:")
    print("export OPENAI_API_KEY='your-api-key'")
    exit(1)

async def main():
    """Create a simple greeting agent."""
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
        print("Generating greeting agent...")
        implementation = await generate_agent(specification)
        
        # Save the agent files
        print("\nSaving agent files...")
        
        # Create output directory
        os.makedirs("greeting_agent", exist_ok=True)
        
        # Save main file
        with open("greeting_agent/agent.py", "w") as f:
            f.write(implementation.main_file)
        print("Created greeting_agent/agent.py")
        
        # Save additional files
        for filename, content in implementation.additional_files.items():
            file_path = f"greeting_agent/{filename}"
            with open(file_path, "w") as f:
                f.write(content)
            print(f"Created greeting_agent/{filename}")
        
        # Print installation and usage instructions
        print("\nInstallation Instructions:")
        print(implementation.installation_instructions)
        
        print("\nUsage Examples:")
        print(implementation.usage_examples)
        
    except Exception as e:
        print(f"Error generating agent: {e}")

if __name__ == "__main__":
    asyncio.run(main())
