# PRD — Vigil: Autonomous Agent Evaluation Harness & Safe-Runtime Sandbox

**Status:** Draft | **Version:** 1.0.0  
**Stack:** Python, Docker SDK, LangGraph, Pytest, PostgreSQL

---

## 1. Overview & Problem Statement

As autonomous agents transition from "chatbots" to "act-bots" (executing code, querying databases, and managing files), current evaluation methods are failing in two critical areas:

1.  **"Vibes-Based" Evaluation:** Most teams rely on LLM-as-a-judge or manual spot-checking. These are non-deterministic, expensive, and fail to catch logic regressions in tool-use.
2.  **Unsafe Testing Environments:** Running agent-generated code on local machines or shared dev servers risks accidental `rm -rf /`, resource exhaustion, or data leakage.

**Vigil** solves this by providing a programmatic evaluation harness that runs agents inside ephemeral, resource-constrained Docker sandboxes. It replaces subjective "vibes" with hard, state-based assertions (e.g., "Did the agent actually create the file with the correct SHA-256 hash?") while ensuring the host system is never at risk.

---

## 2. Goals & Explicit Non-Goals

### 2.1 Goals
*   **Deterministic Scoring:** Provide a `pass/fail` result based on the final state of the sandbox, not just the LLM’s text output.
*   **Isolation by Default:** Ensure the sandbox lifecycle is one ephemeral container per evaluation task, supporting multiple sequential tool calls within that container, destroyed after task completion/failure/timeout.
*   **Regression Tracking:** Store execution metadata in PostgreSQL (`eval_runs`, `task_results`, and `tool_calls` tables) to compare agent versions.
*   **Pattern Detection:** Identify "runaway" agents that loop excessively or attempt restricted filesystem operations.

### 2.2 Non-Goals
*   **General Purpose Security Tool:** Vigil is not a hardened production sandbox for hostile multi-tenant workloads; it is an evaluation tool for engineers.
*   **Agent Library:** Vigil does not provide the agents; it provides the *infrastructure* to test them.
*   **Zero-Day Prevention:** Vigil does not protect against sophisticated Docker escape exploits (0-days).

---

## 3. Target Users & Use Cases

### 3.1 Target Users
*   **AI Engineers:** Developing tool-use agents who need to verify that prompt changes don't break code-execution logic.
*   **LLM Ops / DevOps:** Benchmarking the cost and latency of different agent architectures (e.g., ReAct vs. Plan-and-Execute).

### 3.2 Key Use Cases
*   **Tool Regression Testing:** "Ensure my SQL-agent can still join three tables after I updated the system prompt."
*   **Safety Guardrail Validation:** "Verify the agent stops and reports an error if it is asked to delete a system-level directory."
*   **Cost/Performance Optimization:** "Identify which version of my agent solves the 'Data Cleaning' task with the fewest API calls."

---

## 4. Functional Requirements

### 4.1 MVP (Build First)
| ID | Requirement | Description |
| :--- | :--- | :--- |
| **F-1.1** | **Ephemeral Provisioning** | System must use Docker SDK to spin up one ephemeral container per evaluation task, supporting multiple sequential tool calls within that container, destroyed after task completion/failure/timeout. |
| **F-1.2** | **Filesystem Restriction** | Containers must mount only a specific `WORKSPACE_DIR` with no access to host root or environment variables. |
| **F-1.3** | **Hard Teardown** | System must guarantee container removal (SIGKILL) even if the agent process hangs or the harness crashes. |
| **F-1.4** | **Pytest Integration** | Evaluation tasks must be definable as standard Pytest functions that assert on sandbox state (files, exit codes, stdout). |
| **F-1.5** | **Run Persistence** | Every execution must log to PostgreSQL tables: `eval_suites`, `eval_runs` (status: PENDING/COMPLETED/FAILED), `task_results` (status: PASS/FAIL/ERROR), `tool_calls` (sequence_number, tool_name, input_args, stdout_capture, exit_code, duration_ms), and `anomalies`. |

### 4.2 Phase 2 (Anomaly Detection)
| ID | Requirement | Description |
| :--- | :--- | :--- |
| **F-2.1** | **Loop Detection** | System must flag/terminate runs that exceed a user-defined maximum tool-call count (e.g., >10 calls for one task). |
| **F-2.2** | **Path Violation** | Block and log attempts to write to paths outside the designated `/workspace` (e.g., attempts to modify `/etc/`) as PATH anomalies in the `anomalies` table. |
| **F-2.3** | **Subprocess Monitor** | Block and log spawning of unexpected shell processes as PROCESS anomalies in the `anomalies` table. |

### 4.3 Phase 3 (Metrics & Dashboard)
| ID | Requirement | Description |
| :--- | :--- | :--- |
| **F-3.1** | **Aggregated Metrics** | Dashboard must display P50/P90 latency, average token cost, and pass/fail rates per agent version. |
| **F-3.2** | **Version Comparison** | Provide a "Differential View" comparing Run A vs Run B to show how a prompt change affected tool-use accuracy. |

---

## 5. Non-Functional Requirements

*   **Isolation Guarantee:** Containers must run as `non-root` users with `no-new-privileges` flag enabled.
*   **Resource Limits:** Every sandbox must be capped at `0.5 CPU` cores and `512MB RAM` to prevent local denial-of-service by agent code.
*   **Durability:** PostgreSQL must use Write-Ahead Logging (WAL) to ensure execution logs are not lost during harness crashes.
*   **Concurrency:** The harness must support running up to 5 evaluation tasks in parallel on a standard developer workstation (16GB RAM).

---

## 6. Success Metrics

1.  **Resource Cleanup:** 100% of Docker containers created by the harness must be removed within 60 seconds of task completion/timeout.
2.  **Scoring Accuracy:** 100% agreement between the Pytest assertion result and the database `status` in the `task_results` table.
3.  **Benchmarking Overhead:** The time taken to provision and teardown the sandbox should be $<25\%$ of the total task execution time.

---

## 7. Honest Scope Boundary (Out-of-Scope)

Vigil is designed for **Evaluation and Engineering Safety**, not as a production-grade firewall. 

*   **No Sandbox Escape Detection:** We do not detect side-channel attacks, Spectre/Meltdown-style exploits, or kernel-level escapes.
*   **Pattern-Based, Not Intent-Based:** Anomaly detection is strictly based on *explicit rules* (e.g., "Max 5 file writes"). We do not use "AI Security" to guess if an agent's intent is malicious.
*   **No Network Simulation:** Vigil does not simulate complex network topologies. Containers are either `network: none` or have full access (user-configured).

---

## 8. Open Questions / Assumptions

1.  **Assumptions:** It is assumed the user has Docker installed and the Python process has permissions to communicate with `docker.sock`.
2.  **Question:** Should we support different container images (e.g., `python:alpine` vs `node:alpine`) per task, or stick to a unified Vigil-Base image for MVP?
3.  **Question:** How should we handle "long-running" tools? (Currently assuming a hard timeout of 30s per tool call).