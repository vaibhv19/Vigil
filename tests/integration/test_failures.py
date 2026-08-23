import pytest
from pydantic import ValidationError
from sqlalchemy import select

from vigil.db.connection import get_session
from vigil.db.models import TaskResult
from vigil.eval.task_loader import TaskLoader
from vigil.eval.task_models import TaskDefinition
from vigil.eval.assertion_models import FileExistsAssertion
from vigil.eval.runner import EvalRunner
from vigil.core.exceptions import TaskDefinitionValidationError
from vigil.agents.base_adapter import BaseAgentAdapter
from vigil.core.tool_executor import ToolExecutor
from vigil.core.tool_models import ToolRequest
from vigil.config import get_settings

class FailureAgent(BaseAgentAdapter):
    """
    Agent that triggers failures or returns exit codes.
    """
    def __init__(self, action: str):
        self.action = action

    def run_task(self, prompt: str, tool_executor: ToolExecutor) -> str:
        if self.action == "non_zero_exit":
            req = ToolRequest(tool_name="bash", arguments=["bash", "-c", "exit 5"])
            tool_executor.execute(req)
            return "Command exited with non-zero code."
        elif self.action == "do_nothing":
            return "Agent did nothing."
        return "Unknown action"


def test_invalid_task_definitions():
    """
    Verify Loader rejects malformed task schemas.
    """
    # Verify parsing raises TaskDefinitionValidationError on bad input
    with pytest.raises(TaskDefinitionValidationError):
        TaskLoader.load_task("tests/fixtures/tasks/invalid_task.yaml")


def test_tool_execution_failure_exit_codes():
    """
    Verify command non-zero exit codes are captured successfully without crashing the harness.
    """
    settings = get_settings()
    agent = FailureAgent(action="non_zero_exit")
    runner = EvalRunner(agent, settings.WORKSPACE_BASE_DIR)

    task = TaskDefinition(
        task_id="non-zero-exit-task",
        description="Verify exit code mapping.",
        input_prompt="Run command",
        category="failures",
        expected_output={"assertions": []}
    )

    result = runner.run_task(task)
    assert result["status"] == "PASS"  # Empty assertions pass
    assert len(result["tool_calls"]) == 1
    assert result["tool_calls"][0].exit_code == 5
    assert result["tool_calls"][0].status == "SUCCESS"  # The execution itself completed successfully


def test_assertion_scoring_failures():
    """
    Verify scoring engine correctly maps failed conditions to FAIL and logs ASSERTION_FAILED.
    """
    settings = get_settings()
    agent = FailureAgent(action="do_nothing")
    runner = EvalRunner(agent, settings.WORKSPACE_BASE_DIR)

    task = TaskDefinition(
        task_id="assertion-fail-task",
        description="Verify assertion fails when condition not met.",
        input_prompt="Create file",
        category="failures",
        expected_output={
            "assertions": [
                FileExistsAssertion(type="file_exists", path="ok.txt")
            ]
        }
    )

    with get_session() as session:
        from vigil.db.repository import VigilRepository
        suite = VigilRepository.get_or_create_suite(session, "failures-suite", "v1.0.0")
        run = VigilRepository.create_eval_run(session, suite.id, {})
        run_id = run.id

    result = runner.run_task(task, run_id=run_id)
    assert result["status"] == "FAIL"
    assert result["failure_reason"] == "ASSERTION_FAILED"

    # Verify database record
    with get_session() as session:
        stmt = select(TaskResult).where(TaskResult.run_id == run_id)
        db_res = session.scalar(stmt)
        assert db_res is not None
        assert db_res.status == "FAIL"
        assert db_res.failure_reason == "ASSERTION_FAILED"
