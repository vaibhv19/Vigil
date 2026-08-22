# Vigil: Implementation Roadmap Index

This document serves as the entry point and master index for the phase-wise implementation roadmap of **Vigil**—an Autonomous Agent Evaluation Harness & Safe-Runtime Sandbox. The roadmap is designed for a single developer working sequentially, keeping the project runnable, testable, and stable at each milestone.

## Staged Delivery Plan
To ensure high depth, accuracy, and engineering rigor, the roadmap documents are delivered in three sequential batches:
1. **Batch 1 (Core MVP Chain):** [Roadmap_Index.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Roadmap_Index.md) and [Phase 01](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_01_Project_Foundation.md) through [Phase 07](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_07_Persistence.md).
2. **Batch 2 (Verification, Setup & Anomaly Detection):** Phase 08 through Phase 13.
3. **Batch 3 (System & Support Documents):** Dependency Graph, Milestones, Git Strategy, Manual Setup Guide, Error Taxonomy, Configuration Reference, Open Questions, and Planning Consistency Audit.

---

## Phase Overview

| Phase | Phase Name | Purpose | Dependencies | Link / Reference |
| :---: | :--- | :--- | :--- | :--- |
| **01** | **Project Foundation & Dev Env** | Set up the Python repository, package structure, configurations, and environment bootstrap. | None | [Phase_01_Project_Foundation.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_01_Project_Foundation.md) |
| **02** | **Sandbox Foundation** | Core Docker SDK integration, resource limits, capability dropping, and workspace mounts. | Phase 01 | [Phase_02_Sandbox_Foundation.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_02_Sandbox_Foundation.md) |
| **03** | **Tool Execution & Interception** | Abstraction of tool requests/results, stdout/stderr capture, exit code tracking, and exec routing. | Phase 02 | [Phase_03_Tool_Execution.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_03_Tool_Execution.md) |
| **04** | **Evaluation Definitions & Scoring** | YAML task definition parsing, Pydantic validation, and terminal state assertions. | Phase 01, 03 | [Phase_04_Evaluation_Definitions.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_04_Evaluation_Definitions.md) |
| **05** | **Agent Integration** | Pluggable Agent Adapter interface and first implementation for LangGraph ReAct loop. | Phase 03, 04 | [Phase_05_Agent_Integration.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_05_Agent_Integration.md) |
| **06** | **Evaluation Harness & Pytest** | Orchestrate lifecycle via custom Pytest runners, running tests, scoring, and generating reports. | Phase 04, 05 | [Phase_06_Evaluation_Harness.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_06_Evaluation_Harness.md) |
| **07** | **Persistence** | PostgreSQL integration, SQLAlchemy models, migration files, and log execution schema. | Phase 01, 06 | [Phase_07_Persistence.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_07_Persistence.md) |
| **08** | **MVP Foundation Verification** | Verify happy-path, failure-path, timeouts, database errors, and cleanups for MVP (Phases 1-7). | Phase 01–07 | *Pending Batch 2* |
| **09** | **Manual Setup & Dev Guide** | Consolidate and formalize manual steps (Docker permissions, database credentials, keys, env setup). | Phase 08 | *Pending Batch 2* |
| **10** | **Anomaly Detection** | Implement excessive loop tracking, pre-execution path validation, and subprocess spawning monitoring. | Phase 08 | *Pending Batch 2* |
| **11** | **Metrics & Comparison** | Aggregate runs to compute P50/P90 latencies, run costs, and version-to-version comparisons. | Phase 07, 10 | *Pending Batch 2* |
| **12** | **API & Dashboard** | FastAPI endpoints and frontend integration to query and display persisted runs and metrics. | Phase 11 | *Pending Batch 2* |
| **13** | **Final Quality & Portfolio** | Comprehensive test coverage, documentation audit, cleanup validations, and portfolio claim proofs. | Phase 12 | *Pending Batch 2* |

---

## Architectural Principles & Strict Guarantees

1. **One Ephemeral Container Per Evaluation Task:** Sandbox containers are initialized at the start of a task, support multiple sequential tool calls (preserving state in `/workspace`), and are unconditionally destroyed upon completion, timeout, or failure. We do **not** spin up a new container per tool call.
2. **Untrusted Runtime Boundary:** The agent reasoning loop and generated code execute inside the resource-constrained, non-root, read-only Docker container. The Vigil Harness runs on the host as trusted infrastructure. Host secrets, Docker socket (`docker.sock`), and host filesystem paths are never exposed to the container.
3. **Objective Evaluation:** Scoring is purely deterministic, asserting against terminal filesystem state, stdout, exit codes, and tool logs. Subjective "LLM-as-a-judge" mechanisms are rejected.
4. **Scope-Guarded Anomaly Detection:** Anomaly detection covers only looping, unauthorized paths (writes outside `/workspace`), and disallowed subprocesses. It is explicitly framed as crash-test safety for development, not a general security IDS or production firewall.
