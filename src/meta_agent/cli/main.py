from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

import click
import sys
import yaml
import json
import asyncio
from pathlib import Path
from pydantic import ValidationError

from meta_agent.models.spec_schema import SpecSchema
from meta_agent.orchestrator import MetaAgentOrchestrator
from meta_agent.planning_engine import PlanningEngine
from meta_agent.sub_agent_manager import SubAgentManager
from meta_agent.registry import ToolRegistry
from meta_agent.tool_designer import ToolDesignerAgent
# TODO: Import logging setup from utils

@click.group()
def cli():
    """Meta-Agent: A tool to generate AI agent code from specifications."""
    # TODO: Configure logging
    pass

@click.option('--spec-file', type=click.Path(exists=True, dir_okay=False, path_type=Path), 
              help='Path to the specification file (JSON or YAML).')
@click.option('--spec-text', type=str, 
              help='Specification provided as a text string.')
async def generate(spec_file: Path | None, spec_text: str | None):
    """Generate agent code based on a specification."""
    if not spec_file and not spec_text:
        click.echo("Error: Please provide either --spec-file or --spec-text.", err=True)
        sys.exit(1)
    if spec_file and spec_text:
        click.echo("Error: Please provide only one of --spec-file or --spec-text.", err=True)
        sys.exit(1)

    spec: SpecSchema | None = None
    raw_spec_data: dict | str | None = None

    try:
        if spec_file:
            click.echo(f"Reading specification from file: {spec_file}")
            raw_spec_data = spec_file # Keep path for now, parsing happens in SpecSchema
            if spec_file.suffix.lower() == '.json':
                spec = SpecSchema.from_json(spec_file)
            elif spec_file.suffix.lower() in ['.yaml', '.yml']:
                spec = SpecSchema.from_yaml(spec_file)
            else:
                # TODO: Add support for attempting text parse from unknown file types?
                click.echo(f"Error: Unsupported file type: {spec_file.suffix}. Please use JSON or YAML.", err=True)
                sys.exit(1)

        elif spec_text:
            click.echo("Processing specification from text input...")
            raw_spec_data = spec_text
            # Attempt structured parse first (e.g., if user pastes JSON/YAML)
            try:
                # Try JSON
                data = json.loads(spec_text)
                spec = SpecSchema.from_dict(data)
                click.echo("Parsed spec-text as JSON.")
            except json.JSONDecodeError:
                try:
                    # Try YAML
                    data = yaml.safe_load(spec_text)
                    if isinstance(data, dict):
                        spec = SpecSchema.from_dict(data)
                        click.echo("Parsed spec-text as YAML.")
                    else:
                        # If YAML parses but not to a dict, treat as text
                        raise yaml.YAMLError("Parsed YAML is not a dictionary")
                except yaml.YAMLError:
                    # Fallback to free-form text parsing
                    click.echo("Parsing spec-text as free-form text.")
                    spec = SpecSchema.from_text(spec_text)
            except ValidationError as e:
                 click.echo(f"Error validating structured text input: {e}", err=True)
                 sys.exit(1)

        if spec:
            click.echo("Specification parsed successfully:")
            # TODO: Implement actual agent generation logic (later tasks)
            click.echo(f"  Task Description: {spec.task_description[:100]}...") 
            click.echo(f"  Inputs: {spec.inputs}")
            click.echo(f"  Outputs: {spec.outputs}")
            # Instantiate components
            # TODO: Configure these properly, maybe via CLI options or config files
            planning_engine = PlanningEngine()
            sub_agent_manager = SubAgentManager()
            tool_registry = ToolRegistry()
            tool_designer_agent = ToolDesignerAgent()
            orchestrator = MetaAgentOrchestrator(
                planning_engine=planning_engine,
                sub_agent_manager=sub_agent_manager,
                tool_registry=tool_registry,
                tool_designer_agent=tool_designer_agent,
            )

            # Run the orchestration
            click.echo("\nStarting agent generation orchestration...")
            # Convert Pydantic model to dict for the orchestrator
            spec_dict = spec.model_dump(exclude_unset=True) 
            results = await orchestrator.run(specification=spec_dict)
            click.echo("\nOrchestration finished.")
            click.echo(f"Results: {json.dumps(results, indent=2)}")

        else:
             # This case should ideally not be reached due to prior checks/errors
            click.echo("Error: Could not parse or load specification.", err=True)
            sys.exit(1)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except (ValidationError, json.JSONDecodeError, yaml.YAMLError, TypeError) as e:
        click.echo(f"Error processing specification: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        # Generic catch-all
        click.echo(f"An unexpected error occurred: {e}", err=True)
        # TODO: Add proper logging here
        sys.exit(1)

# Note: This basic setup works for a single async command.
# If more async commands are added, a more robust asyncio setup might be needed.
@cli.command(name='generate')
@click.option('--spec-file', type=click.Path(exists=True, dir_okay=False, path_type=Path), 
              help='Path to the specification file (JSON or YAML).')
@click.option('--spec-text', type=str, 
              help='Specification provided as a text string.')
def generate_command_wrapper(spec_file, spec_text):
    asyncio.run(generate(spec_file, spec_text))

async def create_tool(spec_file: Path, use_llm: bool, version: str):
    """Create a tool based on a specification file."""
    click.echo(f"Reading tool specification from file: {spec_file}")
    
    try:
        # Parse the specification file
        tool_spec = None
        if spec_file.suffix.lower() == '.json':
            with open(spec_file, 'r') as f:
                tool_spec = json.load(f)
            click.echo("Parsed tool specification from JSON file.")
        elif spec_file.suffix.lower() in ['.yaml', '.yml']:
            with open(spec_file, 'r') as f:
                tool_spec = yaml.safe_load(f)
            click.echo("Parsed tool specification from YAML file.")
        else:
            click.echo(f"Error: Unsupported file type: {spec_file.suffix}. Please use JSON or YAML.", err=True)
            sys.exit(1)
        
        if not tool_spec:
            click.echo("Error: Empty or invalid tool specification.", err=True)
            sys.exit(1)
        
        # Validate basic structure
        if not isinstance(tool_spec, dict):
            click.echo("Error: Tool specification must be a dictionary/object.", err=True)
            sys.exit(1)
        
        if "name" not in tool_spec:
            click.echo("Error: Tool specification must include a 'name' field.", err=True)
            sys.exit(1)
        
        # Initialize components
        click.echo("Initializing components for tool creation...")
        sub_agent_manager = SubAgentManager()
        tool_registry = ToolRegistry()
        tool_designer_agent = ToolDesignerAgent()
        
        # Create the tool
        click.echo(f"Creating tool '{tool_spec.get('name')}' (version {version})...")
        if use_llm:
            click.echo("Using LLM for code generation (--use-llm flag enabled).")
            # Note: Currently the LLM is always used in the implementation,
            # but we keep the flag for future flexibility
        
        module_path = await sub_agent_manager.create_tool(
            spec=tool_spec,
            version=version,
            tool_registry=tool_registry,
            tool_designer_agent=tool_designer_agent
        )
        
        if module_path:
            click.echo(click.style(f"\n✓ Tool created successfully!", fg="green", bold=True))
            click.echo(f"Module path: {module_path}")
            click.echo(f"You can import this tool using: from {module_path} import get_tool_instance")
            return module_path
        else:
            click.echo(click.style("\n✗ Tool creation failed.", fg="red", bold=True))
            click.echo("Check the logs for more details on the failure.")
            sys.exit(1)
            
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        click.echo(f"Error parsing specification file: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
        sys.exit(1)

@cli.command(name='tool')
@click.argument('action', type=click.Choice(['create', 'list', 'delete']))
@click.option('--spec-file', type=click.Path(exists=True, dir_okay=False, path_type=Path),
              help='Path to the tool specification file (JSON or YAML).')
@click.option('--use-llm', is_flag=True, default=True,
              help='Use LLM for code generation (default: enabled).')
@click.option('--version', type=str, default="0.1.0",
              help='Version for the created tool (default: 0.1.0).')
def tool_command_wrapper(action, spec_file, use_llm, version):
    """
    Manage tools for the meta-agent.
    
    ACTION can be one of:
    
    \b
    create: Create a new tool from a specification file
    list: List all available tools (not implemented yet)
    delete: Delete a tool (not implemented yet)
    """
    if action == 'create':
        if not spec_file:
            click.echo("Error: --spec-file is required for the 'create' action.", err=True)
            sys.exit(1)
        asyncio.run(create_tool(spec_file, use_llm, version))
    elif action == 'list':
        click.echo("Tool listing is not implemented yet.")
    elif action == 'delete':
        click.echo("Tool deletion is not implemented yet.")

if __name__ == "__main__":
    cli()
