import os
import uuid
import pytest
from sqlalchemy import select

from vigil.db.connection import get_session
from vigil.db.models import EvalSuite, EvalRun, TaskResult, ToolCall
from vigil.eval.task_models import TaskDefinition, TaskContext, ContextFile
from vigil.eval.assertion_models import FileExistsAssertion, FileContentMatchAssertion
from vigil.eval.runner import EvalRunner
from vigil.agents.base_adapter import BaseAgentAdapter
from vigil.core.tool_executor import ToolExecutor
from vigil.core.tool_models import ToolRequest
from vigil.config import get_settings

class HappyAgent(BaseAgentAdapter):
    """
    Agent that reads a seeded file and writes a result file.
    """
    def run_task(self, prompt: str, tool_executor: ToolExecutor) -> str:
        # Step 1: Read seeded file
        req_read = ToolRequest(tool_name="bash", arguments=["cat", "seed.txt"])
        res_read = tool_executor.execute(req_read)
        
        # Step 2: Write output file
        req_write = ToolRequest(
            tool_name="bash", 
            arguments=["bash", "-c", "echo 'Vigil E2E verified' > result.txt"]
        )
        tool_executor.execute(req_write)
        return f"Processed content: {res_read.stdout.strip()}"

def test_e2e_happy_path_success():
    settings = get_settings()
    agent = HappyAgent()
    runner = EvalRunner(agent, settings.WORKSPACE_BASE_DIR)
    
    task = TaskDefinition(
        task_id="e2e-happy-path-task",
        description="Verify full end-to-end happy path execution.",
        input_prompt="Read seed.txt and write result.txt.",
        category="e2e",
        expected_output={
            "assertions": [
                FileExistsAssertion(type="file_exists", path="result.txt"),
                FileContentMatchAssertion(type="file_content_match", path="result.txt", pattern="Vigil E2E verified")
            ]
        },
        context=TaskContext(files=[ContextFile(path="seed.txt", content="seed-payload")])
    )
    
    # Create DB run metadata
    with get_session() as session:
        from vigil.db.repository import VigilRepository
        suite = VigilRepository.get_or_create_suite(session, "e2e-happy-suite", "v1.0.0-happy")
        run = VigilRepository.create_eval_run(session, suite.id, {"test": "happy"})
        run_id = run.id
        
    result = runner.run_task(task, run_id=run_id)
    
    assert result["status"] == "PASS"
    assert result["failure_reason"] is None
    assert len(result["tool_calls"]) == 2
    
    # Verify records committed to PostgreSQL
    with get_session() as session:
        stmt_res = select(TaskResult).where(TaskResult.run_id == run_id)
        db_res = session.scalar(stmt_res)
        assert db_res is not None
        assert db_res.status == "PASS"
        assert db_res.steps_taken == 2
        assert "Processed content: seed-payload" in db_res.final_output
        
        # Verify Tool Calls list
        stmt_calls = select(ToolCall).where(ToolCall.task_result_id == db_res.id).order_by(ToolCall.sequence_number)
        db_calls = session.scalars(stmt_calls).all()
        assert len(db_calls) == 2
        assert db_calls[0].sequence_number == 1
        assert db_calls[0].tool_name == "bash"
        assert db_calls[0].stdout_capture.strip() == "seed-payload"
        assert db_calls[1].sequence_number == 2
        assert db_calls[1].tool_name == "bash"
