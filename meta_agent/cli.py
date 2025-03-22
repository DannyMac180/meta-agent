"""
Command Line Interface for Meta Agent

This module provides a command-line interface for the Meta Agent.
"""

import asyncio
import argparse
import sys
import os

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
        
        # Write main file
        main_file_path = os.path.join(args.output, "agent.py")
        write_file(main_file_path, agent_implementation.main_file)
        print(f"Generated main agent file: {main_file_path}")
        
        # Write additional files
        for filename, content in agent_implementation.additional_files.items():
            file_path = os.path.join(args.output, filename)
            write_file(file_path, content)
            print(f"Generated additional file: {file_path}")
        
        # Save installation instructions
        if agent_implementation.installation_instructions:
            install_file_path = os.path.join(args.output, "INSTALL.md")
            write_file(install_file_path, agent_implementation.installation_instructions)
            print(f"Generated installation instructions file: {install_file_path}")
        
        # Save usage examples
        if agent_implementation.usage_examples:
            usage_file_path = os.path.join(args.output, "USAGE.md")
            write_file(usage_file_path, agent_implementation.usage_examples)
            print(f"Generated usage examples file: {usage_file_path}")
        
        # Print installation and usage instructions
        print("\nInstallation Instructions:")
        print(agent_implementation.installation_instructions)
        
        print("\nUsage Examples:")
        print(agent_implementation.usage_examples)
        
    except Exception as e:
        print(f"Error generating agent: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
