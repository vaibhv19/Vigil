# Tech Stack Specification: Vigil (v1.0.0)

This document details the engineering choices, versioning, and architectural integration of the components within the **Vigil** ecosystem.

---

## 1. Core Technology Mapping

| Technology | Purpose in Vigil | Rationale & Tradeoffs | Targeted Version |
| :--- | :--- | :--- | :--- |
| **Python** | Primary Runtime | **Rationale:** Industry standard for LLM tooling and Docker SDK support. **Tradeoff:** Slower execution than Go/Rust for system-level monitoring. | `3.12+` |
| **Docker SDK** | Sandbox Management | **Rationale:** Allows fine-grained control over container lifecycle, resource cgroup limits, and networking. **Tradeoff:** Dependent on a local Docker daemon. | `7.1.0` |
| **LangGraph** | Agent Orchestration | **Rationale:** Manages the "ReAct" loop and state persistence of the agent under test. **Tradeoff:** Higher learning curve than simple LangChain chains. | `^0.0.10` |
| **Pytest** | Eval Execution Engine | **Rationale:** Powerful assertion rewriting and fixture support for state-based testing. **Tradeoff:** Requires careful isolation to prevent test-pollution. | `8.2.0` |
| **PostgreSQL** | Run/Metric Persistence | **Rationale:** Excellent JSONB support for logging varying tool-call schemas and Phase 3 analytics. **Tradeoff:** Heavier than SQLite for local-only use. | `16.0` |
| **FastAPI** | Backend API | **Rationale:** Serves run data to the Phase 3 dashboard with native async support. **Tradeoff:** Adds a layer of complexity over a pure CLI tool. | `0.111.0` |
| **Typer** | CLI Runner | **Rationale:** Provides a type-safe CLI for engineers to trigger evaluation suites from the terminal. | `^0.12.0` |

---

## 2. Sandbox Provisioning Strategy

The **Isolated Ephemeral Runtime Sandbox** is managed via the `docker-py` SDK using a "Just-In-Time" (JIT) provisioning model.

### 2.1 Image Strategy
*   **Vigil-Base Image:** A custom, hardened Alpine-based image (`vigil-sandbox-base:latest`) containing only the minimal binaries required for agent tools (e.g., Python, Curl, Bash).
*   **No Persistence:** The container root filesystem is non-persistent. Only the `/workspace` directory (a temporary Docker volume) survives between tool calls within a single task run, and it is wiped upon task completion.

### 2.2 Container Lifecycle (Task-Level Sandbox)
The sandbox lifecycle is defined as one ephemeral container per evaluation task, supporting multiple sequential tool calls within that container, destroyed after task completion/failure/timeout.
1.  **Provision:** One ephemeral container is created using `containers.run(detach=True)` at the start of the evaluation task.
2.  **Execution:** The agent's generated code/commands are injected via `exec_run()` into the running container, supporting multiple sequential tool calls.
3.  **Capture:** The `stdout`, `stderr`, and exit codes are captured and streamed back to the Harness after each tool execution.
4.  **Enforcement:** The container is created with the following isolation constraints:
    *   `mem_limit="512m"`
    *   `nano_cpus=500000000` (0.5 CPU)
    *   `network_mode="none"` (Unless external API access is explicitly required for the task).
    *   `cap_drop=["ALL"]` (Drop all Linux capabilities).
    *   `security_opt=["no-new-privileges"]`.
5.  **Termination:** The container is destroyed after task completion/failure/timeout (the Harness issues a `stop(timeout=0)` and `remove(v=True)`).

---

## 3. Orchestration Architecture: LangGraph vs. Harness

It is critical to distinguish between the **Agent logic** and the **Evaluation logic**.

*   **LangGraph (The Agent):** Orchestrates the internal "brain" of the agent under test. It defines how the agent decides which tool to call and how it processes the sandbox's output. The LangGraph state machine lives *inside* the execution flow that the harness monitors.
*   **Vigil Harness (The Controller):** The Harness sits *above* LangGraph. It initializes the LangGraph agent, provides it with the `SandboxTool` (which wraps the Docker SDK), and records the state transitions into PostgreSQL.

**Unambiguous Boundary:** LangGraph is the **subject** of the test; the Vigil Harness is the **instrument** of the test.

---

## 4. Testing & Evaluation Strategy

Vigil utilizes **Pytest** in two distinct capacities:

### 4.1 Internal Unit/Integration Testing
Standard test suite located in `/tests`. Uses Pytest to verify that the Docker SDK correctly throttles CPU, that PostgreSQL migrations run, and that the anomaly detector flags "runaway" loops.

### 4.2 Deterministic Evaluation Harness (The "Eval Runner")
Vigil treats an "Agent Task" as a specialized Pytest test case.
*   **The Fixture:** A `sandbox` fixture provisions the Docker container.
*   **The Action:** The test passes the task prompt to the LangGraph agent.
*   **The Assertion:** Unlike "vibes-based" evals, the assertion is performed against the **Sandbox State**.
    *   *Example:* `assert sandbox.file_exists("output.csv")` or `assert "200" in sandbox.run_command("curl localhost:8080")`.
*   **The Reporter:** A custom Pytest plugin (`VigilEvalReporter`) intercepts results and writes them to PostgreSQL: final outcomes to `task_results` (status: `PASS`/`FAIL`/`ERROR`) and `eval_runs` (status: `PENDING`/`COMPLETED`/`FAILED`), and raw tool-call logs to `tool_calls` (with sequence numbers).

---

## 5. Local Development Infrastructure

The development environment is containerized via `docker-compose.dev.yml` to ensure parity across engineering machines.

### 5.1 Services
*   **PostgreSQL 16:** Stores `tasks`, `eval_suites`, `eval_runs`, `task_results`, `tool_calls`, and `anomalies`.
*   **Vigil-API:** The FastAPI backend (Phase 3).
*   **Vigil-Worker:** The Python process that consumes evaluation tasks and talks to the host's `/var/run/docker.sock`.
*   **Adminer:** (Optional) Lightweight database GUI for inspecting run logs.

### 5.2 Out-of-Scope (Infrastructure)
*   No Kubernetes manifests.
*   No Cloud Provider (AWS/GCP) SDKs.
*   No remote container registries (images built locally from `/dockerfiles`).
*   No external Auth providers (Local JWT or simple API keys only).

---

## 6. Project Directory Structure (Mapping)

```text
vigil/
├── core/               # Docker SDK & Sandbox Logic
├── agents/             # LangGraph State Definitions
├── eval/               # Pytest Harness & Assertions
├── api/                # FastAPI Endpoints (Phase 3)
├── db/                 # SQLAlchemy Models & Migrations
├── cli/                # Typer CLI Commands
├── dockerfiles/        # Sandbox-Base & Harness images
└── tests/              # Internal Unit Tests
```