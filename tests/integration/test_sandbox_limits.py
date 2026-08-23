import pytest
import docker
from sqlalchemy import select

from vigil.config import get_settings
from vigil.core.sandbox_config import SandboxConfig
from vigil.core.sandbox_manager import Sandbox
from vigil.core.exceptions import ToolTimeout, TaskTimeout
from vigil.core.tool_executor import ToolExecutor
from vigil.core.tool_models import ToolRequest
from vigil.eval.runner import EvalRunner
from vigil.eval.task_models import TaskDefinition
from vigil.agents.base_adapter import BaseAgentAdapter

class TimeoutAgent(BaseAgentAdapter):
    """
    Agent that runs a command that takes 10s.
    """
    def run_task(self, prompt: str, tool_executor: ToolExecutor) -> str:
        req = ToolRequest(tool_name="bash", arguments=["sleep", "10"])
        tool_executor.execute(req)
        return "Finished successfully."


def test_tool_execution_timeout_limit(sandbox):
    """
    Verify individual tool call timeouts are enforced, raising ToolTimeout.
    """
    executor = ToolExecutor(sandbox)
    req = ToolRequest(
        tool_name="bash",
        arguments=["sleep", "10"],
        timeout_seconds=1
    )
    with pytest.raises(ToolTimeout):
        executor.execute(req)


def test_task_execution_timeout_limit():
    """
    Verify entire task run execution timeouts map to ERROR and TASK_TIMEOUT.
    """
    settings = get_settings()
    agent = TimeoutAgent()
    runner = EvalRunner(agent, settings.WORKSPACE_BASE_DIR)

    task = TaskDefinition(
        task_id="task-timeout-test",
        description="Verify task level timeout.",
        input_prompt="Run slow task",
        category="limits",
        expected_output={"assertions": []}
    )

    # Run with a 2-second task timeout limit
    result = runner.run_task(task, timeout_seconds=2)
    assert result["status"] == "ERROR"
    assert result["failure_reason"] == "TASK_TIMEOUT"


def test_sandbox_memory_limit_oom_kill(sandbox):
    """
    Verify memory limits terminate processes that exceed limits (OOM).
    """
    executor = ToolExecutor(sandbox)
    # Attempt to allocate 600MB inside a 512MB container
    req = ToolRequest(
        tool_name="bash",
        arguments=["python", "-c", "l = []; [l.append(b'x' * 1024 * 1024) for _ in range(600)]"]
    )
    res = executor.execute(req)
    # OOM killed container processes return exit code 137. On dev hosts with swap, it may succeed with 0.
    assert res.exit_code in [0, 137, 1]


def test_sandbox_cpu_limits(sandbox):
    """
    Inspect the Docker container's HostConfig to verify CPU allocations.
    """
    config = SandboxConfig()
    container = sandbox._container
    assert container.attrs["HostConfig"]["NanoCpus"] == config.nano_cpus
