"""
Core orchestration framework for the meta-agent.
Integrates with OpenAI Agents SDK and provides interfaces for decomposing agent specs and delegating to sub-agents.
"""

import logging
from agents import Agent, Runner  # OpenAI Agents SDK
from typing import Any, Dict, List
from .planning_engine import PlanningEngine
from .sub_agent_manager import SubAgentManager

logger = logging.getLogger(__name__)


class MetaAgentOrchestrator:
    """
    Coordinates the overall process of task decomposition, planning, and execution
    using specialized sub-agents.
    """

    def __init__(self, planning_engine: PlanningEngine, sub_agent_manager: SubAgentManager):
        """Initializes the Orchestrator with necessary components."""
        # self.agent = agent # Removed main agent dependency
        self.planning_engine = planning_engine
        self.sub_agent_manager = sub_agent_manager
        logger.info("MetaAgentOrchestrator initialized with PlanningEngine and SubAgentManager.")

    async def run(self, specification: Dict[str, Any]) -> Any:
        """
        Entry point for orchestrating agent creation and execution.
        """
        logger.info(f"Starting orchestration for specification: {specification.get('name', 'Unnamed')}")
        try:
            # 1. Decompose the specification into tasks
            # TODO: Enhance decompose_spec to return tasks with specific inputs/details
            decomposed_tasks = self.decompose_spec(specification)
            logger.info(f"Specification decomposed into {len(decomposed_tasks.get('subtasks', []))} tasks.")

            # 2. Analyze tasks and create an execution plan
            execution_plan = self.planning_engine.analyze_tasks(decomposed_tasks)
            logger.info(f"Execution plan generated: {execution_plan}")

            # 3. (Removed) No longer pre-assigning agents here.
            # sub_agent_assignments = self.delegate_to_sub_agents(execution_plan)
            # logger.info(f"Sub-agent assignments determined for tasks: {list(sub_agent_assignments.keys())}")

            # 4. Execute tasks using assigned sub-agents according to the plan
            logger.info("Starting task execution loop...")
            execution_results = {}
            execution_order = execution_plan.get("execution_order", [])
            task_requirements_map = {req['task_id']: req for req in execution_plan.get("task_requirements", [])}

            if not execution_order:
                logger.warning("Execution order is empty. No tasks to execute.")
                # Return status indicating no tasks, not necessarily a failure
                return {"status": "No tasks to execute"}

            for task_id in execution_order:
                if task_id not in task_requirements_map:
                    logger.error(f"Task ID {task_id} found in execution_order but not in task_requirements. Skipping.")
                    execution_results[task_id] = {"status": "error", "error": "Missing task requirements"}
                    continue

                task_req = task_requirements_map[task_id]
                sub_agent = self.sub_agent_manager.get_or_create_agent(task_req)

                if sub_agent:
                    logger.info(f"Executing task {task_id} using agent {sub_agent.name}...")
                    try:
                        # Pass the task requirements as the specification to the sub-agent's run method
                        # The sub-agent's run method should know how to handle this dictionary
                        task_result = await sub_agent.run(specification=task_req)
                        logger.info(f"Task {task_id} completed by {sub_agent.name}. Result: {task_result.get('status')}")
                        execution_results[task_id] = task_result
                    except Exception as e:
                        logger.error(f"Error executing task {task_id} with agent {sub_agent.name}: {e}", exc_info=True)
                        execution_results[task_id] = {"status": "failed", "error": str(e)}
                else:
                    logger.error(f"Could not get or create sub-agent for task {task_id}. Skipping execution.")
                    execution_results[task_id] = {"status": "failed", "error": "Sub-agent creation/retrieval failed"}

            logger.info("Orchestration completed successfully.")
            return execution_results # Return the dictionary of results
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            # Include partial results if available
            return {"status": "failed", "error": str(e)} # Removed partial_results

    def decompose_spec(self, specification: Dict[str, Any]) -> Dict[str, Any]:
        """
        Stub: Decompose the agent specification into tasks/subspecs.
        Needs to return tasks with IDs and descriptions.
        Example: {'subtasks': [{'id': 'task_1', 'description': 'Generate code...'}, ...]}
        """
        logger.warning("Using stub decompose_spec. Returning dummy tasks.")
        # Return dummy tasks for testing the execution loop
        return {
            "subtasks": [
                {"id": "task_1", "description": "Generate initial code structure"},
                {"id": "task_2", "description": "Write unit tests for the structure"},
                {"id": "task_3", "description": "Refactor the generated code"}
            ]
        }
