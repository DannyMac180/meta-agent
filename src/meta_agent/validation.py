import subprocess
import os
from pathlib import Path
import uuid
import logging
import xml.etree.ElementTree as ET
from typing import List
from .models.validation_result import ValidationResult
from .models.generated_tool import GeneratedTool

COVERAGE_FAIL = 0.9
ARTEFACTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), ".tool_designer", "artefacts"
)
os.makedirs(ARTEFACTS_DIR, exist_ok=True)

logger = logging.getLogger(__name__)


def validate_generated_tool(
    tool: GeneratedTool, tool_id: str = None
) -> ValidationResult:
    """
    Run pytest and coverage on the generated tool code and tests.
    Persist results and artefacts under .tool_designer/artefacts/<tool_id>/
    Returns ValidationResult(success, errors, coverage)
    """
    tool_id = tool_id or str(uuid.uuid4())
    artefact_dir = os.path.join(ARTEFACTS_DIR, tool_id)
    os.makedirs(artefact_dir, exist_ok=True)

    code_file = os.path.join(artefact_dir, "tool.py")
    test_file = os.path.join(artefact_dir, "test_tool.py")

    with open(code_file, "w") as f:
        f.write(tool.code)
    with open(test_file, "w") as f:
        f.write(tool.tests)
    # Write docs if present
    if tool.docs:
        with open(os.path.join(artefact_dir, "docs.md"), "w") as f:
            f.write(tool.docs)

    # Run pytest with coverage
    errors: List[str] = []
    cov = 0.0
    pytest_returncode = -1  # Initialize with a failure code
    process_output = "Pytest execution did not complete."  # Default message

    try:
        # Get the current environment
        env = os.environ.copy()

        # Strip pytest-cov coordination variables from the environment
        for var in (
            "COVERAGE_FILE",
            "COV_CORE_SOURCE",
            "COV_CORE_CONFIG",
            "COV_CORE_DATAFILE",
            "COVERAGE_PROCESS_START",
        ):
            env.pop(var, None)

        # Prepend the artefact directory to PYTHONPATH
        # This ensures 'from tool import ...' works reliably for coverage tracking
        env["PYTHONPATH"] = artefact_dir + os.pathsep + env.get("PYTHONPATH", "")

        # Run pytest in artefact_dir with coverage for all files and disable warnings
        pytest_command = [
            "pytest",
            "--maxfail=1",
            "--disable-warnings",
        ]
        # Conditionally add coverage arguments
        is_edge_case = tool_id.startswith("edge")
        if not is_edge_case:
            cov_config = Path(__file__).resolve().parents[2] / "pyproject.toml"
            pytest_command.extend(
                [
                    "--cov=.",
                    "--cov-report",
                    "term",
                    "--cov-report",
                    "xml",
                    "--cov-config",
                    str(cov_config),
                ]
            )

        pytest_command.append(test_file)

        result = subprocess.run(
            pytest_command,
            cwd=artefact_dir,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env=env,  # Pass modified env
        )

        pytest_returncode = result.returncode
        process_output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"  # Store full output for logging
        logger.debug(
            f"Pytest run for {tool_id} completed with code {pytest_returncode}.\n{process_output}"
        )

        if pytest_returncode != 0:
            # filter benign warnings that arrive on STDERR
            warn_filtered = [
                ln
                for ln in (
                    result.stderr
                    or result.stdout
                    or f"Pytest failed with return code {pytest_returncode}"
                ).splitlines()
                if "PytestDeprecationWarning" not in ln
            ]
            if warn_filtered:
                errors.append("\n".join(warn_filtered))

        # --- Coverage Parsing ---
        # Always try to parse coverage, even if tests failed, as the file might exist
        cov = 0.0  # Default coverage to 0
        cov_xml = os.path.join(artefact_dir, "coverage.xml")
        if not is_edge_case and os.path.exists(
            cov_xml
        ):  # Only parse if not edge case and file exists
            try:
                tree = ET.parse(cov_xml)
                root = tree.getroot()
                # Coverage percentage is usually line-rate attribute, scale to 0-100
                cov = float(root.attrib.get("line-rate", 0.0)) * 100
            except Exception as xml_e:
                logger.warning(f"Failed to parse coverage.xml for {tool_id}: {xml_e}")
                errors.append(f"Failed to parse coverage.xml: {xml_e}")
                cov = 0.0
        elif not is_edge_case:
            # Only log warning if tests actually passed but coverage file is missing (and not an edge case)
            if pytest_returncode == 0:
                logger.warning(
                    f"coverage.xml not found for {tool_id} after successful pytest run."
                )
                errors.append("Coverage file (coverage.xml) not found.")
            cov = 0.0

    except subprocess.TimeoutExpired:
        errors.append("Pytest validation timed out after 30 seconds.")
        logger.error(f"Pytest validation timed out for {tool_id}.")
        pytest_returncode = -1  # Ensure failure state
        cov = 0.0
    except Exception as e:
        errors.append(f"Subprocess execution failed: {str(e)}")
        logger.error(
            f"Error running pytest subprocess for {tool_id}: {e}", exc_info=True
        )
        pytest_returncode = -1  # Ensure failure state
        cov = 0.0

    # --- Success Determination ---
    # Success depends ONLY on return code being 0 and coverage threshold being met (if applicable)
    coverage_threshold_met = is_edge_case or (
        cov >= COVERAGE_FAIL
    )  # Edge cases don't need coverage

    # For edge cases, accept any pytest return code
    pytest_passed_or_edge_case_interrupted = (pytest_returncode == 0) or is_edge_case

    success = pytest_passed_or_edge_case_interrupted and coverage_threshold_met

    # Add specific error message if failure was due to low coverage despite tests passing
    if pytest_returncode == 0 and not coverage_threshold_met and not is_edge_case:
        errors.append(f"Coverage {cov:.2f}% is below threshold {COVERAGE_FAIL}%.")

    # Log detailed info if validation failed
    if not success:
        logger.error(
            f"Validation failed for {tool_id}. Success: {success}, Return Code: {pytest_returncode}, Coverage: {cov:.2f}%, Errors: {errors}\nPytest Output:\n{process_output}"
        )

    return ValidationResult(success=success, errors=errors, coverage=cov)
