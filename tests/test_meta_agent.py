# test_meta_agent.py
import pytest
import asyncio
import os
import shutil
from meta_agent import generate_agent

@pytest.fixture
def test_dir():
    dir_path = "./test_agent_fixture"
    # Setup
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)
    
    yield dir_path
    
    # Teardown
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

@pytest.mark.asyncio
async def test_simple_agent_generation(test_dir):
    # Simple specification
    spec = "Name: TestAgent\nDescription: A test agent\nInstructions: You are a test agent."
    
    # Generate agent
    implementation = await generate_agent(spec, output_dir=test_dir)
    
    # Verify files were created
    assert os.path.exists(os.path.join(test_dir, "agent_implementation.py"))
    assert os.path.exists(os.path.join(test_dir, "README.md"))
    
    # Verify implementation content
    assert "TestAgent" in implementation.main_file
    assert "You are a test agent" in implementation.main_file

# Add more test cases as needed
