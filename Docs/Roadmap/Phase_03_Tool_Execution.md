# Phase 03: Tool Execution & Interception

## 1. Package / Folder Structure
```text
vigil/
├── core/
│   ├── __init__.py
│   ├── tool_models.py          # ToolRequest and ToolResult Pydantic models
│   ├── tool_executor.py        # Interception and routing of commands to Docker
│   └── exceptions.py           # Core exceptions (e.g. ToolExecutionError, ToolTimeout)
└── tests/
    ├── integration/
    │   └── test_tool_execution.py # Testing execution of commands inside the Docker sandbox
```

---

## 2. Purpose
This phase implements the execution routing mechanism. It abstracts how agent-generated tool calls (like executing Python scripts, running Bash commands, or reading/writing files) are intercepted on the host, structured into data models, timed, executed inside the running task container using Docker `exec_run()`, and recorded with stdout/stderr/exit codes.

---

## 3. Dependencies
### 3.1 Internal Modules
- `vigil.core.sandbox_manager` (To run commands inside the active container)
- `vigil.core.exceptions` (For structured error handling)

### 3.2 External Libraries
- `docker` (For container execution)
- `pydantic` (For requests/results schema validation)

---

## 4. Inputs
- `ToolRequest` DTO containing:
  - Command array (e.g. `["python", "-c", "print('hello')"]`).
  - Timeout limit for this specific tool call (default: 30s).
  - Environment overrides for the execution environment.

---

## 5. Outputs
- `ToolResult` DTO containing:
  - Sequence number (order of tool execution in the task).
  - Exit code.
  - Captured stdout text.
  - Captured stderr text.
  - Duration in milliseconds.
  - Status flag (success, timeout, failure).

---

## 6. Public Interfaces
### 6.1 Tool Models (`vigil/core/tool_models.py`)
```python
from pydantic import BaseModel, Field
from typing import Optional, Any

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
```

### 6.2 Tool Executor Interface (`vigil/core/tool_executor.py`)
```python
from vigil.core.sandbox_manager import SandboxManager

class ToolExecutor:
    def __init__(self, sandbox_manager: SandboxManager): ...
    def execute(self, request: ToolRequest) -> ToolResult: ...
    @property
    def tool_calls(self) -> list[ToolResult]: ... # Historical execution logs for current task
```

---

## 7. Internal Components
- **`ExecutionTimer`**: Context manager wrapping execution to measure durations in milliseconds using high-resolution performance counters (`time.perf_counter_ns`).
- **`SequenceTracker`**: State tracker managing sequential IDs for execution logs.
- **`TimeoutGuard`**: Thread/process timer to enforce sub-timeouts and trigger `docker kill` if the process hangs.

---

## 8. Development Prerequisites & Environment Bootstrap Checklist
- [ ] **Phase 2 Sandbox working**: Ensure that `SandboxManager` is fully operational and verified by integration tests.
- [ ] **Docker Socket writable**: The harness must be able to run commands asynchronously.

---

## 9. Atomic Implementation Task List

| Task ID | Description | Size | Risk | Prerequisites | Dependencies | Expected Output | Testing | Definition of Done |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **TS-3.1** | Define core system exceptions (`ToolExecutionError`, `ToolTimeout`). | S | Low | TS-1.4 | None | Python exception classes matching design. | Write tests ensuring exception construction and serialization. | Exceptions represent clean hierarchy matching the specifications. |
| **TS-3.2** | Implement Pydantic validation models `ToolRequest` and `ToolResult`. | S | Low | TS-2.2 | None | Robust models for serializing request parameters. | Unit test verifying invalid tool inputs are flagged. | Pydantic validation succeeds for valid fields. |
| **TS-3.3** | Implement `ExecutionTimer` capturing high-resolution durations. | S | Low | TS-1.6 | None | Simple context manager recording elapsed milliseconds. | Test validating timed sleep matches actual output. | Millisecond duration is captured accurately within 5ms. |
| **TS-3.4** | Implement execution routing inside `ToolExecutor.execute` using `container.exec_run`. | M | Med | TS-2.6, TS-3.2 | None | Synchronous invocation executing inside container workspace. | Run command, verify stdout/stderr captures. | Exec runs inside `/workspace` with environment overrides. |
| **TS-3.5** | Implement `TimeoutGuard` enforcing tool timeouts (e.g. 30s limits). | M | High | TS-3.4 | TS-3.1 | Process is aborted and `ToolTimeout` is raised. | Test running `sleep 40` with 2s timeout. Verify exit. | Process terminates and releases connection cleanly. |
| **TS-3.6** | Implement `SequenceTracker` maintaining tool call order. | S | Low | TS-3.2 | None | 1-indexed numbers appended to successive results. | Test triggering multiple tools and verifying serial increments. | Increments sequentially from 1 for every call in a task run. |
| **TS-3.7** | Create integration test verifying sequential file modification. | M | Low | TS-3.4, TS-3.6 | None | Sequential execution changes file; terminal state validates successfully. | Test creates file in step 1, reads/writes in step 2. | File state persists across sequential container calls. |

---

## 10. Definition of Done (DoD)
- Tool execution models parse and validate requests/results.
- `ToolExecutor` executes commands inside the running sandbox container.
- Command execution tracks stdout, stderr, exit codes, and durations.
- Tool timeouts are enforced, halting runaway processes inside the container without terminating the host harness.
- State in `/workspace` is verified to persist between multiple tool executions within the same sandbox session.
- Full test suite passes.
