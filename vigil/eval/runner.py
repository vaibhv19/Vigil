import logging
import os
import time
from typing import Any, List

from vigil.agents.base_adapter import BaseAgentAdapter
from vigil.eval.task_models import TaskDefinition
from vigil.core.sandbox_manager import Sandbox
from vigil.core.exceptions import (
    SandboxProvisionError,
    SandboxTeardownError,
    ToolTimeout,
    AgentExecutionError,
)

logger = logging.getLogger(__name__)

class EvalRunner:
    """
    Orchestrates the evaluation workflow lifecycle: provisioning sandboxes,
    injecting task context, executing agent reasoning loops, timing runs,
    scoring outcomes against state assertions, and ensuring resource cleanup.
    """
    def __init__(self, agent_adapter: BaseAgentAdapter, host_workspace_base: str):
        self.agent_adapter = agent_adapter
        self.host_workspace_base = host_workspace_base

    def run_task(self, task: TaskDefinition) -> dict[str, Any]:
        """
        Orchestrates sandbox startup, context injection, agent execution,
        assertion scoring, and teardown. Guarantees cleanup on failure.
        """
        from vigil.core.sandbox_config import SandboxConfig
        
        config = SandboxConfig()
        
        status = "ERROR"
        failure_reason = None
        tool_calls = []
        assertion_results = {}
        agent_response = ""
        
        start_time = time.perf_counter()
        
        try:
            # Execute within Sandbox lifecycle context manager
            with Sandbox(config, self.host_workspace_base, f"run-{task.task_id}") as manager:
                # 1. Inject Context Files
                from vigil.eval.task_loader import ContextInjector
                ContextInjector.inject_context(manager.workspace_path, task)
                
                # 2. Setup ToolExecutor
                from vigil.core.tool_executor import ToolExecutor
                tool_executor = ToolExecutor(manager)
                
                # 3. Invoke Agent
                try:
                    agent_response = self.agent_adapter.run_task(task.input_prompt, tool_executor)
                except Exception as e:
                    if isinstance(e, ToolTimeout):
                        failure_reason = "TOOL_TIMEOUT"
                    elif isinstance(e, AgentExecutionError):
                        failure_reason = "AGENT_EXECUTION_ERROR"
                    else:
                        failure_reason = "AGENT_EXECUTION_ERROR"
                    logger.error(f"Agent reasoning execution failed: {e}")
                    raise
                    
                # Cache tool executions
                tool_calls = tool_executor.tool_calls
                
                # 4. Scoring assertions
                from vigil.eval.scoring_engine import ScoringEngine
                assertions = task.expected_output.get("assertions", [])
                
                scoring_engine = ScoringEngine(manager.workspace_path, tool_calls)
                passed = scoring_engine.evaluate(assertions)
                assertion_results = scoring_engine.assertion_results
                
                status = "PASS" if passed else "FAIL"
                if not passed:
                    failure_reason = "ASSERTION_FAILED"
                    
        except SandboxProvisionError as e:
            logger.error(f"Sandbox provisioning error: {e}")
            status = "ERROR"
            failure_reason = "SANDBOX_PROVISION_ERROR"
        except SandboxTeardownError as e:
            logger.error(f"Sandbox cleanup error: {e}")
            status = "ERROR"
            failure_reason = "SANDBOX_CLEANUP_ERROR"
        except ToolTimeout as e:
            status = "ERROR"
            failure_reason = "TOOL_TIMEOUT"
        except AgentExecutionError as e:
            status = "ERROR"
            failure_reason = "AGENT_EXECUTION_ERROR"
        except Exception as e:
            logger.error(f"Unhandled operational exception in EvalRunner: {e}")
            status = "ERROR"
            if not failure_reason:
                failure_reason = "INTERNAL_FRAMEWORK_ERROR"
                
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        return {
            "task_id": task.task_id,
            "status": status,
            "failure_reason": failure_reason,
            "duration_ms": duration_ms,
            "agent_response": agent_response,
            "tool_calls": tool_calls,
            "assertion_results": assertion_results
        }

    def run_suite(self, task_dir: str) -> list[dict[str, Any]]:
        """
        Loads and runs all YAML task definitions inside a target folder sequentially.
        """
        from vigil.eval.task_loader import TaskLoader
        import glob
        
        yaml_files = glob.glob(os.path.join(task_dir, "**/*.yaml"), recursive=True) + \
                     glob.glob(os.path.join(task_dir, "**/*.yml"), recursive=True)
                     
        yaml_files.sort()
        results = []
        
        for yaml_file in yaml_files:
            try:
                task_def = TaskLoader.load_task(yaml_file)
                logger.info(f"Loaded task {task_def.task_id} from {yaml_file}")
                res = self.run_task(task_def)
                results.append(res)
            except Exception as e:
                logger.error(f"Failed to load or execute task file {yaml_file}: {e}")
                results.append({
                    "task_id": os.path.basename(yaml_file),
                    "status": "ERROR",
                    "failure_reason": "TASK_DEFINITION_VALIDATION_ERROR",
                    "error_details": str(e),
                    "duration_ms": 0,
                    "agent_response": "",
                    "tool_calls": [],
                    "assertion_results": {}
                })
        return results
