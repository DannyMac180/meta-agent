import ast
from meta_agent.generators.test_generator import generate_basic_tests
from meta_agent.parsers.tool_spec_parser import ToolSpecification, ToolParameter


def test_generate_basic_tests():
    spec = ToolSpecification(
        name="greet",
        purpose="Greets a user",
        input_parameters=[ToolParameter(name="name", type_="string")],
        output_format="string",
    )
    test_code = generate_basic_tests(spec)
    assert "import importlib" in test_code
    assert "greet" in test_code
    # ensure code is syntactically valid
    ast.parse(test_code)
