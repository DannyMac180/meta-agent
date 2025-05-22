"""Simple generator for basic unit tests of generated tools."""

from meta_agent.parsers.tool_spec_parser import ToolSpecification


def _example_value(param_type: str) -> str:
    mapping = {
        "int": "1",
        "integer": "1",
        "float": "1.0",
        "string": "'test'",
        "bool": "True",
        "boolean": "True",
        "list": "[]",
        "dict": "{}",
    }
    return mapping.get(param_type.lower(), "None")


def generate_basic_tests(spec: ToolSpecification) -> str:
    """Generate minimal pytest code exercising the generated tool."""
    param_assignments = []
    for param in spec.input_parameters:
        value = _example_value(param.type_)
        param_assignments.append(f"{param.name}={value}")
    args = ", ".join(param_assignments)
    test_code = f"""
import importlib

def test_call():
    mod = importlib.import_module('tool')
    func = getattr(mod, '{spec.name}')
    func({args})
"""
    return test_code
