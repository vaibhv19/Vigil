import os
import shutil
import pytest
from typing import Any

from vigil.eval.task_models import TaskDefinition, ContextFile, TaskContext
from vigil.eval.assertion_models import FileExistsAssertion, FileContentMatchAssertion
from vigil.eval.runner import EvalRunner
from vigil.eval.reporter import VigilEvalReporter
from vigil.agents.base_adapter import BaseAgentAdapter
from vigil.core.tool_executor import ToolExecutor
from vigil.core.tool_models import ToolRequest
from vigil.core.exceptions import AgentExecutionError, ToolTimeout
from vigil.config import get_settings

class MockAgentForRunner(BaseAgentAdapter):
    """
    Mock agent adapter that performs different commands based on the test action.
    """
    def __init__(self, action: str = "success"):
        self.action = action
        
    def run_task(self, prompt: str, tool_executor: ToolExecutor) -> str:
        if self.action == "success":
            # Write valid hello.txt
            req = ToolRequest(
                tool_name="bash",
                arguments=["bash", "-c", "echo 'Vigil is active' > hello.txt"]
            )
            tool_executor.execute(req)
            return "Agent wrote hello.txt successfully."
            
        elif self.action == "fail_assertions":
            # Write invalid hello.txt
            req = ToolRequest(
                tool_name="bash",
                arguments=["bash", "-c", "echo 'Incorrect content' > hello.txt"]
            )
            tool_executor.execute(req)
            return "Agent wrote invalid content."
            
        elif self.action == "timeout":
            # Run command that will time out
            req = ToolRequest(
                tool_name="bash",
                arguments=["sleep", "10"],
                timeout_seconds=1
            )
            tool_executor.execute(req)
            return "Should have timed out."
            
        elif self.action == "crash":
            raise AgentExecutionError("Simulated agent reasoning crash.")
            
        return "Unknown action"


@pytest.fixture
def sample_task() -> TaskDefinition:
    return TaskDefinition(
        task_id="runner-integration-test",
        description="Verify end to end orchestrator flow.",
        input_prompt="Please write hello.txt containing Vigil is active.",
        category="file-ops",
        expected_output={
            "assertions": [
                FileExistsAssertion(type="file_exists", path="hello.txt"),
                FileContentMatchAssertion(
                    type="file_content_match", path="hello.txt", pattern="Vigil is active"
                )
            ]
        },
        context=TaskContext(files=[ContextFile(path="seed.txt", content="seed-data")])
    )


def test_eval_runner_success(sample_task):
    settings = get_settings()
    agent = MockAgentForRunner(action="success")
    runner = EvalRunner(agent, settings.WORKSPACE_BASE_DIR)
    
    # Run task
    result = runner.run_task(sample_task)
    
    assert result["task_id"] == sample_task.task_id
    assert result["status"] == "PASS"
    assert result["failure_reason"] is None
    assert len(result["tool_calls"]) == 1
    assert result["assertion_results"]["file_exists:{\"path\":\"hello.txt\"}"] is True
    assert result["assertion_results"]["file_content_match:{\"path\":\"hello.txt\",\"pattern\":\"Vigil is active\",\"strategy\":\"exact\"}"] is True

    # Test report generation
    reporter = VigilEvalReporter(output_dir="tests/scratch/reports")
    try:
        report_path = reporter.generate_report("test-suite-success", [result])
        assert os.path.exists(report_path)
    finally:
        if os.path.exists("tests/scratch/reports"):
            shutil.rmtree("tests/scratch/reports")


def test_eval_runner_assertion_failure(sample_task):
    settings = get_settings()
    agent = MockAgentForRunner(action="fail_assertions")
    runner = EvalRunner(agent, settings.WORKSPACE_BASE_DIR)
    
    # Run task
    result = runner.run_task(sample_task)
    
    assert result["task_id"] == sample_task.task_id
    assert result["status"] == "FAIL"
    assert result["failure_reason"] == "ASSERTION_FAILED"
    assert result["assertion_results"]["file_exists:{\"path\":\"hello.txt\"}"] is True
    # The file content check must fail
    assert result["assertion_results"]["file_content_match:{\"path\":\"hello.txt\",\"pattern\":\"Vigil is active\",\"strategy\":\"exact\"}"] is False


def test_eval_runner_timeout_error(sample_task):
    settings = get_settings()
    agent = MockAgentForRunner(action="timeout")
    runner = EvalRunner(agent, settings.WORKSPACE_BASE_DIR)
    
    # Run task (should catch ToolTimeout and raise status=ERROR)
    result = runner.run_task(sample_task)
    
    assert result["task_id"] == sample_task.task_id
    assert result["status"] == "ERROR"
    assert result["failure_reason"] == "TOOL_TIMEOUT"


def test_eval_runner_agent_crash_error(sample_task):
    settings = get_settings()
    agent = MockAgentForRunner(action="crash")
    runner = EvalRunner(agent, settings.WORKSPACE_BASE_DIR)
    
    # Run task (should catch AgentExecutionError and raise status=ERROR)
    result = runner.run_task(sample_task)
    
    assert result["task_id"] == sample_task.task_id
    assert result["status"] == "ERROR"
    assert result["failure_reason"] == "AGENT_EXECUTION_ERROR"
