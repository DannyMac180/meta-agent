import tempfile
import subprocess
import os
import shutil
import uuid
from typing import List
from .models.validation_result import ValidationResult
from .models.generated_tool import GeneratedTool

COVERAGE_FAIL = 0.9
ARTEFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".tool_designer", "artefacts")
os.makedirs(ARTEFACTS_DIR, exist_ok=True)

def validate_generated_tool(tool: GeneratedTool, tool_id: str = None) -> ValidationResult:
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
    try:
        result = subprocess.run([
            "pytest", test_file, "--cov", code_file, "--cov-report", "term", "--cov-report", "xml", "--maxfail=1", "--disable-warnings"
        ], cwd=artefact_dir, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            errors.append(result.stderr or result.stdout)
        # Parse coverage.xml
        cov_xml = os.path.join(artefact_dir, "coverage.xml")
        if os.path.exists(cov_xml):
            import xml.etree.ElementTree as ET
            tree = ET.parse(cov_xml)
            root = tree.getroot()
            try:
                cov = float(root.attrib.get("line-rate", 0.0))
            except Exception:
                cov = 0.0
        else:
            cov = 0.0
    except Exception as e:
        errors.append(str(e))
    success = (not errors) and (cov >= COVERAGE_FAIL)
    return ValidationResult(success=success, errors=errors, coverage=cov)
