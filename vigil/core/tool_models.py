from pydantic import BaseModel, Field
from typing import Optional

class ToolRequest(BaseModel):
    tool_name: str = Field(..., description="Name of the tool requested (e.g. bash, python_exec)")
    arguments: list[str] = Field(..., description="Arguments/command array to pass to exec_run")
    timeout_seconds: int = Field(default=30, description="Max execution time for this specific call")
    env: dict[str, str] = Field(default_factory=dict, description="Exec-specific environment overrides")

class ToolResult(BaseModel):
    sequence_number: int = Field(..., description="1-indexed sequence order")
    tool_name: str = Field(..., description="Name of the executed tool")
    exit_code: Optional[int] = Field(None, description="Exit code returned by the container process")
    stdout: str = Field(default="", description="Captured stdout stream")
    stderr: str = Field(default="", description="Captured stderr stream")
    duration_ms: int = Field(..., description="Execution duration in milliseconds")
    status: str = Field(..., description="Execution status: SUCCESS, TIMEOUT, ERROR")
