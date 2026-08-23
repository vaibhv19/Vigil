import uuid
from typing import Optional

from vigil.core.tool_models import ToolRequest
from vigil.core.path_validator import PathValidationLayer
from vigil.core.subprocess_monitor import SubprocessAllowListScanner
from vigil.core.exceptions import AnomalyException

class AnomalyDetector:
    """
    Main monitoring layer inspecting agent actions prior to sandbox execution
    to detect execution loops, path escapes, or shell command subprocess bypasses.
    """
    def __init__(self, task_result_id: Optional[uuid.UUID], max_tool_calls: int):
        self.task_result_id = task_result_id
        self.max_tool_calls = max_tool_calls
        self.current_calls = 0

    def inspect_request(self, request: ToolRequest) -> None:
        """
        Inspects the incoming tool request for loop, path, or process violations.
        Raises AnomalyException if a violation is detected.
        """
        # 1. Loop Detection
        if self.current_calls >= self.max_tool_calls:
            raise AnomalyException(
                pattern_type="LOOP",
                severity="CRITICAL",
                incident_data={
                    "current_calls": self.current_calls,
                    "max_tool_calls": self.max_tool_calls
                },
                message=f"Execution loop detected! Tool calls exceeded limit of {self.max_tool_calls}."
            )
            
        self.current_calls += 1
        
        # 2. Path Validation Check
        PathValidationLayer.validate(request.arguments)
        
        # 3. Subprocess Allow-list Checks
        SubprocessAllowListScanner.scan(request.arguments)
