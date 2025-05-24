"""
Defines the PlanningEngine class responsible for analyzing decomposed tasks.
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PlanningEngine:
    """Handles the analysis of decomposed tasks and generation of execution plans."""

    # Define keyword mappings (can be expanded)
    TOOL_KEYWORD_MAP = {
        ("code", "generate", "implement", "develop"): "coder_tool",
        ("test", "validate", "verify"): "tester_tool",
        ("review", "analyze", "check"): "reviewer_tool",
        # Add more mappings as needed
    }

    GUARDRAIL_KEYWORD_MAP = {
        ("security", "sensitive", "credentials", "secure"): "security_guardrail",
        ("style", "lint", "format"): "style_guardrail",
        # Add more mappings as needed
    }

    def __init__(self):
        logger.info("PlanningEngine initialized.")

    def analyze_tasks(self, decomposed_tasks: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes decomposed tasks to determine required tools, guardrails,
        and execution order.

        Args:
            decomposed_tasks: A dictionary containing subtasks, typically from
                              the orchestrator's decompose_spec method.

        Returns:
            A dictionary representing the execution plan, including task requirements,
            execution order, and dependencies.
        """
        logger.info("Analyzing decomposed tasks...")
        subtasks = decomposed_tasks.get("subtasks", [])
        task_requirements = []
        execution_order = []
        dependencies = {} # Placeholder for dependency logic

        if not subtasks:
            logger.warning("No subtasks found in decomposed tasks.")
            return {
                "task_requirements": [],
                "execution_order": [],
                "dependencies": {},
            }

        for task in subtasks:
            task_id = task.get("id")
            description = task.get("description", "").lower()
            if not task_id:
                logger.warning(f"Skipping task without ID: {task}")
                continue

            required_tools = set() # Use set to avoid duplicates
            required_guardrails = set()

            # Determine tools based on keywords
            found_tool = False
            for keywords, tool_name in self.TOOL_KEYWORD_MAP.items():
                if any(keyword in description for keyword in keywords):
                    required_tools.add(tool_name)
                    found_tool = True
                    # break # Decide if first match is enough or allow multiple tools

            if not found_tool:
                logger.warning(f"No specific tool identified for task {task_id}. Assigning default or handling needed.")
                # required_tools.add("general_tool") # Example default

            # Determine guardrails based on keywords (similar logic)
            found_guardrail = False
            for keywords, guardrail_name in self.GUARDRAIL_KEYWORD_MAP.items():
                 if any(keyword in description for keyword in keywords):
                    required_guardrails.add(guardrail_name)
                    found_guardrail = True
                    # break

            if not found_guardrail:
                 logger.debug(f"No specific guardrails identified for task {task_id}.")
                 # required_guardrails.add("default_guardrail") # Example default

            task_requirements.append({
                "task_id": task_id,
                "tools": sorted(list(required_tools)), # Sort tools list
                "guardrails": list(required_guardrails),
                "description": task.get("description") # Keep original description if needed
            })
            execution_order.append(task_id) # Simple sequential order for now

        logger.info(f"Generated execution plan with {len(execution_order)} tasks.")
        plan = {
            "task_requirements": task_requirements,
            "execution_order": execution_order,
            "dependencies": dependencies,
        }
        logger.debug(f"Execution Plan: {plan}")
        return plan
