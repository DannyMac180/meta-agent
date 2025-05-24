from meta_agent.template_engine import TemplateEngine, validate_agent_code
import os

def test_assemble_and_validate_default():
    # Minimal sub-agent outputs for the default template
    outputs = {
        "agent_class_name": "TestAgent",
        "name": "TestAgent",
        "instructions": "Do stuff",
        "core_logic": "return 'ok'",
        "tools": ["def tool1(self): pass"],
        "guardrails": ["def guardrail1(self): pass"]
    }
    # Setup template engine to use the correct templates dir
    templates_dir = os.path.join(os.path.dirname(__file__), "../src/meta_agent/templates")
    engine = TemplateEngine(templates_dir=templates_dir)
    code = engine.assemble_agent(outputs)
    assert isinstance(code, str)
    valid, err = validate_agent_code(code)
    assert valid, f"Validation failed: {err}"

def test_validate_agent_code_failures():
    # No Agent subclass
    code = "class Foo: pass"
    valid, err = validate_agent_code(code)
    assert not valid and "Agent" in err
    # Agent subclass but no run method
    code = "from agents import Agent\nclass X(Agent): pass"
    valid, err = validate_agent_code(code)
    assert not valid and "run" in err
    # Syntax error
    code = "def foo(:)"
    valid, err = validate_agent_code(code)
    assert not valid and "Syntax error" in err
