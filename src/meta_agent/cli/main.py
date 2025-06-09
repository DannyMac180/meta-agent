try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - fallback when python-dotenv is missing

    def load_dotenv(*_args, **_kwargs) -> None:
        return None


import click
import sys
import yaml
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from pydantic import ValidationError

from meta_agent.models.spec_schema import SpecSchema
from meta_agent.orchestrator import MetaAgentOrchestrator
from meta_agent.planning_engine import PlanningEngine
from meta_agent.sub_agent_manager import SubAgentManager
from meta_agent.registry import ToolRegistry
from meta_agent.tool_designer import ToolDesignerAgent
from meta_agent.telemetry import TelemetryCollector
from meta_agent.telemetry_db import TelemetryDB
from meta_agent.template_registry import TemplateRegistry
from meta_agent.template_search import TemplateSearchEngine
from meta_agent.template_docs_generator import TemplateDocsGenerator
import tempfile

load_dotenv()  # Load environment variables from .env file

# TODO: Import logging setup from utils


@click.group()
@click.option(
    "--no-sensitive-logs",
    is_flag=True,
    help="Exclude sensitive data from traces and telemetry.",
)
@click.pass_context
def cli(ctx: click.Context, no_sensitive_logs: bool) -> None:
    """Meta-Agent: A tool to generate AI agent code from specifications."""
    ctx.ensure_object(dict)
    ctx.obj["include_sensitive"] = not no_sensitive_logs
    # TODO: Configure logging
    pass


@click.option(
    "--spec-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the specification file (JSON or YAML).",
)
@click.option("--spec-text", type=str, help="Specification provided as a text string.")
@click.option(
    "--metric",
    "metrics",
    multiple=True,
    type=click.Choice(["cost", "tokens", "latency", "guardrails"]),
    help="Metric to show in the summary line (repeatable).",
)
async def generate(
    spec_file: Path | None, spec_text: str | None, metrics: tuple[str, ...]
):
    """Generate agent code based on a specification."""
    if not spec_file and not spec_text:
        click.echo("Error: Please provide either --spec-file or --spec-text.", err=True)
        sys.exit(1)
    if spec_file and spec_text:
        click.echo(
            "Error: Please provide only one of --spec-file or --spec-text.", err=True
        )
        sys.exit(1)

    spec: SpecSchema | None = None
    include_sensitive: bool = click.get_current_context().obj.get(
        "include_sensitive", True
    )
    db_path = Path(tempfile.gettempdir()) / "meta_agent_telemetry.db"
    db = TelemetryDB(db_path)
    telemetry = TelemetryCollector(db=db, include_sensitive=include_sensitive)

    try:
        if spec_file:
            click.echo(f"Reading specification from file: {spec_file}")
            if spec_file.suffix.lower() == ".json":
                spec = SpecSchema.from_json(spec_file)
            elif spec_file.suffix.lower() in [".yaml", ".yml"]:
                spec = SpecSchema.from_yaml(spec_file)
            else:
                # TODO: Add support for attempting text parse from unknown file types?
                click.echo(
                    f"Error: Unsupported file type: {spec_file.suffix}. Please use JSON or YAML.",
                    err=True,
                )
                sys.exit(1)

        elif spec_text:
            click.echo("Processing specification from text input...")
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
            spec_dict = (
                spec.model_dump(exclude_unset=True)
                if hasattr(spec, "model_dump")
                else spec.dict(exclude_unset=True)
            )
            telemetry.start_timer()
            results = await orchestrator.run(specification=spec_dict)
            telemetry.stop_timer()
            click.echo("\nOrchestration finished.")
            click.echo(f"Results: {json.dumps(results, indent=2)}")
            click.echo(telemetry.summary_line(list(metrics)))
            db.close()

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
@cli.command(name="generate")
@click.option(
    "--spec-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the specification file (JSON or YAML).",
)
@click.option("--spec-text", type=str, help="Specification provided as a text string.")
@click.option(
    "--metric",
    "metrics",
    multiple=True,
    type=click.Choice(["cost", "tokens", "latency", "guardrails"]),
    help="Metric to show in the summary line (repeatable).",
)
def generate_command_wrapper(spec_file, spec_text, metrics):
    """Synchronous wrapper for the async ``generate`` command."""
    root_logger = logging.getLogger()
    saved_handlers = root_logger.handlers[:]
    root_logger.handlers = []
    try:
        asyncio.run(generate(spec_file, spec_text, metrics))
    finally:
        root_logger.handlers = saved_handlers


async def create_tool(spec_file: Path, use_llm: bool, version: str):
    """Create a tool based on a specification file."""
    click.echo(f"Reading tool specification from file: {spec_file}")

    try:
        # Parse the specification file
        tool_spec = None
        if spec_file.suffix.lower() == ".json":
            with open(spec_file, "r") as f:
                tool_spec = json.load(f)
            click.echo("Parsed tool specification from JSON file.")
        elif spec_file.suffix.lower() in [".yaml", ".yml"]:
            with open(spec_file, "r") as f:
                tool_spec = yaml.safe_load(f)
            click.echo("Parsed tool specification from YAML file.")
        else:
            click.echo(
                f"Error: Unsupported file type: {spec_file.suffix}. Please use JSON or YAML.",
                err=True,
            )
            sys.exit(1)

        if not tool_spec:
            click.echo("Error: Empty or invalid tool specification.", err=True)
            sys.exit(1)

        # Validate basic structure
        if not isinstance(tool_spec, dict):
            click.echo(
                "Error: Tool specification must be a dictionary/object.", err=True
            )
            sys.exit(1)

        if "name" not in tool_spec:
            click.echo(
                "Error: Tool specification must include a 'name' field.", err=True
            )
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
            tool_designer_agent=tool_designer_agent,
        )

        if module_path:
            click.echo(
                click.style("\n✓ Tool created successfully!", fg="green", bold=True)
            )
            click.echo(f"Module path: {module_path}")
            click.echo(
                f"You can import this tool using: from {module_path} import get_tool_instance"
            )
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


@cli.command(name="tool")
@click.argument("action", type=click.Choice(["create", "list", "delete"]))
@click.option(
    "--spec-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the tool specification file (JSON or YAML).",
)
@click.option(
    "--use-llm",
    is_flag=True,
    default=True,
    help="Use LLM for code generation (default: enabled).",
)
@click.option(
    "--version",
    type=str,
    default="0.1.0",
    help="Version for the created tool (default: 0.1.0).",
)
def tool_command_wrapper(action, spec_file, use_llm, version):
    """
    Manage tools for the meta-agent.

    ACTION can be one of:

    \b
    create: Create a new tool from a specification file
    list: List all available tools (not implemented yet)
    delete: Delete a tool (not implemented yet)
    """
    if action == "create":
        if not spec_file:
            click.echo(
                "Error: --spec-file is required for the 'create' action.", err=True
            )
            sys.exit(1)
        asyncio.run(create_tool(spec_file, use_llm, version))
    elif action == "list":
        click.echo("Tool listing is not implemented yet.")
    elif action == "delete":
        click.echo("Tool deletion is not implemented yet.")


@cli.command(name="dashboard")
@click.option(
    "--db-path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path(tempfile.gettempdir()) / "meta_agent_telemetry.db",
    show_default=True,
    help="Path to the telemetry database file.",
)
def dashboard(db_path: Path) -> None:
    """Display a simple telemetry dashboard."""
    db = TelemetryDB(db_path)
    records = db.fetch_all()
    if not records:
        click.echo("No telemetry data found.")
        db.close()
        return

    click.echo("Telemetry Dashboard:")
    header = (
        f"{'Timestamp':<20} {'Tokens':>6} {'Cost':>7} {'Latency':>8} {'Guardrails':>10}"
    )
    click.echo(header)
    for row in records:
        ts = row["timestamp"][:19]
        line = (
            f"{ts:<20} "
            f"{row['tokens']:>6} "
            f"${row['cost']:.2f} "
            f"{row['latency']:>8.2f} "
            f"{row['guardrail_hits']:>10}"
        )
    click.echo(line)
    db.close()


@cli.command(name="export")
@click.option(
    "--db-path",
    type=click.Path(dir_okay=False, path_type=Path),
    default=Path(tempfile.gettempdir()) / "meta_agent_telemetry.db",
    show_default=True,
    help="Path to the telemetry database file.",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "csv", "pdf"]),
    default="json",
    show_default=True,
    help="Export format",
)
@click.option(
    "--output", "output_path", type=click.Path(dir_okay=False, path_type=Path)
)
@click.option("--start", type=str, help="Start timestamp (ISO format)")
@click.option("--end", type=str, help="End timestamp (ISO format)")
@click.option("--metric", "metrics", multiple=True, help="Metric to include")
def export_command(
    db_path: Path,
    fmt: str,
    output_path: Path | None,
    start: str | None,
    end: str | None,
    metrics: tuple[str, ...],
) -> None:
    """Export telemetry data from the database."""
    db = TelemetryDB(db_path)
    if output_path is None:
        suffix = "json" if fmt == "json" else "csv" if fmt == "csv" else fmt
        output_path = Path(f"telemetry_export.{suffix}")
    if fmt == "json":
        db.export_json(output_path, start=start, end=end, metrics=metrics or None)
    elif fmt == "csv":
        db.export_csv(output_path, start=start, end=end, metrics=metrics or None)
    else:
        db.export(output_path, fmt=fmt, start=start, end=end, metrics=metrics or None)
    click.echo(f"Exported telemetry to {output_path}")
    db.close()


async def init_project(
    project_name: str, template_slug: str | None = None, directory: Path | None = None
):
    """Initialize a new meta-agent project, optionally from a template."""
    if not directory:
        directory = Path.cwd() / project_name

    # Create project directory
    directory.mkdir(parents=True, exist_ok=True)
    click.echo(f"Initializing project '{project_name}' in {directory}")

    # Basic project structure
    config_dir = directory / ".meta-agent"
    config_dir.mkdir(exist_ok=True)

    if template_slug:
        # Use template
        registry = TemplateRegistry()
        template_content = registry.load_template(template_slug)

        if template_content:
            click.echo(f"Using template: {template_slug}")
            # Create project files from template
            spec_file = directory / "agent_spec.yaml"
            spec_file.write_text(template_content, encoding="utf-8")
            click.echo(f"Created specification file: {spec_file}")
        else:
            # If template not found, show available templates
            click.echo(f"Template '{template_slug}' not found.", err=True)
            click.echo("Available templates:")
            search_engine = TemplateSearchEngine(registry)
            search_engine.build_index()
            templates = registry.list_templates()
            for template in templates:
                click.echo(f"  - {template['slug']} (v{template['current_version']})")
            return
    else:
        # Create basic template
        basic_spec = """# Agent Specification
task_description: "Describe what your agent should do"
inputs:
  - name: "input_data"
    description: "Input description"
outputs:
  - name: "result"
    description: "Output description"
model_preference: "gpt-4"
"""
        spec_file = directory / "agent_spec.yaml"
        spec_file.write_text(basic_spec, encoding="utf-8")
        click.echo(f"Created basic specification file: {spec_file}")

    # Create basic config
    config_file = config_dir / "config.yaml"
    config_content = f"""project_name: "{project_name}"
version: "0.1.0"
created_at: "{datetime.utcnow().isoformat()}"
"""
    config_file.write_text(config_content, encoding="utf-8")
    click.echo(f"Created config file: {config_file}")

    click.echo(
        click.style("\n✓ Project initialized successfully!", fg="green", bold=True)
    )
    click.echo("Next steps:")
    click.echo(f"  1. Edit {spec_file} to define your agent")
    click.echo(
        f"  2. Run 'meta-agent generate --spec-file {spec_file}' to create your agent"
    )


@cli.command(name="init")
@click.argument("project_name")
@click.option(
    "--template",
    type=str,
    help="Template slug to use for initialization (e.g., 'hello-world')",
)
@click.option(
    "--directory",
    type=click.Path(path_type=Path),
    help="Directory to create project in (default: current directory + project name)",
)
def init_command_wrapper(
    project_name: str, template: str | None, directory: Path | None
):
    """Initialize a new meta-agent project."""
    asyncio.run(init_project(project_name, template, directory))


@cli.command(name="templates")
@click.argument("action", type=click.Choice(["docs", "list", "search"]))
@click.option(
    "--output-dir",
    type=click.Path(path_type=Path),
    default="docs/templates",
    help="Output directory for generated documentation (default: docs/templates)",
)
@click.option(
    "--template",
    type=str,
    help="Specific template slug to generate docs for (default: all templates)",
)
@click.option(
    "--no-samples",
    is_flag=True,
    help="Exclude sample usage from generated documentation",
)
def templates_command(
    action: str, output_dir: Path, template: str | None, no_samples: bool
):
    """
    Manage and document templates.

    ACTION can be one of:

    \b
    docs: Generate documentation for templates
    list: List all available templates
    search: Search for templates (not implemented yet)
    """
    if action == "docs":
        click.echo("Generating template documentation...")

        registry = TemplateRegistry()
        generator = TemplateDocsGenerator(registry=registry)

        try:
            if template:
                # Generate docs for specific template
                templates = registry.list_templates()
                template_info = next(
                    (t for t in templates if t["slug"] == template), None
                )

                if not template_info:
                    click.echo(f"Error: Template '{template}' not found.", err=True)
                    sys.exit(1)

                current_version = template_info["current_version"]
                if not current_version:
                    click.echo(
                        f"Error: No current version found for template '{template}'.",
                        err=True,
                    )
                    sys.exit(1)

                metadata = generator._load_template_metadata(template, current_version)
                if not metadata:
                    click.echo(
                        f"Error: Could not load metadata for template '{template}'.",
                        err=True,
                    )
                    sys.exit(1)

                # Generate sample usage if requested
                sample_usage = (
                    None if no_samples else generator._generate_sample_usage(metadata)
                )

                # Generate card
                card_content = generator.generate_card(metadata, sample_usage)

                # Save to file
                output_dir.mkdir(parents=True, exist_ok=True)
                filename = f"{template.replace('_', '-')}.md"
                file_path = output_dir / filename
                file_path.write_text(card_content, encoding="utf-8")

                click.echo(
                    click.style(
                        "✓ Documentation generated successfully!", fg="green", bold=True
                    )
                )
                click.echo(f"File: {file_path}")

            else:
                # Generate docs for all templates
                include_samples = not no_samples
                generated_files = generator.generate_all_cards(
                    output_dir, include_sample=include_samples
                )

                if generated_files:
                    # Generate index file
                    index_path = generator.generate_index(output_dir)

                    click.echo(
                        click.style(
                            "✓ Documentation generated successfully!",
                            fg="green",
                            bold=True,
                        )
                    )
                    click.echo(
                        f"Generated {len(generated_files)} template documentation files"
                    )
                    click.echo(f"Index file: {index_path}")
                    click.echo(f"Documentation directory: {output_dir}")
                else:
                    click.echo("No templates found to document.", err=True)

        except Exception as e:
            click.echo(f"Error generating documentation: {e}", err=True)
            sys.exit(1)

    elif action == "list":
        click.echo("Available templates:")
        registry = TemplateRegistry()
        templates = registry.list_templates()

        if not templates:
            click.echo("No templates found.")
            return

        for template_info in templates:
            slug = template_info["slug"]
            version = template_info["current_version"] or "unknown"
            click.echo(f"  - {slug} (v{version})")

    elif action == "search":
        click.echo("Template search is not implemented yet.")


@cli.command(name="serve")
@click.option(
    "--host",
    type=str,
    default="127.0.0.1",
    help="Host to bind the server to (default: 127.0.0.1)",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port to bind the server to (default: 8000)",
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
def serve_command(host: str, port: int, reload: bool):
    """Start the REST API server for template management."""
    try:
        import uvicorn
        from meta_agent.api import app

        if app is None:
            click.echo(
                "Error: FastAPI and uvicorn are required to run the API server.",
                err=True,
            )
            click.echo("Install with: pip install fastapi uvicorn", err=True)
            sys.exit(1)

        click.echo(f"Starting API server on http://{host}:{port}")
        click.echo("API documentation available at: http://{host}:{port}/docs")

        uvicorn.run("meta_agent.api:app", host=host, port=port, reload=reload)

    except ImportError as e:
        click.echo(f"Error: Missing dependency for API server: {e}", err=True)
        click.echo("Install with: pip install fastapi uvicorn", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
