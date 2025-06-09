import pytest
import ast
from meta_agent.parsers.tool_spec_parser import ToolSpecification, ToolParameter
from meta_agent.generators.tool_code_generator import ToolCodeGenerator

# --- Test Data ---

SPEC_SIMPLE = ToolSpecification(
    name="get_current_time",
    purpose="Gets the current system time.",
    input_parameters=[],
    output_format="string",
)

SPEC_WITH_PARAMS = ToolSpecification(
    name="get_stock_price",
    purpose="Fetches the current stock price for a given ticker symbol.",
    input_parameters=[
        ToolParameter(
            name="ticker",
            type_="string",
            description="The stock ticker symbol (e.g., AAPL)",
            required=True,
        ),
        ToolParameter(
            name="exchange",
            type_="string",
            description="The stock exchange (e.g., NASDAQ)",
            required=False,
        ),
    ],
    output_format="float",
)

SPEC_LIST_PARAM = ToolSpecification(
    name="sum_numbers",
    purpose="Calculates the sum of a list of numbers.",
    input_parameters=[
        ToolParameter(
            name="numbers",
            type_="list[float]",
            description="A list of numbers to sum.",
            required=True,
        )
    ],
    output_format="float",
)

SPEC_INVALID_SYNTAX_IN_PURPOSE = ToolSpecification(
    name="bad_tool",
    # Purpose contains syntax that might break the docstring if not handled
    purpose="Fetches data using `SELECT * FROM table WHERE id = {id}`. It's tricky.",
    input_parameters=[
        ToolParameter(
            name="id", type_="integer", description="The ID to fetch.", required=True
        )
    ],
    output_format="dict",
)

# --- Test Cases ---


def test_generate_simple_tool():
    """Tests generating a tool with no parameters."""
    generator = ToolCodeGenerator(SPEC_SIMPLE)
    code = generator.generate()

    # Basic checks: Not empty, doesn't start with error marker
    assert code.strip()
    assert not code.startswith("# SYNTAX ERROR")

    # Check syntax validity
    try:
        tree = ast.parse(code)
        assert isinstance(tree, ast.Module)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax error: {e}\nCode:\n{code}")

    # Check function definition
    func_defs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    assert len(func_defs) == 1
    func_def = func_defs[0]
    assert func_def.name == "get_current_time"
    assert not func_def.args.args  # No arguments
    assert func_def.returns.id == "str"  # Check return type hint

    # Check docstring content (basic)
    docstring = ast.get_docstring(func_def)
    assert docstring is not None
    assert "Gets the current system time." in docstring
    assert "Returns:" in docstring
    assert "str: string" in docstring  # Check return type in docstring


def test_generate_tool_with_params():
    """Tests generating a tool with multiple parameters (required and optional)."""
    generator = ToolCodeGenerator(SPEC_WITH_PARAMS)
    code = generator.generate()

    assert code.strip()
    assert not code.startswith("# SYNTAX ERROR")

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax error: {e}\nCode:\n{code}")

    func_defs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    assert len(func_defs) == 1
    func_def = func_defs[0]
    assert func_def.name == "get_stock_price"
    assert len(func_def.args.args) == 2

    # Check parameters and type hints
    assert func_def.args.args[0].arg == "ticker"
    assert func_def.args.args[0].annotation.id == "str"
    assert func_def.args.args[1].arg == "exchange"
    assert func_def.args.args[1].annotation.id == "str"

    # Check optional parameter default (should be None)
    assert len(func_def.args.defaults) == 1
    assert isinstance(func_def.args.defaults[0], ast.Constant)
    assert func_def.args.defaults[0].value is None

    assert func_def.returns.id == "float"

    # Check docstring params
    docstring = ast.get_docstring(func_def)
    assert docstring is not None
    assert "ticker: The stock ticker symbol (e.g., AAPL) (Required)" in docstring
    assert "exchange: The stock exchange (e.g., NASDAQ) (Optional)" in docstring
    assert "float: float" in docstring  # Check return type in docstring


def test_generate_tool_with_list_param():
    """Tests generating a tool with a generic list parameter."""
    generator = ToolCodeGenerator(SPEC_LIST_PARAM)
    code = generator.generate()

    assert code.strip()
    assert not code.startswith("# SYNTAX ERROR")

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax error: {e}\nCode:\n{code}")

    func_defs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    assert len(func_defs) == 1
    func_def = func_defs[0]
    assert func_def.name == "sum_numbers"
    assert len(func_def.args.args) == 1

    # Check list parameter type hint (e.g., List[float])
    assert func_def.args.args[0].arg == "numbers"
    annotation = func_def.args.args[0].annotation
    assert isinstance(annotation, ast.Subscript)
    assert annotation.value.id == "List"
    assert isinstance(annotation.slice, ast.Name)
    assert annotation.slice.id == "float"

    assert func_def.returns.id == "float"

    docstring = ast.get_docstring(func_def)
    assert docstring is not None
    assert "numbers: A list of numbers to sum. (Required)" in docstring
    assert "Returns:" in docstring
    assert "float: float" in docstring  # Check corrected return type in docstring


def test_generate_with_tricky_docstring():
    """Tests generating with characters in purpose/description that might break docstrings."""
    # This primarily tests that the generation doesn't create syntax errors
    # due to quotes or backticks within the specification strings.
    generator = ToolCodeGenerator(SPEC_INVALID_SYNTAX_IN_PURPOSE)
    code = generator.generate()

    assert code.strip()
    assert not code.startswith("# SYNTAX ERROR")

    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax error: {e}\nCode:\n{code}")

    func_defs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    assert len(func_defs) == 1
    func_def = func_defs[0]

    docstring = ast.get_docstring(func_def)
    assert docstring is not None
    # Check if the potentially tricky parts are present (Jinja2 should handle escaping)
    assert "`SELECT * FROM table WHERE id = {id}`" in docstring
    assert "It's tricky." in docstring
    assert "id: The ID to fetch. (Required)" in docstring
    assert "Dict: dict" in docstring  # Check return type mapping
