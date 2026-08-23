import time
import pytest
import docker
from pydantic import ValidationError

from vigil.core.sandbox_config import SandboxConfig
from vigil.core.sandbox_manager import Sandbox
from vigil.core.tool_models import ToolRequest, ToolResult
from vigil.core.tool_executor import ToolExecutor, ExecutionTimer
from vigil.core.exceptions import ToolExecutionError, ToolTimeout
from vigil.config import get_settings

def test_tool_request_validation():
    # arguments is required and must be a list
    with pytest.raises(ValidationError):
        ToolRequest(tool_name="bash", arguments="not-a-list")
        
    req = ToolRequest(tool_name="bash", arguments=["ls", "-la"])
    assert req.tool_name == "bash"
    assert req.arguments == ["ls", "-la"]
    assert req.timeout_seconds == 30

def test_execution_timer():
    with ExecutionTimer() as timer:
        time.sleep(0.05)  # Sleep 50ms
    # Allowed delta check
    assert 40 <= timer.duration_ms <= 80

def test_successful_tool_execution():
    config = SandboxConfig()
    settings = get_settings()
    
    with Sandbox(config, settings.WORKSPACE_BASE_DIR, "test-exec-success") as manager:
        executor = ToolExecutor(manager)
        
        # Run a simple echo command
        req = ToolRequest(tool_name="bash", arguments=["echo", "Hello World"])
        result = executor.execute(req)
        
        assert result.sequence_number == 1
        assert result.tool_name == "bash"
        assert result.exit_code == 0
        assert result.stdout.strip() == "Hello World"
        assert result.stderr == ""
        assert result.status == "SUCCESS"
        assert result.duration_ms >= 0
        
        # Test historical calls logging
        assert len(executor.tool_calls) == 1
        assert executor.tool_calls[0] == result

def test_tool_timeout():
    config = SandboxConfig()
    settings = get_settings()
    
    with Sandbox(config, settings.WORKSPACE_BASE_DIR, "test-exec-timeout") as manager:
        executor = ToolExecutor(manager)
        
        # Run sleep 10 with 1s timeout
        req = ToolRequest(tool_name="bash", arguments=["sleep", "10"], timeout_seconds=1)
        
        with pytest.raises(ToolTimeout):
            executor.execute(req)
            
        assert len(executor.tool_calls) == 1
        assert executor.tool_calls[0].status == "TIMEOUT"
        
        # Since container was killed, trying to run another tool raises ToolExecutionError
        req2 = ToolRequest(tool_name="bash", arguments=["echo", "alive"])
        with pytest.raises(ToolExecutionError):
            executor.execute(req2)

def test_environment_variable_override():
    config = SandboxConfig()
    settings = get_settings()
    
    with Sandbox(config, settings.WORKSPACE_BASE_DIR, "test-env-override") as manager:
        executor = ToolExecutor(manager)
        
        # Run env command with overrides
        req = ToolRequest(
            tool_name="bash",
            arguments=["bash", "-c", "echo $CUSTOM_VAR"],
            env={"CUSTOM_VAR": "VigilOverrideValue"}
        )
        result = executor.execute(req)
        assert result.exit_code == 0
        assert result.stdout.strip() == "VigilOverrideValue"

def test_sequential_file_persistence():
    config = SandboxConfig()
    settings = get_settings()
    
    with Sandbox(config, settings.WORKSPACE_BASE_DIR, "test-persistence") as manager:
        executor = ToolExecutor(manager)
        
        # Step 1: Write file
        req_write = ToolRequest(
            tool_name="bash", 
            arguments=["bash", "-c", "echo 'Vigil State Persistence' > file.txt"]
        )
        res_write = executor.execute(req_write)
        assert res_write.sequence_number == 1
        assert res_write.exit_code == 0
        
        # Step 2: Append and read file
        req_read = ToolRequest(
            tool_name="bash",
            arguments=["cat", "file.txt"]
        )
        res_read = executor.execute(req_read)
        assert res_read.sequence_number == 2
        assert res_read.exit_code == 0
        assert res_read.stdout.strip() == "Vigil State Persistence"
