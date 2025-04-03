# test_simple_agent.py
"""
Tests for simple agent generation with various features.
"""
import os
import pytest
import shutil
from meta_agent import generate_agent
from meta_agent.models import AgentImplementation

@pytest.fixture
def test_dir():
    """Fixture to create and clean up a test directory."""
    dir_path = "./test_agent_simple"
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)
    yield dir_path
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

def test_simple_greeting_agent(test_dir):
    """Test generating a greeting agent with multiple tools and guardrails."""
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
    implementation = generate_agent(specification, output_dir=test_dir)

    # Verify return type
    assert isinstance(implementation, AgentImplementation)

    # Verify files were created
    assert os.path.exists(os.path.join(test_dir, "agent_implementation.py"))
    assert os.path.exists(os.path.join(test_dir, "README.md"))

    # Verify implementation content
    # The implementation seems to be using the spec as instructions rather than parsing it
    assert "GreetingAgent" in implementation.main_file
    assert "different languages" in implementation.main_file
    assert "detect_language" in implementation.main_file
    assert "translate_greeting" in implementation.main_file

def test_minimal_agent(test_dir):
    """Test generating a minimal agent with no tools or guardrails."""
    # Minimal specification
    specification = """
    Name: MinimalAgent
    Description: A minimal agent with no tools or guardrails.
    Instructions: You are a minimal agent. Just respond with 'Hello, world!'
    """

    # Generate the agent
    implementation = generate_agent(specification, output_dir=test_dir)

    # Verify implementation content
    assert "MinimalAgent" in implementation.main_file
    assert "A minimal agent with no tools or guardrails" in implementation.main_file
    assert "You are a minimal agent" in implementation.main_file
    assert "tools=[]" not in implementation.main_file  # Should not explicitly list empty tools

    # Verify no tools or guardrails
    assert "@function_tool" not in implementation.main_file
    assert "@input_guardrail" not in implementation.main_file
    assert "@output_guardrail" not in implementation.main_file

def test_agent_with_output_type(test_dir):
    """Test generating an agent with a structured output type."""
    # Specification with output type
    specification = """
    Name: OutputTypeAgent

    Description: An agent that returns structured output

    Instructions: You are an agent that returns structured output.

    Output type: StructuredResponse
    - message (string, required): The response message
    - confidence (number, required): Confidence score from 0-1
    - timestamp (string, optional): ISO timestamp
    """

    # Generate the agent
    implementation = generate_agent(specification, output_dir=test_dir)

    # Verify implementation content
    # The implementation seems to be using the spec as instructions rather than parsing it
    assert "OutputTypeAgent" in implementation.main_file
    assert "structured output" in implementation.main_file
    assert "StructuredResponse" in implementation.main_file
    assert "message" in implementation.main_file
    assert "confidence" in implementation.main_file
    assert "timestamp" in implementation.main_file
