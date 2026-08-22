# Vigil: Project Milestones

This document details the sequential checkpoints for Vigil development. Each milestone represents a stable, runnable, and testable codebase state.

---

## Milestone 1: Ephemeral Sandbox Isolation Core (Phase 1–2)

### 1. Completed Functionality
- Python project structure, dependencies via Poetry, and environment configuration loader.
- Docker client integration and unprivileged workspace volume creation.
- Ephemeral task-level container provisioning with memory, CPU, networking, and capability dropping limits.

### 2. What Can Be Demonstrated
- Spin up of an Alpine-based sandbox with isolated parameters.
- Mounting and checking of `/workspace` permissions (writable by non-root UID 1000).
- Explicit cleanup of sandbox resources via python commands.

### 3. What Can Be Tested
- Unit test for environment loading (`test_config.py`).
- Integration tests checking container boundaries, user settings, capability drops, and CPU/memory quotas (`test_sandbox.py`).

### 4. What Intentionally Remains Incomplete
- Executing code or tracking command streams inside the sandbox.
- Evaluation definitions, scoring engines, agent adapter integrations, and database persistence.

### 5. Required Verification
- Execute `poetry run pytest tests/unit/test_sandbox_cfg.py tests/integration/test_sandbox.py`.

### 6. Cleanup Expectations
- 100% reclamation of test containers and host temporary mounts.

### 7. Required Manual Setup Status
- Docker daemon must be running.
- Copy `.env.example` to `.env` and fill out `WORKSPACE_BASE_DIR`.

---

## Milestone 2: Code Execution & Interception Layer (Phase 3)

### 1. Completed Functionality
- Request and Result models for tool calls.
- Command routing to sandboxes via `exec_run()`.
- Capturing of stdout, stderr, and exit codes.
- Duration measurement (ms) and execution timeout guards (e.g. 30s limits).

### 2. What Can Be Demonstrated
- Run shell commands inside a provisioned container and print stdout streams.
- Trigger sequential commands that modify workspace files.
- Halt commands exceeding timeouts.

### 3. What Can Be Tested
- Integration test running code lines inside containers and checking results (`test_tool_execution.py`).
- Timeout test verifying hung processes are aborted cleanly.

### 4. What Intentionally Remains Incomplete
- Parsing YAML evaluations, scoring criteria, and agent loops.
- PostgreSQL database persistence.

### 5. Required Verification
- Execute `poetry run pytest tests/integration/test_tool_execution.py`.

### 6. Cleanup Expectations
- Container is killed on timeout and all sandbox folders are purged.

---

## Milestone 3: Deterministic Scoring & Agent Integration (Phase 4–6)

### 1. Completed Functionality
- YAML task specifications parser and Pydantic validator.
- Evaluation assertion evaluators (`file_exists`, `file_content_match`, `exit_code`, `stdout_contains`, `tool_call_count`, `json_schema`) supporting `negate: true`.
- Pluggable agent adapter and concrete LangGraph adapter ReAct loop.
- Pytest suite integration runner and JSON result compiler.

### 2. What Can Be Demonstrated
- Load YAML tasks, execute a LangGraph agent through the virtual sandbox tool, score outcomes, and print console results tables.

### 3. What Can Be Tested
- Assertion matching logic (`test_assertions.py`).
- YAML syntax checks (`test_task_loader.py`).
- Complete integration runs with mock LLMs (`test_eval_runner.py`).

### 4. What Intentionally Remains Incomplete
- PostgreSQL database writes and FastAPI dashboard pages.
- Active loop and path anomaly monitors (Phase 10).

### 5. Required Verification
- Execute `poetry run pytest tests/integration/test_eval_runner.py`.

### 6. Cleanup Expectations
- Task containers and temporary directory systems are removed.

---

## Milestone 4: Database Persistence (Phase 7–8)

### 1. Completed Functionality
- Alembic database migration profiles.
- PostgreSQL ORM models representing the complete schema (using TIMESTAMPTZ).
- Persistence service saving executions, log history, and result structures.
- Failure testing confirming the MVP system is stable (Milestones 1–4).

### 2. What Can Be Demonstrated
- Run evaluations and inspect DB tables showingPASS/FAIL, execution config snapshots, and tool call logs.

### 3. What Can Be Tested
- Database connection, ORM writes, and session releases (`test_persistence.py`).
- Comprehensive stability, timeout, and failure integration tests (`test_happy_path.py`, `test_failures.py`).

### 4. What Intentionally Remains Incomplete
- Anomaly monitors (loop, path, and process violations).
- FastAPI REST routes and HTML dashboard page components.

### 5. Required Verification
- Execute `poetry run pytest tests/integration/test_persistence.py tests/integration/test_happy_path.py`.

### 6. Cleanup Expectations
- Database failure raises `DATABASE_PERSISTENCE_ERROR` and aborts safely.

---

## Milestone 5: Complete Safe-Runtime Platform (Phase 9–13)

### 1. Completed Functionality
- Verification tools (`vigil bootstrap`).
- LOOP, PATH, and PROCESS anomaly monitoring.
- Percentile latency metrics and run comparison utilities.
- FastAPI REST backend and static single-page Vanilla CSS dashboard.
- Full test sweep and updated system documentation.

### 2. What Can Be Demonstrated
- Run agent tasks attempting safety violations, observe immediate container halts, and view anomalies in the dashboard.
- Compare two agent versions showing regression charts.

### 3. What Can Be Tested
- Anomaly checks (`test_anomalies.py`), metrics logic (`test_metrics.py`), and HTTP API endpoints (`test_api.py`).

### 4. What Intentionally Remains Incomplete
- None. Project is feature-complete.

### 5. Required Verification
- Execute `poetry run pytest`.
- Start API: `poetry run uvicorn vigil.api.main:app --reload` and visit dashboard.

### 6. Cleanup Expectations
- 100% reclamation of test containers.
