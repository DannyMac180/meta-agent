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
    def __init__(self, agent: Agent):
        self.agent = agent  # Keep the main agent for potential meta-tasks or fallback
        self.planning_engine = PlanningEngine()
        self.sub_agent_manager = SubAgentManager()
        logger.info("MetaAgentOrchestrator initialized.")

    async def run(self, specification: Dict[str, Any]) -> Any:
        """
        Entry point for orchestrating agent creation and execution.
        """
        logger.info(f"Starting orchestration for specification: {specification.get('name', 'Unnamed')}")
        final_results = {}
        try:
            # 1. Decompose the specification into tasks
            # TODO: Enhance decompose_spec to return tasks with specific inputs/details
            decomposed_tasks = self.decompose_spec(specification)
            logger.info(f"Specification decomposed into {len(decomposed_tasks.get('subtasks', []))} tasks.")

            # 2. Analyze tasks and create an execution plan
            execution_plan = self.planning_engine.analyze_tasks(decomposed_tasks)
            logger.info(f"Execution plan generated: {execution_plan}")

            # 3. Get agent assignments for tasks
            sub_agent_assignments = self.delegate_to_sub_agents(execution_plan)
            logger.info(f"Sub-agent assignments determined for tasks: {list(sub_agent_assignments.keys())}")

            # 4. Execute tasks using assigned sub-agents according to the plan
            logger.info("Starting task execution based on plan.")
            execution_order = execution_plan.get('execution_order', [])
            task_details_map = {task['id']: task for task in decomposed_tasks.get('subtasks', [])} # Map for easy lookup

            if not execution_order:
                 logger.warning("Execution order is empty. No tasks to execute.")
                 # Decide return value? Maybe return the plan?
                 return {"status": "No tasks to execute", "plan": execution_plan}


            for task_id in execution_order:
                if task_id not in sub_agent_assignments:
                    logger.error(f"No agent assigned for task {task_id}. Skipping.")
                    final_results[task_id] = {"status": "skipped", "error": "No agent assigned"}
                    continue

                sub_agent = sub_agent_assignments[task_id]
                task_detail = task_details_map.get(task_id)

                if not task_detail:
                     logger.error(f"Details not found for task {task_id}. Cannot execute.")
                     final_results[task_id] = {"status": "skipped", "error": "Task details not found"}
                     continue

                logger.info(f"Executing task {task_id} using agent {sub_agent}...")

                # TODO: Refine how task details/inputs are passed to sub-agents.
                #       This currently passes the original subtask dict from decomposition.
                #       It might need context from previous tasks.
                task_input = task_detail # Placeholder: use the decomposed task dict as input

                try:
                    # *** Replace placeholder object call with actual Runner.run for the sub_agent ***
                    # result = await Runner.run(sub_agent, task_input) # Assuming sub_agent is a valid Agent object
                    # For now, simulate execution:
                    logger.warning(f"Simulating Runner.run for sub_agent on task {task_id}")
                    result = {"status": "simulated_success", "output": f"Result for {task_id}"}
                    final_results[task_id] = result
                    logger.info(f"Task {task_id} completed. Result: {result}")
                except Exception as task_exc:
                    logger.error(f"Error executing task {task_id} with agent {sub_agent}: {task_exc}", exc_info=True)
                    final_results[task_id] = {"status": "failed", "error": str(task_exc)}


            # No longer running the main agent directly
            # logger.warning("Executing main agent directly - Sub-agent delegation not yet implemented.")
            # result = await Runner.run(self.agent, specification)

            logger.info("Orchestration completed successfully.")
            return final_results # Return the collected results from sub-tasks
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            # Include partial results if available
            return {"status": "failed", "error": str(e), "partial_results": final_results}

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

    def delegate_to_sub_agents(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses the SubAgentManager to get or create sub-agents for tasks based on the plan.

        Args:
            execution_plan: The plan generated by the PlanningEngine.
                            Expected format includes 'task_requirements':
                            [{'task_id': 't1', 'tools': [...], 'guardrails': [...]}, ...]

        Returns:
            A dictionary mapping task IDs to the assigned agent (or agent ID).
            Example: {'task_1': agent_instance_or_id, 'task_2': agent_instance_or_id}
        """
        logger.info("Delegating tasks to sub-agents based on execution plan.")
        assignments = {}
        task_requirements_list = execution_plan.get('task_requirements', [])

        if not task_requirements_list:
            logger.warning("No task requirements found in execution plan. Cannot delegate.")
            return assignments

        for task_req in task_requirements_list:
            task_id = task_req.get('task_id')
            if not task_id:
                logger.warning(f"Skipping task requirement with missing ID: {task_req}")
                continue

            logger.debug(f"Attempting to get/create agent for task: {task_id}")
            agent = self.sub_agent_manager.get_or_create_agent(task_req)

            if agent:
                # Store the agent instance or an identifier
                assignments[task_id] = agent
                logger.info(f"Assigned agent {agent} to task {task_id}")
            else:
                logger.error(f"Could not assign agent for task {task_id}. Skipping delegation for this task.")

        logger.info("Sub-agent delegation process complete.")
        return assignments
