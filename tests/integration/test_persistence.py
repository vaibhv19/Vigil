import pytest
import os
import uuid
import shutil
from sqlalchemy import select

from vigil.db.connection import get_session
from vigil.db.models import EvalSuite, Task, EvalSuiteTask, EvalRun, TaskResult, ToolCall
from vigil.db.repository import VigilRepository
from vigil.core.exceptions import DatabasePersistenceError
from vigil.eval.runner import EvalRunner
from vigil.agents.base_adapter import BaseAgentAdapter
from vigil.core.tool_executor import ToolExecutor
from vigil.core.tool_models import ToolRequest
from vigil.config import get_settings

class SimpleMockAgent(BaseAgentAdapter):
    """
    Mock agent that prints a message to verify database tool call logs.
    """
    def run_task(self, prompt: str, tool_executor: ToolExecutor) -> str:
        req = ToolRequest(
            tool_name="bash",
            arguments=["echo", "Persistence Checked"]
        )
        tool_executor.execute(req)
        return "Agent output text."


def test_database_orm_and_repository():
    """
    Test direct saving and foreign key linkages via repository class.
    """
    with get_session() as session:
        # Create Suite
        suite = VigilRepository.get_or_create_suite(session, "test-suite", "v1.0.0")
        assert suite.id is not None
        
        # Create Task definition and model
        from vigil.eval.task_models import TaskDefinition
        task_def = TaskDefinition(
            task_id="persistence-test-task",
            description="Persistence test desc",
            input_prompt="Persistence prompt",
            category="db-ops",
            expected_output={"assertions": []}
        )
        task = VigilRepository.get_or_create_task(session, task_def)
        assert task.id is not None
        
        # Associate Task with Suite
        assoc = VigilRepository.associate_task_with_suite(session, suite.id, task.id, 1)
        assert assoc.suite_id == suite.id
        assert assoc.task_id == task.id
        
        # Create Run
        run = VigilRepository.create_eval_run(session, suite.id, {"env": "test"})
        assert run.id is not None
        assert run.status == "RUNNING"
        
        # Create TaskResult
        result = VigilRepository.create_task_result(
            session=session,
            run_id=run.id,
            task_id=task.id,
            status="PASS",
            steps_taken=1,
            final_output="Output payload"
        )
        assert result.id is not None
        assert result.status == "PASS"
        
        # Create ToolCall
        call = VigilRepository.create_tool_call(
            session=session,
            task_result_id=result.id,
            sequence_number=1,
            tool_name="bash",
            input_args={"cmd": "echo"},
            stdout_capture="Stdout content",
            exit_code=0,
            duration_ms=45
        )
        assert call.id is not None
        assert call.task_result_id == result.id

        # Update Run
        updated_run = VigilRepository.update_eval_run(session, run.id, "COMPLETED", 1500)
        assert updated_run.status == "COMPLETED"
        assert updated_run.total_duration_ms == 1500


def test_eval_runner_suite_persistence():
    """
    Verify EvalRunner suite execution automatically persists all metadata, runs, task results, and tool calls.
    """
    settings = get_settings()
    agent = SimpleMockAgent()
    runner = EvalRunner(agent, settings.WORKSPACE_BASE_DIR)
    
    # Run suite over task YAML fixture directory
    results = runner.run_suite(
        task_dir="tests/fixtures/tasks",
        suite_id="integration-persistence-suite",
        name="Persistence Verification Suite",
        agent_version="v2.0.0-test"
    )
    
    assert len(results) >= 1
    
    # Verify records exist in PostgreSQL
    with get_session() as session:
        # Check Suite
        stmt_suite = select(EvalSuite).where(EvalSuite.name == "Persistence Verification Suite")
        suite = session.scalar(stmt_suite)
        assert suite is not None
        assert suite.agent_version == "v2.0.0-test"
        
        # Check Run
        stmt_run = select(EvalRun).where(EvalRun.suite_id == suite.id)
        run = session.scalar(stmt_run)
        assert run is not None
        assert run.status in ["COMPLETED", "FAILED"]
        
        # Check TaskResult
        stmt_res = select(TaskResult).where(TaskResult.run_id == run.id)
        task_results = session.scalars(stmt_res).all()
        assert len(task_results) >= 1
        
        # Check ToolCall
        stmt_call = select(ToolCall).where(ToolCall.task_result_id == task_results[0].id)
        tool_calls = session.scalars(stmt_call).all()
        assert len(tool_calls) >= 1


def test_persistence_failure_raises_error():
    """
    Verify database connection failures correctly raise DatabasePersistenceError and abort suite runs.
    """
    # Force a broken database connection URL by overriding settings
    from vigil.config import get_settings
    
    old_db_url = os.environ.get("DATABASE_URL")
    
    try:
        # Override to point to non-existent DB
        os.environ["DATABASE_URL"] = "postgresql://invalid_user:invalid_pass@localhost:9999/invalid_db"
        get_settings.cache_clear()
        
        # Recreate connections singleton caches to force connection attempt
        import vigil.db.connection
        vigil.db.connection._engine = None
        vigil.db.connection._SessionFactory = None
        
        agent = SimpleMockAgent()
        settings = get_settings()
        runner = EvalRunner(agent, settings.WORKSPACE_BASE_DIR)
        
        with pytest.raises(DatabasePersistenceError):
            runner.run_suite("tests/fixtures/tasks")
            
    finally:
        # Restore old database config URL
        if old_db_url:
            os.environ["DATABASE_URL"] = old_db_url
        else:
            os.environ.pop("DATABASE_URL", None)
            
        get_settings.cache_clear()
        import vigil.db.connection
        vigil.db.connection._engine = None
        vigil.db.connection._SessionFactory = None
