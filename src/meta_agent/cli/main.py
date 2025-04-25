from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

import click
import sys
import yaml
import json
from pathlib import Path
from pydantic import ValidationError

from meta_agent.models.spec_schema import SpecSchema
# TODO: Import logging setup from utils

@click.group()
def cli():
    """Meta-Agent: A tool to generate AI agent code from specifications."""
    # TODO: Configure logging
    pass

@cli.command()
@click.option('--spec-file', type=click.Path(exists=True, dir_okay=False, path_type=Path), 
              help='Path to the specification file (JSON or YAML).')
@click.option('--spec-text', type=str, 
              help='Specification provided as a text string.')
def generate(spec_file: Path | None, spec_text: str | None):
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
            # Placeholder for generation
            click.echo("\n(Agent generation logic goes here)") 
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

if __name__ == '__main__':
    cli()
