"""
Unit tests for the PlanningEngine.
"""

import pytest

# Make sure the src directory is importable
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from meta_agent.planning_engine import PlanningEngine

# Fixture for the PlanningEngine instance
@pytest.fixture
def engine():
    return PlanningEngine()

# Sample decomposed tasks for testing
@pytest.fixture
def sample_decomposed_tasks():
    return {
        "subtasks": [
            {"id": "task_1", "description": "Generate code for the login module."},
            {"id": "task_2", "description": "Write unit tests for the new component."},
            {"id": "task_3", "description": "Review the security aspects of the authentication flow."},
            {"id": "task_4", "description": "Implement security checks and format the code style."},
            {"id": "task_5", "description": "Document the API endpoints."},
            {"id": "task_6"}, # Task missing description
            # Task missing ID is handled by the method itself
        ]
    }

# Test case for basic tool assignment
def test_analyze_tasks_assigns_coder_tool(engine):
    tasks = {"subtasks": [{"id": "t1", "description": "Implement the user profile page."}]}
    plan = engine.analyze_tasks(tasks)
    assert len(plan['task_requirements']) == 1
    req = plan['task_requirements'][0]
    assert req['task_id'] == 't1'
    assert 'coder_tool' in req['tools']
    assert not req['guardrails'] # No guardrail keywords
    assert plan['execution_order'] == ['t1']

# Test case for basic guardrail assignment
def test_analyze_tasks_assigns_security_guardrail(engine):
    tasks = {"subtasks": [{"id": "t2", "description": "Analyze security risks."}]}
    plan = engine.analyze_tasks(tasks)
    assert len(plan['task_requirements']) == 1
    req = plan['task_requirements'][0]
    assert req['task_id'] == 't2'
    assert 'reviewer_tool' in req['tools'] # 'analyze' keyword
    assert 'security_guardrail' in req['guardrails']
    assert plan['execution_order'] == ['t2']

# Test case for multiple assignments (tool and guardrail)
def test_analyze_tasks_assigns_multiple(engine):
    tasks = {"subtasks": [{"id": "t3", "description": "Develop secure login code and lint it."}]}
    plan = engine.analyze_tasks(tasks)
    assert len(plan['task_requirements']) == 1
    req = plan['task_requirements'][0]
    assert req['task_id'] == 't3'
    assert 'coder_tool' in req['tools']
    assert 'security_guardrail' in req['guardrails']
    assert 'style_guardrail' in req['guardrails']
    assert plan['execution_order'] == ['t3']

# Test case for no specific keywords matched
def test_analyze_tasks_no_keywords(engine):
    tasks = {"subtasks": [{"id": "t4", "description": "Update the documentation."}]}
    plan = engine.analyze_tasks(tasks)
    assert len(plan['task_requirements']) == 1
    req = plan['task_requirements'][0]
    assert req['task_id'] == 't4'
    assert not req['tools'] # No tool keywords matched
    assert not req['guardrails'] # No guardrail keywords matched
    assert plan['execution_order'] == ['t4']

# Test case for comprehensive example using the fixture
def test_analyze_tasks_comprehensive(engine, sample_decomposed_tasks):
    plan = engine.analyze_tasks(sample_decomposed_tasks)
    reqs = {req['task_id']: req for req in plan['task_requirements']}

    assert len(plan['task_requirements']) == 6 # Expect 6 tasks, including task_6 with no description
    assert plan['execution_order'] == ['task_1', 'task_2', 'task_3', 'task_4', 'task_5', 'task_6'] # Include task_6

    # Task 1: Generate code
    assert 'coder_tool' in reqs['task_1']['tools']
    assert not reqs['task_1']['guardrails']

    # Task 2: Write tests
    assert 'tester_tool' in reqs['task_2']['tools']
    assert not reqs['task_2']['guardrails']

    # Task 3: Review security
    assert 'reviewer_tool' in reqs['task_3']['tools']
    assert 'security_guardrail' in reqs['task_3']['guardrails']

    # Task 4: Implement security checks and format code style
    assert 'coder_tool' in reqs['task_4']['tools']
    assert 'security_guardrail' in reqs['task_4']['guardrails']
    assert 'style_guardrail' in reqs['task_4']['guardrails']

    # Task 5: Document API (no specific keywords)
    assert not reqs['task_5']['tools']
    assert not reqs['task_5']['guardrails']

    # Task 6: No description - should have no tools/guardrails assigned
    assert 'task_6' in reqs
    assert not reqs['task_6']['tools']
    assert not reqs['task_6']['guardrails']

# Test case for empty input
def test_analyze_tasks_empty_input(engine):
    tasks = {"subtasks": []}
    plan = engine.analyze_tasks(tasks)
    assert not plan['task_requirements']
    assert not plan['execution_order']
    assert not plan['dependencies']

# Test case for input with no subtasks key
def test_analyze_tasks_no_subtasks_key(engine):
    tasks = {}
    plan = engine.analyze_tasks(tasks)
    assert not plan['task_requirements']
    assert not plan['execution_order']
    assert not plan['dependencies']

# Test case for task missing description (should be skipped in current logic)
def test_analyze_tasks_missing_description(engine):
    tasks = {"subtasks": [{"id": "t_no_desc"}]}
    plan = engine.analyze_tasks(tasks)
    assert len(plan['task_requirements']) == 1 # Task is added but has no tools/guardrails
    req = plan['task_requirements'][0]
    assert req['task_id'] == 't_no_desc'
    assert not req['tools']
    assert not req['guardrails']
    assert plan['execution_order'] == ['t_no_desc']
