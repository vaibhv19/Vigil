import logging
import os
import time
import uuid
import threading
from typing import Any, Optional


from vigil.agents.base_adapter import BaseAgentAdapter
from vigil.eval.task_models import TaskDefinition
from vigil.core.sandbox_manager import Sandbox
from vigil.core.exceptions import (
    SandboxProvisionError,
    SandboxTeardownError,
    ToolTimeout,
    TaskTimeout,
    AgentExecutionError,
    DatabasePersistenceError,
    AnomalyException,
)
from vigil.core.anomaly_detector import AnomalyDetector

logger = logging.getLogger(__name__)

class TaskExecThread(threading.Thread):
    """
    Thread to run the agent task execution loop, allowing us to enforce task-level timeouts.
    """
    def __init__(self, agent_adapter: BaseAgentAdapter, prompt: str, tool_executor: Any):
        super().__init__()
        self.agent_adapter = agent_adapter
        self.prompt = prompt
        self.tool_executor = tool_executor
        self.result = None
        self.exception = None
        
    def run(self):
        try:
            self.result = self.agent_adapter.run_task(self.prompt, self.tool_executor)
        except Exception as e:
            self.exception = e


class EvalRunner:
    """
    Orchestrates the evaluation workflow lifecycle: provisioning sandboxes,
    injecting task context, executing agent reasoning loops, timing runs,
    scoring outcomes against state assertions, ensuring resource cleanup,
    persisting results to PostgreSQL, and checking for action anomalies.
    """
    def __init__(self, agent_adapter: BaseAgentAdapter, host_workspace_base: str):
        self.agent_adapter = agent_adapter
        self.host_workspace_base = host_workspace_base

    def run_task(
        self, 
        task: TaskDefinition, 
        run_id: Optional[uuid.UUID] = None, 
        timeout_seconds: int = 300
    ) -> dict[str, Any]:
        """
        Orchestrates sandbox startup, context injection, agent execution,
        assertion scoring, and teardown. Guarantees cleanup on failure.
        Saves execution results to DB if run_id is supplied.
        """
        from vigil.core.sandbox_config import SandboxConfig
        
        config = SandboxConfig()
        
        status = "ERROR"
        failure_reason = None
        tool_calls = []
        assertion_results = {}
        agent_response = ""
        
        # 1. Initialize TaskResult in database first if run_id is active
        db_result_id = None
        if run_id:
            from vigil.db.connection import get_session
            from vigil.db.repository import VigilRepository
            try:
                with get_session() as session:
                    db_task = VigilRepository.get_or_create_task(session, task)
                    db_result = VigilRepository.create_task_result(
                        session=session,
                        run_id=run_id,
                        task_id=db_task.id,
                        status="RUNNING",
                        steps_taken=0
                    )
                    db_result_id = db_result.id
            except Exception as e:
                logger.error(f"Failed to pre-register task result in DB: {e}")
                if isinstance(e, DatabasePersistenceError):
                    raise e
                raise DatabasePersistenceError(f"Database pre-registration failed: {e}")

        # 2. Instantiate AnomalyDetector
        anomaly_detector = AnomalyDetector(task_result_id=db_result_id, max_tool_calls=task.max_steps)
        
        start_time = time.perf_counter()
        
        try:
            # Execute within Sandbox lifecycle context manager
            with Sandbox(config, self.host_workspace_base, f"run-{task.task_id}") as manager:
                # 3. Inject Context Files
                from vigil.eval.task_loader import ContextInjector
                ContextInjector.inject_context(manager.workspace_path, task)
                
                # 4. Setup ToolExecutor with AnomalyDetector registered
                from vigil.core.tool_executor import ToolExecutor
                tool_executor = ToolExecutor(manager, anomaly_detector=anomaly_detector)
                
                # 5. Invoke Agent with task timeout guard
                try:
                    agent_thread = TaskExecThread(self.agent_adapter, task.input_prompt, tool_executor)
                    agent_thread.start()
                    agent_thread.join(timeout=timeout_seconds)
                    
                    if agent_thread.is_alive():
                        logger.warning(f"Task {task.task_id} timed out after {timeout_seconds}s. Terminating container...")
                        raise TaskTimeout(f"Task execution exceeded timeout limit of {timeout_seconds} seconds.")
                        
                    if agent_thread.exception:
                        raise agent_thread.exception
                        
                    agent_response = agent_thread.result
                except Exception as e:
                    if isinstance(e, ToolTimeout):
                        failure_reason = "TOOL_TIMEOUT"
                    elif isinstance(e, TaskTimeout):
                        failure_reason = "TASK_TIMEOUT"
                    elif isinstance(e, AnomalyException):
                        failure_reason = "LOOP_DETECTED" if e.pattern_type == "LOOP" else f"{e.pattern_type}_VIOLATION"
                        
                        # Commit Anomaly record to database immediately
                        if db_result_id:
                            from vigil.db.connection import get_session
                            from vigil.db.repository import VigilRepository
                            try:
                                with get_session() as session:
                                    VigilRepository.create_anomaly(
                                        session=session,
                                        task_result_id=db_result_id,
                                        pattern_type=e.pattern_type,
                                        severity=e.severity,
                                        incident_data=e.incident_data
                                    )
                            except Exception as db_err:
                                logger.error(f"Failed to log anomaly to database: {db_err}")
                    elif isinstance(e, AgentExecutionError):
                        failure_reason = "AGENT_EXECUTION_ERROR"
                    else:
                        failure_reason = "AGENT_EXECUTION_ERROR"
                    logger.error(f"Agent reasoning execution failed: {e}")
                    raise
                    
                # Cache tool executions
                tool_calls = tool_executor.tool_calls
                
                # 6. Scoring assertions
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
        except TaskTimeout as e:
            status = "ERROR"
            failure_reason = "TASK_TIMEOUT"
        except AnomalyException as e:
            status = "FAIL"
            failure_reason = "LOOP_DETECTED" if e.pattern_type == "LOOP" else f"{e.pattern_type}_VIOLATION"
        except AgentExecutionError as e:
            status = "ERROR"
            failure_reason = "AGENT_EXECUTION_ERROR"
        except Exception as e:
            logger.error(f"Unhandled operational exception in EvalRunner: {e}")
            status = "ERROR"
            if not failure_reason:
                failure_reason = "INTERNAL_FRAMEWORK_ERROR"
                
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        
        result_payload = {
            "task_id": task.task_id,
            "status": status,
            "failure_reason": failure_reason,
            "duration_ms": duration_ms,
            "agent_response": agent_response,
            "tool_calls": tool_calls,
            "assertion_results": assertion_results
        }
        
        # 7. Finalize/Update task run details in database if db_result_id is active
        if db_result_id:
            from vigil.db.connection import get_session
            from vigil.db.repository import VigilRepository
            
            try:
                with get_session() as session:
                    # Update TaskResult record status and telemetry metrics
                    VigilRepository.update_task_result(
                        session=session,
                        task_result_id=db_result_id,
                        status=status,
                        steps_taken=len(tool_calls),
                        failure_reason=failure_reason,
                        final_output=agent_response
                    )
                    
                    # Create individual ToolCall rows
                    for call in tool_calls:
                        input_args = {"command": call.arguments} if hasattr(call, "arguments") else {}
                        VigilRepository.create_tool_call(
                            session=session,
                            task_result_id=db_result_id,
                            sequence_number=call.sequence_number,
                            tool_name=call.tool_name,
                            input_args=input_args,
                            stdout_capture=call.stdout,
                            exit_code=call.exit_code,
                            duration_ms=call.duration_ms
                        )
            except Exception as e:
                logger.error(f"Failed database persistence finalization operations: {e}")
                if isinstance(e, DatabasePersistenceError):
                    raise e
                raise DatabasePersistenceError(f"Database finalization failed during run: {e}")
                
        return result_payload

    def run_suite(
        self, 
        task_dir: str, 
        suite_id: str = "suite-run", 
        name: str = "Suite Run", 
        agent_version: str = "develop",
        max_workers: int = 1
    ) -> list[dict[str, Any]]:
        """
        Loads and runs all YAML task definitions inside a target folder.
        Supports parallel execution up to 5 concurrent task workers (PRD §5).
        Saves execution telemetry and logs results to PostgreSQL.
        """
        from vigil.db.connection import get_session
        from vigil.db.repository import VigilRepository
        from vigil.eval.task_loader import TaskLoader
        import glob
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Enforce maximum concurrency cap of 5 as mandated by PRD §5
        workers = max(1, min(max_workers, 5))

        # 1. Initialize Database Run Metadata
        run_id = None
        db_suite_id = None
        try:
            with get_session() as session:
                db_suite = VigilRepository.get_or_create_suite(session, name, agent_version)
                db_suite_id = db_suite.id
                execution_config = {
                    "agent_version": agent_version,
                    "task_dir": task_dir,
                    "suite_id": suite_id,
                    "max_workers": workers
                }
                db_run = VigilRepository.create_eval_run(session, db_suite.id, execution_config)
                run_id = db_run.id
        except Exception as e:
            logger.error(f"Failed to initialize database run: {e}")
            if isinstance(e, DatabasePersistenceError):
                raise e
            raise DatabasePersistenceError(f"Database initialization failed: {e}")
            
        yaml_files = glob.glob(os.path.join(task_dir, "**/*.yaml"), recursive=True) + \
                     glob.glob(os.path.join(task_dir, "**/*.yml"), recursive=True)
                     
        yaml_files.sort()
        results = []
        suite_status = "COMPLETED"
        start_time = time.perf_counter()

        def _execute_task_file(idx_and_file: tuple[int, str]) -> tuple[int, dict[str, Any]]:
            idx, yaml_file = idx_and_file
            try:
                task_def = TaskLoader.load_task(yaml_file)
                
                with get_session() as session:
                    db_task = VigilRepository.get_or_create_task(session, task_def)
                    VigilRepository.associate_task_with_suite(session, db_suite_id, db_task.id, idx)
                    
                res = self.run_task(task_def, run_id=run_id)
                return idx, res
            except DatabasePersistenceError:
                raise
            except Exception as e:
                logger.error(f"Failed to load or execute task file {yaml_file}: {e}")
                err_res = {
                    "task_id": os.path.basename(yaml_file),
                    "status": "ERROR",
                    "failure_reason": "TASK_DEFINITION_VALIDATION_ERROR",
                    "error_details": str(e),
                    "duration_ms": 0,
                    "agent_response": "",
                    "tool_calls": [],
                    "assertion_results": {}
                }
                return idx, err_res
        
        try:
            indexed_files = list(enumerate(yaml_files, start=1))
            
            if workers == 1:
                # Sequential execution path
                indexed_results = [_execute_task_file(item) for item in indexed_files]
            else:
                # Parallel execution path using ThreadPoolExecutor capped at workers (max 5)
                logger.info(f"Executing suite {suite_id} with {workers} parallel workers")
                indexed_results = []
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    future_to_item = {executor.submit(_execute_task_file, item): item for item in indexed_files}
                    for future in as_completed(future_to_item):
                        indexed_results.append(future.result())
            
            # Sort results by original task index for deterministic reporting order
            indexed_results.sort(key=lambda x: x[0])
            results = [res for _, res in indexed_results]

            for res in results:
                if res["status"] in ["ERROR", "FAIL"]:
                    suite_status = "FAILED"

        finally:
            # 2. Finalize Database Run record
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            if run_id:
                try:
                    with get_session() as session:
                        VigilRepository.update_eval_run(session, run_id, suite_status, duration_ms)
                except Exception as e:
                    logger.error(f"Failed to update database run finalization: {e}")
                    if not isinstance(e, DatabasePersistenceError):
                        raise DatabasePersistenceError(f"Database finalization failed: {e}")
                    raise e
                    
        return results

