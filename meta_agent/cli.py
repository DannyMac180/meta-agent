"""
Command Line Interface for Meta Agent

This module provides a command-line interface for the Meta Agent.
"""

import asyncio
import argparse
import sys
import os
import importlib.util
import pathlib
import re

# Add parent directory to path to allow imports
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from meta_agent.core import generate_agent
from meta_agent.config import config, load_config, check_api_key, print_api_key_warning
from meta_agent.utils import write_file


def main():
    """Main entry point for the CLI."""
    # Load environment variables from .env file
    load_config()

    # Check for API key
    if not check_api_key():
        print_api_key_warning()
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Meta Agent - Generate OpenAI Agents SDK agents from natural language specifications"
    )
    parser.add_argument(
        "--spec", "-s",
        type=str,
        help="Natural language specification for the agent to generate"
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to a file containing the agent specification"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=".",
        help="Output directory for the generated agent code (default: current directory)"
    )

    args = parser.parse_args()

    # Get specification from file or command line
    specification = ""
    if args.file:
        try:
            with open(args.file, "r") as f:
                specification = f.read()
        except Exception as e:
            print(f"Error reading specification file: {e}")
            sys.exit(1)
    elif args.spec:
        specification = args.spec
    else:
        parser.print_help()
        sys.exit(1)

    # Generate the agent
    try:
        agent_implementation = asyncio.run(generate_agent(specification))
        
        # Create output directory if it doesn't exist
        os.makedirs(args.output, exist_ok=True)
        
        # Extract the agent name from the main file code
        agent_name_match = re.search(r'class\s+(\w+)\(Agent\)', agent_implementation.main_file)
        if agent_name_match:
            agent_name = agent_name_match.group(1)
        else:
            # Fallback to extracting from name attribute if class definition not found
            name_match = re.search(r'name="([^"]+)"', agent_implementation.main_file)
            if name_match:
                agent_name = name_match.group(1)
            else:
                agent_name = "DefaultAgent"
        
        # Create snake_case filename from agent name
        agent_filename = agent_name.lower().replace(' ', '_') + '.py'
        
        # Write main file
        main_file_path = os.path.join(args.output, agent_filename)
        write_file(main_file_path, agent_implementation.main_file)
        print(f"Generated agent file: {main_file_path}")
        
        # Write additional files
        for filename, content in agent_implementation.additional_files.items():
            file_path = os.path.join(args.output, filename)
            write_file(file_path, content)
            print(f"Generated additional file: {file_path}")
        
        # Print a simple success message
        print(f"\nAgent {agent_name} successfully generated!")
        
    except Exception as e:
        print(f"Error generating agent: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
