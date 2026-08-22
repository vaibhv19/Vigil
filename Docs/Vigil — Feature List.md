# Vigil — Feature List

**Project Name:** Vigil (Autonomous Agent Evaluation Harness & Safe-Runtime Sandbox)  
**Stack:** Python + Docker SDK + LangGraph + Pytest + PostgreSQL  
**Core Differentiator:** Agent Safety & Evaluation Infrastructure  

---

## MVP (Build First)

*   **Isolated Ephemeral Runtime Sandbox** — Provisions unprivileged, containerized environments per agent tool call, with restricted filesystem access and capped resource limits (CPU/memory/time), torn down after each run.
*   **Deterministic Evaluation Harness** — Programmatic regression runner: given an agent + a set of pre-defined tasks with known-correct outcomes, runs the agent against each and scores pass/fail — hard accuracy metrics, not vibes.
*   **Run Logging** — Every sandboxed execution stored in PostgreSQL: what tool was called, what it did, pass/fail result, duration, cost.
*   **Core Engineering** — Containers cleaned up reliably even on crash/timeout, clear pass/fail reporting per run.

---

## Phase 2 — Anomaly Detection
*Scoped honestly, not "general escape detection"*

*   **Tool Execution Loop Tracker** — Flags a defined, explicit set of concerning patterns: excessive repeated calls (loop detection by call-count/time), filesystem writes outside the sandboxed path, unexpected process spawning.
*   **Honest Scope Boundary** — Framed explicitly as "detects known risky patterns," not "detects all possible malicious behavior" — same as StudyLink's "local pickup only".

---

## Phase 3 — Metrics & Dashboard

*   **Performance Metrics Matrix Dashboard** — Aggregates across multiple runs: latency percentiles, token/cost-per-run, pass rate over time.
*   **Comparison Engine** — Useful for comparing agent versions against each other (e.g., "did my last prompt change make the agent slower/more expensive/less accurate?").
