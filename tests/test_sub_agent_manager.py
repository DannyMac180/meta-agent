"""
Unit tests for the SubAgentManager.
"""

import pytest

# Make sure the src directory is importable
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from meta_agent.sub_agent_manager import (
    SubAgentManager,
    BaseAgent,
    CoderAgent,
    TesterAgent,
    ReviewerAgent
)

# Fixture for the SubAgentManager instance
@pytest.fixture
def manager():
    return SubAgentManager()

# Test cases for get_or_create_agent

def test_get_or_create_coder_agent(manager):
    req = {"task_id": "t1", "tools": ["coder_tool"], "guardrails": [], "description": "code task"}
    agent = manager.get_or_create_agent(req)
    assert isinstance(agent, CoderAgent)
    assert agent is not None

def test_get_or_create_tester_agent(manager):
    req = {"task_id": "t2", "tools": ["tester_tool"], "guardrails": [], "description": "test task"}
    agent = manager.get_or_create_agent(req)
    assert isinstance(agent, TesterAgent)
    assert agent is not None

def test_get_or_create_reviewer_agent(manager):
    req = {"task_id": "t3", "tools": ["reviewer_tool"], "guardrails": [], "description": "review task"}
    agent = manager.get_or_create_agent(req)
    assert isinstance(agent, ReviewerAgent)
    assert agent is not None

def test_get_or_create_multiple_tools_uses_first(manager):
    # Expects CoderAgent because 'coder_tool' is first
    req = {"task_id": "t4", "tools": ["coder_tool", "tester_tool"], "guardrails": [], "description": "multi tool task"}
    agent = manager.get_or_create_agent(req)
    assert isinstance(agent, CoderAgent)
    assert agent is not None

def test_get_or_create_no_matching_tool_returns_base(manager):
    req = {"task_id": "t5", "tools": ["unknown_tool"], "guardrails": [], "description": "unknown tool task"}
    agent = manager.get_or_create_agent(req)
    assert isinstance(agent, BaseAgent)
    assert agent is not None

def test_get_or_create_no_tools_returns_base(manager):
    req = {"task_id": "t6", "tools": [], "guardrails": [], "description": "no tool task"}
    agent = manager.get_or_create_agent(req)
    assert isinstance(agent, BaseAgent)
    assert agent is not None

def test_get_or_create_empty_requirements_returns_base(manager):
    req = {}
    agent = manager.get_or_create_agent(req)
    assert isinstance(agent, BaseAgent)
    assert agent is not None

# Test caching
def test_agent_caching(manager):
    req1 = {"task_id": "c1", "tools": ["coder_tool"], "guardrails": [], "description": "code task 1"}
    req2 = {"task_id": "c2", "tools": ["coder_tool"], "guardrails": [], "description": "code task 2"}
    req3 = {"task_id": "t1", "tools": ["tester_tool"], "guardrails": [], "description": "test task 1"}

    agent1 = manager.get_or_create_agent(req1)
    agent2 = manager.get_or_create_agent(req2)
    agent3 = manager.get_or_create_agent(req3)

    assert isinstance(agent1, CoderAgent)
    assert isinstance(agent2, CoderAgent)
    assert isinstance(agent3, TesterAgent)

    # Coder agents should be the same instance due to caching
    assert agent1 is agent2

    # Tester agent should be a different instance
    assert agent1 is not agent3

    # Check internal cache state (optional)
    assert CoderAgent.__name__ in manager.active_agents
    assert TesterAgent.__name__ in manager.active_agents
    # Check that list_agents only returns the class-based agents (not tool-based)
    assert len(manager.list_agents()) == 2 # Only one CoderAgent and one TesterAgent cached
