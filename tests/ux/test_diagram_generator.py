import pytest
from meta_agent.ux import DiagramGenerator, DiagramGenerationError


MINIMAL_SPEC = {
    "task_description": "Sample agent",
    "inputs": {"query": "string"},
    "outputs": {"result": "string"},
}


def test_generate_basic_diagram():
    """DiagramGenerator produces valid mermaid syntax for a simple spec."""
    generator = DiagramGenerator()
    diagram = generator.generate(MINIMAL_SPEC)

    assert diagram.startswith("flowchart TB\n")
    assert "IN_query" in diagram
    assert "OUT_result" in diagram


def test_invalid_spec_error():
    """Non-mapping specs raise DiagramGenerationError."""
    generator = DiagramGenerator()
    with pytest.raises(DiagramGenerationError):
        generator.generate(None)  # type: ignore[arg-type]


def test_custom_node_styles():
    """Custom node style directives are included in output."""
    generator = DiagramGenerator()
    styles = {"AGENT": "fill:#fff"}
    diagram = generator.generate(MINIMAL_SPEC, node_styles=styles)

    assert "style AGENT fill:#fff" in diagram
