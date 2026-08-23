import uuid
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from vigil.db.models import EvalSuite, Task, EvalSuiteTask, EvalRun, TaskResult, ToolCall, Anomaly
from vigil.eval.task_models import TaskDefinition

class VigilRepository:
    """
    Data Access Object (DAO) providing helper routines to query and persist
    evaluation suite metadata, tasks definitions, runs telemetry, and logs.
    """
    @staticmethod
    def get_or_create_suite(session: Session, name: str, agent_version: str) -> EvalSuite:
        stmt = select(EvalSuite).where(EvalSuite.name == name, EvalSuite.agent_version == agent_version)
        suite = session.scalar(stmt)
        if not suite:
            suite = EvalSuite(name=name, agent_version=agent_version)
            session.add(suite)
            session.flush()  # Populates auto-generated ID
        return suite

    @staticmethod
    def get_or_create_task(session: Session, task_def: TaskDefinition) -> Task:
        stmt = select(Task).where(Task.slug == task_def.task_id)
        task = session.scalar(stmt)
        if not task:
            # Serialize expected output models to JSON-compatible dictionaries
            expected_output_dump = {
                k: [a.model_dump() for a in v] for k, v in task_def.expected_output.items()
            }
            task = Task(
                slug=task_def.task_id,
                description=task_def.description,
                input_prompt=task_def.input_prompt,
                expected_output=expected_output_dump,
                max_steps=task_def.max_steps,
                category=task_def.category
            )
            session.add(task)
            session.flush()
        return task

    @staticmethod
    def associate_task_with_suite(session: Session, suite_id: uuid.UUID, task_id: uuid.UUID, execution_order: int) -> EvalSuiteTask:
        stmt = select(EvalSuiteTask).where(EvalSuiteTask.suite_id == suite_id, EvalSuiteTask.task_id == task_id)
        association = session.scalar(stmt)
        if not association:
            association = EvalSuiteTask(suite_id=suite_id, task_id=task_id, execution_order=execution_order)
            session.add(association)
            session.flush()
        return association

    @staticmethod
    def create_eval_run(session: Session, suite_id: uuid.UUID, execution_config: Dict[str, Any]) -> EvalRun:
        run = EvalRun(
            suite_id=suite_id,
            status="RUNNING",
            execution_config=execution_config
        )
        session.add(run)
        session.flush()
        return run

    @staticmethod
    def update_eval_run(session: Session, run_id: uuid.UUID, status: str, total_duration_ms: int, total_cost: float = 0.0) -> EvalRun:
        stmt = select(EvalRun).where(EvalRun.id == run_id)
        run = session.scalar(stmt)
        if not run:
            raise ValueError(f"EvalRun not found: {run_id}")
        run.status = status
        run.total_duration_ms = total_duration_ms
        run.total_cost = total_cost
        run.finished_at = datetime.now(timezone.utc)
        session.add(run)
        session.flush()
        return run

    @staticmethod
    def create_task_result(
        session: Session, 
        run_id: uuid.UUID, 
        task_id: uuid.UUID, 
        status: str, 
        steps_taken: int, 
        failure_reason: Optional[str] = None, 
        final_output: Optional[str] = None
    ) -> TaskResult:
        result = TaskResult(
            run_id=run_id,
            task_id=task_id,
            status=status,
            steps_taken=steps_taken,
            failure_reason=failure_reason,
            final_output=final_output,
            finished_at=datetime.now(timezone.utc)
        )
        session.add(result)
        session.flush()
        return result

    @staticmethod
    def update_task_result(
        session: Session,
        task_result_id: uuid.UUID,
        status: str,
        steps_taken: int,
        failure_reason: Optional[str] = None,
        final_output: Optional[str] = None
    ) -> TaskResult:
        stmt = select(TaskResult).where(TaskResult.id == task_result_id)
        result = session.scalar(stmt)
        if not result:
            raise ValueError(f"TaskResult not found: {task_result_id}")
        result.status = status
        result.steps_taken = steps_taken
        result.failure_reason = failure_reason
        result.final_output = final_output
        result.finished_at = datetime.now(timezone.utc)
        session.add(result)
        session.flush()
        return result

    @staticmethod
    def create_tool_call(
        session: Session,
        task_result_id: uuid.UUID,
        sequence_number: int,
        tool_name: str,
        input_args: Dict[str, Any],
        stdout_capture: str,
        exit_code: Optional[int],
        duration_ms: int
    ) -> ToolCall:
        tool_call = ToolCall(
            task_result_id=task_result_id,
            sequence_number=sequence_number,
            tool_name=tool_name,
            input_args=input_args,
            stdout_capture=stdout_capture,
            exit_code=exit_code,
            duration_ms=duration_ms
        )
        session.add(tool_call)
        session.flush()
        return tool_call

    @staticmethod
    def create_anomaly(
        session: Session,
        task_result_id: uuid.UUID,
        pattern_type: str,
        severity: str,
        incident_data: Dict[str, Any]
    ) -> Anomaly:
        anomaly = Anomaly(
            task_result_id=task_result_id,
            pattern_type=pattern_type,
            severity=severity,
            incident_data=incident_data
        )
        session.add(anomaly)
        session.flush()
        return anomaly
