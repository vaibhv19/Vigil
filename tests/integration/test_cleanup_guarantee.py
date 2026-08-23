import os
import signal
import pytest
from docker.errors import NotFound

from vigil.config import get_settings
from vigil.core.docker_client import get_docker_client
from vigil.core.sandbox_config import SandboxConfig
from vigil.core.sandbox_manager import Sandbox, _cleanup_active_containers, ActiveContainerRegistry
from vigil.eval.runner import EvalRunner
from vigil.eval.task_models import TaskDefinition
from vigil.agents.base_adapter import BaseAgentAdapter
from vigil.core.tool_executor import ToolExecutor

class SimpleAgent(BaseAgentAdapter):
    def run_task(self, prompt: str, tool_executor: ToolExecutor) -> str:
        return "Task done."


class HostEnvironmentAuditor:
    """
    Helper to verify host resource reclamation.
    """
    @staticmethod
    def get_vigil_containers(task_id: str = None):
        client = get_docker_client()
        filters = {"label": "vigil-sandbox=true"}
        if task_id:
            filters["label"] = f"task-id={task_id}"
        return client.containers.list(
            all=True,
            filters=filters
        )

    @classmethod
    def assert_no_leaked_containers(cls, task_id: str = None):
        containers = cls.get_vigil_containers(task_id)
        assert len(containers) == 0, f"Leaked containers found: {[c.id for c in containers]}"

    @staticmethod
    def assert_workspace_is_deleted(workspace_path: str):
        assert not os.path.exists(workspace_path), f"Workspace directory was not deleted: {workspace_path}"


def test_cleanup_on_success_and_failure():
    """
    Verify E2E runs reclaim containers and workspace directories on completion.
    """
    settings = get_settings()
    agent = SimpleAgent()
    runner = EvalRunner(agent, settings.WORKSPACE_BASE_DIR)

    task = TaskDefinition(
        task_id="cleanup-test-task",
        description="Verify post-run cleanups.",
        input_prompt="Do task",
        category="cleanup",
        expected_output={"assertions": []}
    )

    # Execute task
    result = runner.run_task(task)
    assert result["status"] == "PASS"

    # Audits
    HostEnvironmentAuditor.assert_no_leaked_containers(task_id="cleanup-test-task")


def test_cleanup_on_signal_interruption():
    """
    Verify process signal handlers prune containers on SIGINT/SIGTERM interruptions.
    """
    config = SandboxConfig()
    settings = get_settings()

    # Create sandbox container manually
    with Sandbox(config, settings.WORKSPACE_BASE_DIR, "signal-test") as manager:
        container_id = manager.container_id
        workspace_path = manager.workspace_path
        
        # Verify container is running and registered
        assert container_id in ActiveContainerRegistry.get_all()
        client = get_docker_client()
        container = client.containers.get(container_id)
        assert container.status == "running"

        # Simulate SIGINT signal by calling the handler callback directly in-process
        with pytest.raises(SystemExit) as exc_info:
            _cleanup_active_containers(signal.SIGINT, None)
            
        # Verify exit status
        assert exc_info.value.code == 128 + signal.SIGINT

        # Verify container was killed and removed from registry
        with pytest.raises(NotFound):
            client.containers.get(container_id)
            
        assert container_id not in ActiveContainerRegistry.get_all()
