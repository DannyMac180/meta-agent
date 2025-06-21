from typing import Any

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - fallback when python-dotenv is missing

    def load_dotenv(*_args: Any, **_kwargs: Any) -> bool:  # pragma: no cover
        """Stub replacement when `python‑dotenv` isn't installed."""
        return False


import click
import sys
import yaml
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from pydantic import ValidationError

from meta_agent.utils.logging import setup_logging
# Other imports deferred to avoid circular dependencies and OpenAI SDK issues
import tempfile

# Template imports - placed here so tests can patch them
try:
    from meta_agent.template_registry import TemplateRegistry
    from meta_agent.template_search import TemplateSearchEngine
except ImportError:
    # Handle missing template dependencies gracefully
    TemplateRegistry = None
    TemplateSearchEngine = None

# Import potential network/API exceptions with fallbacks
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True  
    NETWORK_EXCEPTIONS = (aiohttp.ClientError, asyncio.TimeoutError)
except ImportError:
    AIOHTTP_AVAILABLE = False
    NETWORK_EXCEPTIONS = (asyncio.TimeoutError,)

# Handle OpenAI SDK imports - defer to avoid module-level compatibility issues
OPENAI_AVAILABLE = False  
OPENAI_EXCEPTIONS = ()

load_dotenv()  # Load environment variables from .env file

# Configure logging at module level
logger = setup_logging("meta_agent.cli", level="INFO")


def _sanitize_error_message(error: Exception, include_sensitive: bool) -> str:
    """Sanitize error messages based on privacy settings."""
    error_str = str(error)
    
    if not include_sensitive:
        # Remove potentially sensitive patterns
        import re
        # Remove file paths
        error_str = re.sub(r'/[^\s]*', '[PATH]', error_str)
        # Remove API keys or tokens
        error_str = re.sub(r'[a-zA-Z0-9]{20,}', '[TOKEN]', error_str)
        # Remove URLs
        error_str = re.sub(r'https?://[^\s]+', '[URL]', error_str)
    
    return error_str


def _get_helpful_error_message(error: Exception, context: str = "") -> str:
    """Generate helpful error messages with actionable suggestions."""
    error_msg = str(error).lower()
    
    if "api key" in error_msg or "authentication" in error_msg:
        return (
            f"Authentication failed: {error}\n"
            "💡 Check your API key configuration:\n"
            "   • Set OPENAI_API_KEY environment variable\n"
            "   • Verify the key is valid and has sufficient credits"
        )
    
    if "network" in error_msg or "connection" in error_msg or "timeout" in error_msg:
        return (
            f"Network error: {error}\n"
            "💡 Try these solutions:\n"
            "   • Check your internet connection\n"
            "   • Verify firewall settings\n"
            "   • Try again in a few moments"
        )
    
    if "rate limit" in error_msg or "quota" in error_msg:
        return (
            f"Rate limit exceeded: {error}\n"
            "💡 Rate limiting solutions:\n"
            "   • Wait a few minutes before retrying\n"
            "   • Check your API usage limits\n"
            "   • Consider upgrading your API plan"
        )
    
    if "validation" in error_msg or "invalid" in error_msg:
        if context == "specification":
            return (
                f"Specification validation failed: {error}\n"
                "💡 Specification fixes:\n"
                "   • Ensure task_description is not empty\n"
                "   • Check JSON/YAML syntax\n"
                "   • Verify required fields are present"
            )
    
    if "file not found" in error_msg or "no such file" in error_msg:
        return (
            f"File not found: {error}\n"
            "💡 File access solutions:\n"
            "   • Check the file path is correct\n"
            "   • Verify file permissions\n"
            "   • Ensure the file exists"
        )
    
    return str(error)


async def _retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0):
    """Retry function with exponential backoff for transient failures."""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            
            # Only retry on network/transient errors
            is_retryable = (
                isinstance(e, NETWORK_EXCEPTIONS) or
                isinstance(e, OPENAI_EXCEPTIONS) or
                "timeout" in str(e).lower() or
                "rate limit" in str(e).lower()
            )
            
            if not is_retryable or attempt == max_retries - 1:
                raise e
            
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)
    
    if last_exception:
        raise last_exception


@click.group()
@click.option(
    "--no-sensitive-logs",
    is_flag=True,
    help="Exclude sensitive data from traces and telemetry.",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging.",
)
@click.pass_context
def cli(ctx: click.Context, no_sensitive_logs: bool, debug: bool) -> None:
    """Meta-Agent: Generate AI agent code from natural language descriptions."""
    ctx.ensure_object(dict)
    ctx.obj["include_sensitive"] = not no_sensitive_logs
    ctx.obj["debug"] = debug
    
    # Configure logging based on debug flag
    log_level = "DEBUG" if debug else "INFO"
    global logger
    logger = setup_logging("meta_agent.cli", level=log_level)
    
    if debug:
        logger.debug("Debug logging enabled")


@click.option(
    "--spec-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the specification file (JSON or YAML).",
)
@click.option("--spec-text", type=str, help="Natural language specification describing your agent (e.g., 'Create a calculator that adds numbers').")
@click.option(
    "--metric",
    "metrics",
    multiple=True,
    type=click.Choice(["cost", "tokens", "latency", "guardrails"]),
    help="Metric to show in the summary line (repeatable).",
)
async def create_agent(
    spec_file: Path | None, spec_text: str | None, metrics: tuple[str, ...], show_spec: bool
):
    """Create agent code from natural language specifications."""
    ctx = click.get_current_context()
    include_sensitive = ctx.obj.get("include_sensitive", True)
    debug = ctx.obj.get("debug", False)
    
    if debug:
        logger.debug(f"Starting create_agent with spec_file={spec_file}, spec_text={'[REDACTED]' if not include_sensitive and spec_text else bool(spec_text)}")
    
    # Handle missing specification with enhanced prompting
    if not spec_file and not spec_text:
        is_interactive = sys.stdin.isatty() and not (hasattr(ctx, 'resilient_parsing') and ctx.resilient_parsing)
        
        if not is_interactive:
            click.echo(
                "❌ No specification provided.\n"
                "\n"
                "In non-interactive environments, you must specify the agent specification:\n"
                "  • Use --spec-file path/to/spec.yaml\n"
                "  • Use --spec-text 'your specification here'\n"
                "\n"
                "Example: meta-agent create --spec-text 'Analyze customer feedback sentiment'",
                err=True
            )
            sys.exit(1)
        
        # Enhanced interactive prompting
        try:
            click.echo("🤖 Let's create your agent interactively!")
            click.echo()
            click.echo("Describe what you want your agent to do:")
            click.echo("  • Task: What should the agent perform?")
            click.echo("  • Inputs: What data will it receive?")
            click.echo("  • Outputs: What should it produce?")
            click.echo()
            click.echo("Example: 'Analyze customer feedback and categorize by sentiment'")
            click.echo()
            
            initial_text = """# Describe your agent here
# What should your agent do?

# What inputs will it need?

# What outputs should it produce?

# Any specific requirements?
"""
            
            user_input = click.edit(initial_text, extension='.txt')
            if not user_input or not user_input.strip():
                click.echo("❌ No specification provided. Agent creation cancelled.", err=True)
                sys.exit(1)
            
            # Remove template comments and validate content
            lines = [line for line in user_input.split('\n') if not line.strip().startswith('#')]
            cleaned_input = '\n'.join(lines).strip()
            
            if not cleaned_input:
                click.echo("❌ No specification content provided. Agent creation cancelled.", err=True)
                sys.exit(1)
            
            spec_text = user_input.strip()
            click.echo("✓ Specification received. Processing...")
            
        except click.ClickException:
            click.echo("Agent creation cancelled.", err=True)
            sys.exit(1)
        except Exception as e:
            sanitized_error = _sanitize_error_message(e, include_sensitive)
            click.echo(f"❌ Failed to get specification input: {sanitized_error}", err=True)
            sys.exit(1)
    
    if spec_file and spec_text:
        click.echo("❌ Provide only one of --spec-file or --spec-text.", err=True)
        sys.exit(1)

    # Import required modules here to avoid module-level import issues
    from meta_agent.models.spec_schema import SpecSchema
    from meta_agent.telemetry import TelemetryCollector
    from meta_agent.telemetry_db import TelemetryDB
    
    # Initialize telemetry with error handling
    spec: SpecSchema | None = None
    telemetry = None
    db = None
    
    try:
        db_path = Path(tempfile.gettempdir()) / "meta_agent_telemetry.db"
        db = TelemetryDB(db_path)
        telemetry = TelemetryCollector(db=db, include_sensitive=include_sensitive)
        logger.debug("Telemetry initialized successfully")
    except Exception as e:
        logger.warning(f"Telemetry initialization failed: {e}. Continuing without telemetry.")
        telemetry = None
        db = None

    try:
        # Parse specification with enhanced error handling
        if spec_file:
            click.echo(f"📄 Reading specification from {spec_file.name}")
            logger.debug(f"Parsing spec file: {spec_file}")
            
            try:
                if spec_file.suffix.lower() == ".json":
                    spec = SpecSchema.from_json(spec_file)
                elif spec_file.suffix.lower() in [".yaml", ".yml"]:
                    spec = SpecSchema.from_yaml(spec_file)
                else:
                    click.echo(
                        f"❌ Unsupported file type: {spec_file.suffix}\n"
                        "💡 Supported formats: .json, .yaml, .yml",
                        err=True,
                    )
                    sys.exit(1)
            except FileNotFoundError:
                click.echo(f"❌ File not found: {spec_file}", err=True)
                sys.exit(1)
            except (json.JSONDecodeError, yaml.YAMLError) as e:
                click.echo(
                    f"❌ Failed to parse {spec_file.suffix.upper()} file: {e}\n"
                    "💡 Check your file syntax and format",
                    err=True
                )
                sys.exit(1)

        elif spec_text:
            click.echo("📝 Processing specification from text...")
            logger.debug("Parsing spec text")
            
            try:
                # Try structured formats first
                try:
                    data = json.loads(spec_text)
                    spec = SpecSchema.from_dict(data)
                    logger.debug("Parsed as JSON")
                except json.JSONDecodeError:
                    try:
                        data = yaml.safe_load(spec_text)
                        if isinstance(data, dict):
                            spec = SpecSchema.from_dict(data)
                            logger.debug("Parsed as YAML")
                        else:
                            raise yaml.YAMLError("Not a dictionary")
                    except yaml.YAMLError:
                        # Fallback to natural language parsing
                        logger.debug("Parsing as natural language")
                        spec = SpecSchema.from_text(spec_text)
                        
            except ValidationError as e:
                helpful_msg = _get_helpful_error_message(e, "specification")
                click.echo(f"❌ {helpful_msg}", err=True)
                sys.exit(1)

        if not spec:
            click.echo("❌ Could not parse specification.", err=True)
            sys.exit(1)

        # Display parsed specification
        click.echo("✅ Specification parsed successfully:")
        task_preview = spec.task_description[:100] + "..." if len(spec.task_description) > 100 else spec.task_description
        click.echo(f"   Task: {task_preview}")
        if spec.inputs:
            click.echo(f"   Inputs: {list(spec.inputs.keys()) if isinstance(spec.inputs, dict) else spec.inputs}")
        if spec.outputs:
            click.echo(f"   Outputs: {list(spec.outputs.keys()) if isinstance(spec.outputs, dict) else spec.outputs}")
        
        # Show specification YAML if requested
        if show_spec:
            click.echo("\n📋 Generated Specification:")
            click.echo("─" * 50)
            spec_dict = spec.model_dump(exclude_unset=True) if hasattr(spec, "model_dump") else spec.dict(exclude_unset=True)
            formatted_yaml = yaml.dump(spec_dict, default_flow_style=False, sort_keys=False, indent=2)
            click.echo(formatted_yaml.strip())
            click.echo("─" * 50)

        # Initialize components with error handling
        click.echo("\n🔧 Initializing components...")
        try:
            from meta_agent.orchestrator import MetaAgentOrchestrator
            from meta_agent.planning_engine import PlanningEngine
            from meta_agent.sub_agent_manager import SubAgentManager
            from meta_agent.registry import ToolRegistry
            from meta_agent.tool_designer import ToolDesignerAgent
            
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
            logger.debug("Components initialized successfully")
            
        except Exception as e:
            sanitized_error = _sanitize_error_message(e, include_sensitive)
            click.echo(f"❌ Failed to initialize components: {sanitized_error}", err=True)
            
            # Provide specific guidance for common component failures
            if "api key" in str(e).lower():
                click.echo("💡 Set your OPENAI_API_KEY environment variable", err=True)
            elif "connection" in str(e).lower():
                click.echo("💡 Check your network connection and API access", err=True)
            
            sys.exit(1)

        # Run orchestration with retry logic and enhanced error handling
        click.echo("\n🚀 Starting agent generation...")
        
        if telemetry:
            telemetry.start_timer()
        
        async def run_orchestration():
            return await orchestrator.run(specification=spec)
        
        try:
            # Use retry logic for orchestration
            results = await _retry_with_backoff(run_orchestration, max_retries=3)
            
            if telemetry:
                telemetry.stop_timer()
            
            click.echo("\n✅ Agent generation completed successfully!")
            click.echo(f"📊 Results: {json.dumps(results, indent=2)}")
            
            if telemetry and metrics:
                click.echo(f"📈 {telemetry.summary_line(list(metrics))}")
                
        except Exception as e:
            # Check if it's a CodeGenerationError
            if "CodeGenerationError" in str(type(e)):
                sanitized_error = _sanitize_error_message(e, include_sensitive)
                click.echo(f"❌ Code generation failed: {sanitized_error}", err=True)
                click.echo("💡 Try simplifying your specification or check the logs for details", err=True)
                sys.exit(1)
            # Check for OpenAI specific errors
            elif any(exc_name in str(type(e)) for exc_name in ["AuthenticationError", "APIConnectionError", "APITimeoutError"]):
                helpful_msg = _get_helpful_error_message(e)
                click.echo(f"❌ {helpful_msg}", err=True)
                sys.exit(1)
            # Check for network errors  
            elif any(exc_name in str(type(e)) for exc_name in ["ClientError", "TimeoutError"]) or "timeout" in str(e).lower():
                helpful_msg = _get_helpful_error_message(e)
                click.echo(f"❌ {helpful_msg}", err=True)
                sys.exit(1)
            sanitized_error = _sanitize_error_message(e, include_sensitive)
            logger.exception("Unexpected error during orchestration")
            click.echo(f"❌ Unexpected error during agent generation: {sanitized_error}", err=True)
            
            if debug:
                import traceback
                click.echo(f"Debug traceback:\n{traceback.format_exc()}", err=True)
            else:
                click.echo("💡 Run with --debug for detailed error information", err=True)
            
            sys.exit(1)

    except KeyboardInterrupt:
        click.echo("\n⚠️  Agent generation interrupted by user", err=True)
        sys.exit(1)
        
    except Exception as e:
        sanitized_error = _sanitize_error_message(e, include_sensitive)
        logger.exception("Unexpected error in create_agent")
        click.echo(f"❌ Unexpected error: {sanitized_error}", err=True)
        
        if debug:
            import traceback
            click.echo(f"Debug traceback:\n{traceback.format_exc()}", err=True)
        else:
            click.echo("💡 Run with --debug for detailed error information", err=True)
        
        sys.exit(1)
        
    finally:
        # Cleanup resources
        if db:
            try:
                db.close()
            except Exception as e:
                logger.warning(f"Error closing database: {e}")


async def generate(
    spec_file: Path | None, spec_text: str | None, metrics: tuple[str, ...]
):
    """Generate agent code based on a specification. (DEPRECATED: Use 'create' command instead)"""
    # Maintain old behavior for deprecated generate command
    if not spec_file and not spec_text:
        click.echo("❌ Please provide either --spec-file or --spec-text.", err=True)
        sys.exit(1)
    if spec_file and spec_text:
        click.echo("❌ Please provide only one of --spec-file or --spec-text.", err=True)
        sys.exit(1)
    
    return await create_agent(spec_file, spec_text, metrics, show_spec=False)


# Note: This basic setup works for a single async command.
# If more async commands are added, a more robust asyncio setup might be needed.
@cli.command(name="generate")
@click.option(
    "--spec-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the specification file (JSON or YAML).",
)
@click.option("--spec-text", type=str, help="Natural language specification describing your agent.")
@click.option(
    "--metric",
    "metrics",
    multiple=True,
    type=click.Choice(["cost", "tokens", "latency", "guardrails"]),
    help="Metric to show in the summary line (repeatable).",
)
def generate_command_wrapper(spec_file, spec_text, metrics):
    """Generate agent code based on a specification. (DEPRECATED: Use 'create' command instead)"""
    root_logger = logging.getLogger()
    saved_handlers = root_logger.handlers[:]
    root_logger.handlers = []
    try:
        asyncio.run(generate(spec_file, spec_text, metrics))
    except KeyboardInterrupt:
        click.echo("\n⚠️  Generation interrupted by user", err=True)
        sys.exit(1)
    finally:
        root_logger.handlers = saved_handlers


@cli.command(name="create")
@click.option(
    "--spec-file",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Path to the specification file (JSON or YAML).",
)
@click.option("--spec-text", type=str, help="Natural language specification describing your agent.")
@click.option(
    "--metric",
    "metrics",
    multiple=True,
    type=click.Choice(["cost", "tokens", "latency", "guardrails"]),
    help="Metric to show in the summary line (repeatable).",
)
@click.option(
    "--show-spec",
    is_flag=True,
    help="Display the generated specification YAML before creating the agent.",
)
def create_command_wrapper(spec_file, spec_text, metrics, show_spec):
    """Create agent code from natural language specifications. (Primary command for agent creation)"""
    root_logger = logging.getLogger()
    saved_handlers = root_logger.handlers[:]
    root_logger.handlers = []
    try:
        asyncio.run(create_agent(spec_file, spec_text, metrics, show_spec))
    except KeyboardInterrupt:
        click.echo("\n⚠️  Agent creation interrupted by user", err=True)
        sys.exit(1)
    finally:
        root_logger.handlers = saved_handlers


async def create_tool(spec_file: Path, use_llm: bool, version: str):
    """Create a tool based on a specification file."""
    ctx = click.get_current_context()
    include_sensitive = ctx.obj.get("include_sensitive", True)
    debug = ctx.obj.get("debug", False)
    
    click.echo(f"📄 Reading tool specification from {spec_file.name}")

    try:
        # Parse specification with enhanced error handling
        tool_spec = None
        if spec_file.suffix.lower() == ".json":
            with open(spec_file, "r") as f:
                tool_spec = json.load(f)
            click.echo("✓ Parsed JSON specification")
        elif spec_file.suffix.lower() in [".yaml", ".yml"]:
            with open(spec_file, "r") as f:
                tool_spec = yaml.safe_load(f)
            click.echo("✓ Parsed YAML specification")
        else:
            click.echo(
                f"❌ Unsupported file type: {spec_file.suffix}\n"
                "💡 Supported formats: .json, .yaml, .yml",
                err=True,
            )
            sys.exit(1)

        if not tool_spec:
            click.echo(
                "❌ Empty or invalid tool specification\n"
                "💡 Ensure your file contains valid specification data",
                err=True
            )
            sys.exit(1)

        # Enhanced validation
        if not isinstance(tool_spec, dict):
            click.echo(
                "❌ Tool specification must be a dictionary/object\n"
                "💡 Check your JSON/YAML structure",
                err=True
            )
            sys.exit(1)

        if "name" not in tool_spec:
            click.echo(
                "❌ Tool specification must include a 'name' field\n"
                "💡 Add a 'name' field to your specification",
                err=True
            )
            sys.exit(1)

        # Initialize components with error handling
        click.echo("🔧 Initializing components...")
        try:
            from meta_agent.sub_agent_manager import SubAgentManager
            from meta_agent.registry import ToolRegistry
            from meta_agent.tool_designer import ToolDesignerAgent
            
            sub_agent_manager = SubAgentManager()
            tool_registry = ToolRegistry()
            tool_designer_agent = ToolDesignerAgent()
        except Exception as e:
            sanitized_error = _sanitize_error_message(e, include_sensitive)
            click.echo(f"❌ Failed to initialize components: {sanitized_error}", err=True)
            sys.exit(1)

        # Create tool with retry logic
        tool_name = tool_spec.get('name', 'unknown')
        click.echo(f"🛠️  Creating tool '{tool_name}' (v{version})...")
        
        if use_llm:
            click.echo("🤖 Using LLM for code generation")

        async def create_tool_with_retry():
            return await sub_agent_manager.create_tool(
                spec=tool_spec,
                version=version,
                tool_registry=tool_registry,
                tool_designer_agent=tool_designer_agent,
            )

        try:
            module_path = await _retry_with_backoff(create_tool_with_retry, max_retries=2)
            
            if module_path:
                click.echo(click.style("\n✅ Tool created successfully!", fg="green", bold=True))
                click.echo(f"📦 Module path: {module_path}")
                click.echo(f"💡 Import with: from {module_path} import get_tool_instance")
                return module_path
            else:
                click.echo(click.style("\n❌ Tool creation failed", fg="red", bold=True))
                click.echo("💡 Check the logs for more details")
                sys.exit(1)
                
        except Exception as e:
            # Check if it's a CodeGenerationError
            if "CodeGenerationError" in str(type(e)):
                sanitized_error = _sanitize_error_message(e, include_sensitive)
                click.echo(f"❌ Code generation failed: {sanitized_error}", err=True)
                click.echo("💡 Try simplifying your tool specification", err=True)
                sys.exit(1)
            # Check for OpenAI specific errors
            elif any(exc_name in str(type(e)) for exc_name in ["AuthenticationError", "APIConnectionError", "APITimeoutError"]):
                helpful_msg = _get_helpful_error_message(e)
                click.echo(f"❌ {helpful_msg}", err=True)
                sys.exit(1)
            sanitized_error = _sanitize_error_message(e, include_sensitive)
            logger.exception("Unexpected error during tool creation")
            click.echo(f"❌ Unexpected error: {sanitized_error}", err=True)
            
            if debug:
                import traceback
                click.echo(f"Debug traceback:\n{traceback.format_exc()}", err=True)
            else:
                click.echo("💡 Run with --debug for detailed error information", err=True)
            
            sys.exit(1)

    except FileNotFoundError as e:
        click.echo(f"❌ File not found: {e}", err=True)
        sys.exit(1)
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        click.echo(f"❌ Error parsing specification file: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n⚠️  Tool creation interrupted by user", err=True)
        sys.exit(1)
    except Exception as e:
        sanitized_error = _sanitize_error_message(e, include_sensitive)
        logger.exception("Unexpected error in create_tool")
        click.echo(f"❌ Unexpected error: {sanitized_error}", err=True)
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
    try:
        if action == "create":
            if not spec_file:
                click.echo(
                    "❌ --spec-file is required for the 'create' action\n"
                    "💡 Example: meta-agent tool create --spec-file my_tool.yaml",
                    err=True
                )
                sys.exit(1)
            asyncio.run(create_tool(spec_file, use_llm, version))
        elif action == "list":
            click.echo("📋 Tool listing is not implemented yet.")
        elif action == "delete":
            click.echo("🗑️  Tool deletion is not implemented yet.")
    except KeyboardInterrupt:
        click.echo(f"\n⚠️  {action.title()} operation interrupted by user", err=True)
        sys.exit(1)


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
    try:
        from meta_agent.telemetry_db import TelemetryDB, TelemetryRow
        
        db = TelemetryDB(db_path)
        records: list[TelemetryRow] = db.fetch_all()
        if not records:
            click.echo("📊 No telemetry data found.")
            db.close()
            return

        click.echo("📊 Telemetry Dashboard:")
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
    except Exception as e:
        click.echo(f"❌ Error accessing telemetry database: {e}", err=True)
        sys.exit(1)


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
    try:
        from meta_agent.telemetry_db import TelemetryDB
        
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
        
        click.echo(f"✅ Exported telemetry to {output_path}")
        db.close()
    except Exception as e:
        click.echo(f"❌ Export failed: {e}", err=True)
        sys.exit(1)


async def init_project(
    project_name: str, template_slug: str | None = None, directory: Path | None = None
):
    """Initialize a new meta-agent project, optionally from a template."""
    if not directory:
        directory = Path.cwd() / project_name

    try:
        # Create project directory
        directory.mkdir(parents=True, exist_ok=True)
        click.echo(f"📁 Initializing project '{project_name}' in {directory}")

        # Basic project structure
        config_dir = directory / ".meta-agent"
        config_dir.mkdir(exist_ok=True)

        if template_slug:
            # Use template with error handling
            try:
                if TemplateRegistry is None or TemplateSearchEngine is None:
                    click.echo("❌ Template functionality not available", err=True)
                    sys.exit(1)
                
                registry = TemplateRegistry()
                template_content = registry.load_template(template_slug)

                if template_content:
                    click.echo(f"📋 Using template: {template_slug}")
                    spec_file = directory / "agent_spec.yaml"
                    spec_file.write_text(template_content, encoding="utf-8")
                    click.echo(f"✓ Created specification file: {spec_file}")
                else:
                    click.echo(f"❌ Template '{template_slug}' not found.", err=True)
                    click.echo("Available templates:")
                    search_engine = TemplateSearchEngine(registry)
                    search_engine.build_index()
                    templates = registry.list_templates()
                    for template in templates:
                        click.echo(f"  - {template['slug']} (v{template['current_version']})")
                    return
            except Exception as e:
                click.echo(f"❌ Error loading template: {e}", err=True)
                sys.exit(1)
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
            click.echo(f"✓ Created basic specification file: {spec_file}")

        # Create basic config
        config_file = config_dir / "config.yaml"
        config_content = f"""project_name: "{project_name}"
version: "0.1.0"
created_at: "{datetime.utcnow().isoformat()}"
"""
        config_file.write_text(config_content, encoding="utf-8")
        click.echo(f"✓ Created config file: {config_file}")

        click.echo(click.style("\n✅ Project initialized successfully!", fg="green", bold=True))
        click.echo("Next steps:")
        click.echo(f"  1. Edit {spec_file} to define your agent")
        click.echo(f"  2. Run 'meta-agent create --spec-file {spec_file}' to create your agent")
        
    except PermissionError as e:
        click.echo(f"❌ Permission denied: {e}", err=True)
        click.echo("💡 Check directory permissions or try a different location", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Project initialization failed: {e}", err=True)
        sys.exit(1)


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
    try:
        asyncio.run(init_project(project_name, template, directory))
    except KeyboardInterrupt:
        click.echo("\n⚠️  Project initialization interrupted by user", err=True)
        sys.exit(1)


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
        click.echo("📚 Generating template documentation...")
        
        if TemplateRegistry is None:
            click.echo("❌ Template functionality not available", err=True)
            sys.exit(1)
            
        from meta_agent.template_docs_generator import TemplateDocsGenerator

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
                    click.echo(f"❌ Template '{template}' not found.", err=True)
                    sys.exit(1)

                current_version = template_info["current_version"]
                if not current_version:
                    click.echo(
                        f"❌ No current version found for template '{template}'.",
                        err=True,
                    )
                    sys.exit(1)

                metadata = generator._load_template_metadata(template, current_version)
                if not metadata:
                    click.echo(
                        f"❌ Could not load metadata for template '{template}'.",
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

                click.echo(click.style("✅ Documentation generated successfully!", fg="green", bold=True))
                click.echo(f"📄 File: {file_path}")

            else:
                # Generate docs for all templates
                include_samples = not no_samples
                generated_files = generator.generate_all_cards(
                    output_dir, include_sample=include_samples
                )

                if generated_files:
                    # Generate index file
                    index_path = generator.generate_index(output_dir)

                    click.echo(click.style("✅ Documentation generated successfully!", fg="green", bold=True))
                    click.echo(f"📄 Generated {len(generated_files)} template documentation files")
                    click.echo(f"📋 Index file: {index_path}")
                    click.echo(f"📁 Documentation directory: {output_dir}")
                else:
                    click.echo("❌ No templates found to document.", err=True)

        except Exception as e:
            click.echo(f"❌ Error generating documentation: {e}", err=True)
            sys.exit(1)

    elif action == "list":
        click.echo("📋 Available templates:")
        try:
            if TemplateRegistry is None:
                click.echo("❌ Template functionality not available", err=True)
                sys.exit(1)
            
            registry = TemplateRegistry()
            templates = registry.list_templates()

            if not templates:
                click.echo("No templates found.")
                return

            for template_info in templates:
                slug = template_info["slug"]
                version = template_info["current_version"] or "unknown"
                click.echo(f"  - {slug} (v{version})")
        except Exception as e:
            click.echo(f"❌ Error listing templates: {e}", err=True)
            sys.exit(1)

    elif action == "search":
        click.echo("🔍 Template search is not implemented yet.")


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
                "❌ FastAPI and uvicorn are required to run the API server.\n"
                "💡 Install with: pip install fastapi uvicorn",
                err=True,
            )
            sys.exit(1)

        click.echo(f"🚀 Starting API server on http://{host}:{port}")
        click.echo(f"📚 API documentation: http://{host}:{port}/docs")

        uvicorn.run("meta_agent.api:app", host=host, port=port, reload=reload)

    except ImportError as e:
        click.echo(f"❌ Missing dependency for API server: {e}", err=True)
        click.echo("💡 Install with: pip install fastapi uvicorn", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n⚠️  Server stopped by user", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
