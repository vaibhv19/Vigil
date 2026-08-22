# Vigil — Feature List

**Project Name:** Vigil (Autonomous Agent Evaluation Harness & Safe-Runtime Sandbox)  
**Stack:** Python + Docker SDK + LangGraph + Pytest + PostgreSQL  
**Core Differentiator:** Agent Safety & Evaluation Infrastructure  

---

## MVP (Build First)

*   **Isolated Ephemeral Runtime Sandbox** — Provisions one ephemeral container per evaluation task, supporting multiple sequential tool calls within that container, destroyed after task completion/failure/timeout, with restricted filesystem access and capped resource limits (CPU/memory/time).
*   **Deterministic Evaluation Harness** — Programmatic regression runner: given an agent + a set of pre-defined tasks with known-correct outcomes, runs the agent against each and scores them, saving final outcomes in `task_results.status` (`PASS`/`FAIL`/`ERROR`).
*   **Run Logging** — Every execution logged to PostgreSQL tables: `eval_suites`, `eval_runs`, `task_results`, and `tool_calls` (sequence_number, tool_name, input_args, stdout_capture, exit_code, duration_ms).
*   **Core Engineering** — Ephemeral containers cleaned up reliably even on crash/timeout, clear `status` reporting per task run.

---

## Phase 2 — Anomaly Detection
*Scoped honestly, not "general escape detection"*

*   **Tool Execution Loop Tracker** — Intercepts and blocks known risky patterns: excessive tool calls (LOOP), writing to paths outside `/workspace` (PATH), and spawning forbidden processes (PROCESS), logging them in the `anomalies` table.
*   **Honest Scope Boundary** — Framed explicitly as "detects known risky patterns," not "detects all possible malicious behavior" — same as StudyLink's "local pickup only".

---

## Phase 3 — Metrics & Dashboard

*   **Performance Metrics Matrix Dashboard** — Aggregates across multiple runs: latency percentiles, token/cost-per-run, pass rate over time.
*   **Comparison Engine** — Useful for comparing agent versions against each other (e.g., "did my last prompt change make the agent slower/more expensive/less accurate?").
