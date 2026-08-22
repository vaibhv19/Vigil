# Phase 10: Anomaly Detection

## 1. Package / Folder Structure
```text
vigil/
├── core/
│   ├── anomaly_detector.py     # Main monitoring loop validator
│   ├── path_validator.py       # Command argument path scanners
│   └── subprocess_monitor.py   # Shell command subprocess checkers
└── tests/
    └── integration/
        └── test_anomalies.py   # Integration tests for loop, path, and process anomalies
```

---

## 2. Purpose
This phase builds the monitoring layer. It intercepts agent actions prior to sandbox execution to detect three specific agentic failure modes: excessive tool loops (LOOP), attempted write access outside the mounted `/workspace` (PATH), and attempts to spawn unauthorized shell commands or subprocesses (PROCESS). Detected violations trigger a safe container teardown, log the event as an anomaly in the database, and fail the task.

---

## 3. Dependencies
### 3.1 Internal Modules
- `vigil.core.tool_models` (To intercept execution parameters)
- `vigil.core.sandbox_manager` (To terminate containers on CRITICAL anomalies)
- `vigil.db.connection` (To log anomalies to the database)

### 3.2 External Libraries
- `pydantic` (To structure anomaly payloads)
- `sqlmodel` / `sqlalchemy` (For DB insertions)

---

## 4. Inputs
- Command argument arrays intercepted from the agent's tool requests.
- Current task state logs (tool counts, elapsed iterations).
- Active allow-list rules per tool (e.g. process rules).

---

## 5. Outputs
- Saved rows in the `anomalies` table linking to the offending task result.
- `AnomalyException` raised on the host to abort task execution immediately.
- Container teardown calls to reclaim host resources.

---

## 6. Public Interfaces
### 6.1 Anomaly Monitoring Engine (`vigil/core/anomaly_detector.py`)
```python
from typing import Any
from vigil.core.tool_models import ToolRequest

class AnomalyDetector:
    def __init__(self, task_result_id: str, max_tool_calls: int):
        self.task_result_id = task_result_id
        self.max_tool_calls = max_tool_calls
        self.current_calls = 0

    def inspect_request(self, request: ToolRequest) -> None:
        """
        Inspects the incoming tool request for loop, path, or process violations.
        Raises AnomalyException if a violation is detected.
        """
        pass
```

### 6.2 Anomaly Models and Exceptions (`vigil/core/exceptions.py`)
- `AnomalyException`: Base exception containing:
  - `pattern_type`: `LOOP` | `PATH` | `PROCESS`
  - `severity`: `WARNING` | `CRITICAL`
  - `incident_data`: Structured dict with parameters (e.g., offending commands).

---

## 7. Internal Components
- **`PathValidationLayer`**: Command argument parser checking for directory traversal elements (e.g. `..`) or absolute paths pointing outside `/workspace`.
- **`SubprocessAllowListScanner`**: Scans command strings for shell metacharacters (e.g., `|`, `;`, `&`, `$` or backticks) that spawn subprocesses (e.g. `curl`, `nc`, `ssh`), unless explicitly allowed by the tool rules.

---

## 8. Development Prerequisites & Environment Bootstrap Checklist
- [ ] **Phase 8 verified**: Core framework is stable and persistence is functional.
- [ ] **Sample anomaly tasks**: Prepare YAML test files with inputs designed to trigger loop, path, and process violations.

---

## 9. Atomic Implementation Task List

| Task ID | Description | Size | Risk | Prerequisites | Dependencies | Expected Output | Testing | Definition of Done |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **TS-10.1** | Define `AnomalyException` class and structured database types. | S | Low | TS-3.1, TS-7.2 | None | Python exception mapping fields matching database fields. | Write serialization test checks. | Exception models validate successfully. |
| **TS-10.2** | Implement Tool Execution Loop Tracker monitoring `max_tool_calls`. | S | Low | TS-3.6 | None | Exception raised when agent executions exceed limit. | Test running dummy task loop with `max_steps=5`, verify exit. | Exception is thrown and execution stops. |
| **TS-10.3** | Implement pre-execution path validator (`PathValidationLayer`). | M | Med | TS-3.4 | None | Block commands traversing outside workspace (e.g., `/etc/`). | Test commands containing traversal paths (`../../etc/`). | Path attempts are flagged before running in the container. |
| **TS-10.4** | Implement subprocess monitor scanning command strings for shell escapes. | M | Med | TS-3.4 | None | Blocks shell spawns or metacharacters (`nc`, `curl`). | Test command executions containing nested commands (`echo $()`, `;`). | Unauthorized processes are flagged and blocked. |
| **TS-10.5** | Implement container teardown logic on anomaly interception. | S | Low | TS-2.7, TS-10.1 | None | Sandbox is terminated and cleared when anomaly is triggered. | Trigger path violation, verify container is killed immediately. | Sandbox is closed, resource leaks are prevented. |
| **TS-10.6** | Implement database logger committing anomaly incidents. | S | Low | TS-7.6, TS-10.1 | None | Records inserted into the `anomalies` table with details. | Query db after anomaly, check `pattern_type` and `incident_data`. | DB commits save details (offending command, paths). |
| **TS-10.7** | Create integration suite verifying anomaly execution paths. | M | Med | TS-10.2, TS-10.3, TS-10.4 | None | Task exits with `FAILED` status, logging the anomaly. | Execute agent task requesting path escape, check table counts. | Complete loop, path, and process anomaly lifecycle works cleanly. |

---

## 10. Definition of Done (DoD)
- Loop Tracker blocks executions exceeding `max_tool_calls` limits, logging a `LOOP` anomaly.
- Path Validator blocks writes outside `/workspace` prior to execution, logging a `PATH` anomaly.
- Subprocess Monitor blocks unauthorized subprocesses and shell metacharacters, logging a `PROCESS` anomaly.
- Anomaly incidents terminate the container immediately, logging details in the `anomalies` table and updating `task_results.status` to `FAIL` (`LOOP_DETECTED`, `PATH_VIOLATION`, or `PROCESS_VIOLATION`).
- Integration tests confirm all three anomaly pathways are intercepted and logged correctly.
