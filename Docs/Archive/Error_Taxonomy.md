# Vigil: Error Taxonomy

This document maps all exception codes and failure pathways to execution statuses, containment rules, and logging destinations.

---

## 1. Error Taxonomy Matrix

| Error Code | Originating Component | Owner | Maps to Result | Task Terminated? | Anomaly Logged? | Database Persistence Detail |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **`TASK_DEFINITION_VALIDATION_ERROR`** | `TaskLoader` | `eval` | **ERROR** | Yes (Pre-run) | No | Not persisted (run halts before execution begins). |
| **`SANDBOX_PROVISION_ERROR`** | `SandboxManager` | `core` | **ERROR** | Yes | No | Logs `task_results.status = ERROR`, `failure_reason = SANDBOX_PROVISION_ERROR`. |
| **`AGENT_EXECUTION_ERROR`** | `AgentAdapter` | `agents`| **ERROR** | Yes | No | Logs `task_results.status = ERROR`, `failure_reason = AGENT_EXECUTION_ERROR`. |
| **`TOOL_EXECUTION_ERROR`** | `ToolExecutor` | `core` | **FAIL** / **ERROR** | Yes | No | Logs exit code in `tool_calls`. Result status depends on task configuration. |
| **`TOOL_TIMEOUT`** | `TimeoutGuard` | `core` | **ERROR** | Yes | No | Logs `task_results.status = ERROR`, `failure_reason = TOOL_TIMEOUT`, kills container. |
| **`TASK_TIMEOUT`** | `EvalRunner` | `eval` | **ERROR** | Yes | No | Logs `task_results.status = ERROR`, `failure_reason = TASK_TIMEOUT`, kills container. |
| **`ASSERTION_FAILURE`** | `ScoringEngine` | `eval` | **FAIL** | Yes | No | Logs `task_results.status = FAIL`, `failure_reason = ASSERTION_FAILED`. |
| **`SANDBOX_CLEANUP_ERROR`** | `SandboxManager` | `core` | **ERROR** | Yes | No | Logs `task_results.status = ERROR`, `failure_reason = SANDBOX_CLEANUP_ERROR`. |
| **`DATABASE_PERSISTENCE_ERROR`**| `PersistenceService` | `db` | **ERROR** | Yes (Abort Suite)| No | Throws exception to host; runs are stopped to prevent telemetry loss. |
| **`LOOP_DETECTED`** | `AnomalyDetector` | `core` | **FAIL** | Yes | Yes | Logs `task_results.status = FAIL`, `failure_reason = LOOP_DETECTED`, anomaly saved. |
| **`PATH_VIOLATION`** | `PathValidationLayer`| `core` | **FAIL** | Yes | Yes | Logs `task_results.status = FAIL`, `failure_reason = PATH_VIOLATION`, anomaly saved. |
| **`PROCESS_VIOLATION`** | `SubprocessMonitor` | `core` | **FAIL** | Yes | Yes | Logs `task_results.status = FAIL`, `failure_reason = PROCESS_VIOLATION`, anomaly saved. |

---

## 2. Failure Handling Details

### 2.1 Pass vs. Fail vs. Error Distinction
- **`PASS`**: The agent completed execution, and 100% of defined state assertions returned `True`.
- **`FAIL`**: The agent completed, but one or more assertions returned `False`, or an anomaly (e.g. `LOOP`, `PATH`, `PROCESS`) was intercepted.
- **`ERROR`**: The framework encountered an operational issue (e.g., Docker is unresponsive, tool timed out, DB crashed, task definitions are invalid) that prevented evaluation completion.

### 2.2 Run Termination Behavior on Database Failures
- Vigil prioritizes logging durability. If the PostgreSQL server goes offline during active execution:
  1. The `PersistenceService` raises `DATABASE_PERSISTENCE_ERROR`.
  2. The harness traps this, stops executing subsequent tasks in the suite, and attempts to clean up any running Docker containers.
  3. No local fallback files are written, and the run exits with a non-zero code to ensure issues are diagnosed immediately.
