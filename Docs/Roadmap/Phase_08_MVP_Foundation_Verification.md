# Phase 08: MVP Foundation Verification & Stabilization

## 1. Package / Folder Structure
```text
vigil/
└── tests/
    └── integration/
        ├── __init__.py
        ├── test_happy_path.py      # E2E success workflow tests
        ├── test_failures.py        # Task/tool/assertion failure test cases
        ├── test_sandbox_limits.py  # CPU, memory, and timeout limit verifications
        └── test_cleanup_guarantee.py # Post-execution host environment audits
```

---

## 2. Purpose
This phase acts as a stability checkpoint before implementing Phase 10 (Anomaly Detection). It focuses on writing integration and validation suites to confirm the core evaluation framework (Phases 1–7) is robust, correctly handles timeout boundaries, maps failure conditions cleanly, logs outcomes accurately to the database, and guarantees 100% reclamation of containers and filesystem resources under all circumstances.

---

## 3. Dependencies
### 3.1 Internal Modules
- `vigil.core.sandbox_manager` (To verify container lifecycles)
- `vigil.core.tool_executor` (To verify timeout limits and durations)
- `vigil.eval.runner` (To execute E2E tasks)
- `vigil.db.connection` (To query test outputs)

### 3.2 External Libraries
- `pytest` (To structure assertions and fixtures)
- `docker` (To inspect container status on the host)

---

## 4. Inputs
- Structured test YAML inputs (representing happy path, timeout path, and validation failures).
- Execution control parameters (e.g. artificial delays injected via tool command simulations).

---

## 5. Outputs
- Complete Pytest pass status for all integration suites.
- Validated records committed to `eval_runs`, `task_results`, and `tool_calls` tables verifying correct error types.

---

## 6. Public Interfaces
This is a verification phase. The primary interface is the Pytest suite itself, run via the command line:
`poetry run pytest tests/integration/`

---

## 7. Internal Components
- **`HostEnvironmentAuditor`**: Test helper scanning Docker daemon and host temp folder to assert no leaked resources remain after test suite runs.
- **`MockToolSimulator`**: Registers dummy commands simulating slow executions (to trigger timeouts) and error exits.

---

## 8. Development Prerequisites & Environment Bootstrap Checklist
- [ ] **Docker SDK accessible**: Docker daemon must be running.
- [ ] **PostgreSQL running**: Postgres Compose service active and migrated to latest schema.

---

## 9. Atomic Implementation Task List

| Task ID | Description | Size | Risk | Prerequisites | Dependencies | Expected Output | Testing | Definition of Done |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **TS-8.1** | Implement `test_happy_path.py` verifying full execution and persistence. | M | Low | TS-6.2, TS-7.7 | None | Validated tables (PASS result, sequence counts, TIMESTAMPTZ timestamps). | Run pytest on target file; query database tables to verify contents. | Run succeeds, commits task results, and saves tool call records. |
| **TS-8.2** | Implement invalid task definitions test (`test_failures.py`). | S | Low | TS-4.3 | None | Throws `TASK_DEFINITION_VALIDATION_ERROR` and aborts. | Test with malformed assertions (e.g. `expect_value: false`). | Validator successfully rejects bad schemas before provisioning. |
| **TS-8.3** | Implement tool execution failure and command timeout test cases. | M | Med | TS-3.5, TS-6.3 | None | Tool exit codes captured; processes terminated. | Execute commands returning non-zero codes, verify captures. | Non-zero exit code captures correctly without raising harness errors. |
| **TS-8.4** | Implement task-level timeout tests executing SIGKILL in docker. | M | Med | TS-2.7, TS-6.7 | None | Container is stopped; result mapped to `ERROR` (`TASK_TIMEOUT`). | Execute command: `sleep 300` with a 5s task timeout limit. | Sandbox is terminated, result is logged, and resources are cleared. |
| **TS-8.5** | Implement assertion failure scoring integration test. | S | Low | TS-4.8, TS-6.2 | None | scoring results map to `FAIL` (`ASSERTION_FAILED`). | Create task expecting file `ok.txt`, write nothing, verify. | Scoring results are mapped to `FAIL` and saved to `task_results`. |
| **TS-8.6** | Implement sandbox provisioning failure handling tests. | M | Med | TS-2.6, TS-6.3 | None | Result mapped to `ERROR` (`SANDBOX_PROVISION_ERROR`). | Stop Docker daemon temporarily, run harness, check logs. | System shuts down cleanly, logging DB errors, with no leakages. |
| **TS-8.7** | Implement `HostEnvironmentAuditor` test verification hooks. | M | Med | TS-2.8, TS-6.7 | None | Complete container and folder reclamation. | Run tests that crash or fail, verify no active docker objects remain. | 100% of container and directory objects are successfully reclaimed. |
| **TS-8.8** | Verify process interruption signal handlers (`SIGINT`, `SIGTERM`). | M | High | TS-2.7, TS-6.7 | None | Containers terminated; workspace deleted on exit. | Run harness task, send SIGINT signal from test command, verify. | Signal handler intercepts interruption and cleans resources. |

---

## 10. Definition of Done (DoD)
- Happy-path and edge-case validation suites are fully implemented.
- Task validation errors, tool failures, and tool/task timeouts are mapped correctly in the database.
- Cleanup audit tests verify that 100% of container and temporary filesystem directories are reclaimed on completion, timeout, or failure.
- Pytest integration suite runs cleanly and exits with a success code.
