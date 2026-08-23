import time
import logging
import threading
from typing import Optional

from vigil.core.sandbox_manager import SandboxManager
from vigil.core.tool_models import ToolRequest, ToolResult
from vigil.core.exceptions import ToolExecutionError, ToolTimeout

logger = logging.getLogger(__name__)

class ExecutionTimer:
    """
    Context manager to measure durations in milliseconds using high-resolution performance counters.
    """
    def __enter__(self):
        self.start_ns = time.perf_counter_ns()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_ns = time.perf_counter_ns()
        self.duration_ms = (self.end_ns - self.start_ns) // 1_000_000


class TimeoutExecThread(threading.Thread):
    def __init__(self, container, command, environment, workdir):
        super().__init__()
        self.container = container
        self.command = command
        self.environment = environment
        self.workdir = workdir
        self.result = None
        self.exception = None
        
    def run(self):
        try:
            # Execute command inside container with demux=True to separate stdout/stderr
            self.result = self.container.exec_run(
                cmd=self.command,
                environment=self.environment,
                workdir=self.workdir,
                demux=True
            )
        except Exception as e:
            self.exception = e


class ToolExecutor:
    """
    Handles intercepting, timing, and routing commands to the running Docker container.
    """
    def __init__(self, sandbox_manager: SandboxManager, anomaly_detector: Optional[Any] = None):
        self.sandbox_manager = sandbox_manager
        self.anomaly_detector = anomaly_detector
        self._tool_calls = []
        self._sequence_number = 0

    @property
    def tool_calls(self) -> list[ToolResult]:
        """
        Historical execution logs for the current task.
        """
        return self._tool_calls

    def execute(self, request: ToolRequest) -> ToolResult:
        """
        Executes a command inside the running sandbox container with sub-timeout guards.
        """
        # Intercept and validate request prior to container execution
        if self.anomaly_detector:
            self.anomaly_detector.inspect_request(request)

        self._sequence_number += 1
        seq = self._sequence_number
        tool_name = request.tool_name
        
        # Verify container is active
        try:
            container = self.sandbox_manager._container
            if not container:
                raise ValueError("Container is not active.")
        except Exception as e:
            err_msg = f"No active container found to execute tool: {e}"
            logger.error(err_msg)
            res = ToolResult(
                sequence_number=seq,
                tool_name=tool_name,
                exit_code=None,
                stdout="",
                stderr=err_msg,
                duration_ms=0,
                status="ERROR"
            )
            self._tool_calls.append(res)
            raise ToolExecutionError(err_msg)

        # Enforce execution timeout
        timer = ExecutionTimer()
        thread = TimeoutExecThread(
            container=container,
            command=request.arguments,
            environment=request.env,
            workdir="/workspace"
        )
        
        with timer:
            thread.start()
            thread.join(timeout=request.timeout_seconds)
            
        if thread.is_alive():
            # Execution timed out! Kill the container and raise ToolTimeout.
            logger.warning(f"Tool execution {tool_name} (seq {seq}) timed out after {request.timeout_seconds}s. Killing container...")
            try:
                container.kill()
            except Exception as e:
                logger.error(f"Failed to kill timed-out container: {e}")
                
            res = ToolResult(
                sequence_number=seq,
                tool_name=tool_name,
                exit_code=None,
                stdout="",
                stderr=f"Tool execution exceeded timeout of {request.timeout_seconds} seconds.",
                duration_ms=timer.duration_ms,
                status="TIMEOUT"
            )
            self._tool_calls.append(res)
            raise ToolTimeout(f"Tool {tool_name} timed out after {request.timeout_seconds}s.")
            
        # If thread completed within timeout
        if thread.exception:
            err_msg = f"Docker exec exception: {thread.exception}"
            logger.error(err_msg)
            res = ToolResult(
                sequence_number=seq,
                tool_name=tool_name,
                exit_code=None,
                stdout="",
                stderr=err_msg,
                duration_ms=timer.duration_ms,
                status="ERROR"
            )
            self._tool_calls.append(res)
            raise ToolExecutionError(err_msg)
            
        # Parse result
        exec_res = thread.result
        exit_code = exec_res.exit_code
        stdout_bytes, stderr_bytes = exec_res.output
        
        stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
        stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
        
        res = ToolResult(
            sequence_number=seq,
            tool_name=tool_name,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=timer.duration_ms,
            status="SUCCESS"
        )
        self._tool_calls.append(res)
        return res
