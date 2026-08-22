# Vigil: Planning Consistency Audit

This document records the final consistency audit conducted to verify that the sequential implementation roadmap aligns with architectural guidelines, security constraints, and data definitions.

---

## 1. Core Architecture Checks

| Audit Item | Status | Verification Detail |
| :--- | :---: | :--- |
| **Task-Level Container Lifecycle** | **PASS** | Every phase (Phases 2, 3, 6, 8) defines the container lifecycle as one container per task, supporting multiple sequential tool calls and destroyed after completion. No "one container per tool call" schemes are implemented. |
| **Workspace Mount Strategy** | **PASS** | Intended writable paths are restricted to `/workspace` mounted from a temporary host directory. All phases follow this convention. |
| **Explicit Trust Boundaries** | **PASS** | Clear separation between the trusted harness host (with docker socket access, DB connections, and secrets) and the untrusted container runtime (unprivileged, non-root user, read-only root, no docker socket access). |
| **Status Enum Separation** | **PASS** | `eval_runs.status` (strictly `RUNNING`, `COMPLETED`, `FAILED`) remains separate from `task_results.status` (strictly `PASS`, `FAIL`, `ERROR`). They are not conflated. |
| **Assertion Schema Alignment** | **PASS** | Negative assertions in task YAML configurations use `negate: true` to align with the schema. Non-standard parameters like `expect_value: false` are rejected. |
| **Dependencies Sequencing** | **PASS** | Prerequisite packages are scheduled prior to their consumers: Config -> Sandbox -> Executor -> Adapter -> Harness -> DB -> Monitors -> Metrics -> API/UI. |
| **Atomic Task Definitions** | **PASS** | Tasks in all phases are detailed with Prerequisites, Size, Risk, Expected Output, and Definitions of Done. |
| **No Speculative Infrastructure** | **PASS** | No distributed queues (Celery, RabbitMQ), cache layers (Redis), cloud APIs, Kubernetes configurations, or microservices are introduced. |

---

## 2. Planning Document Modifications & Gaps

We have identified and flagged the following discrepancies between planning documents:

### 2.1 DB Schema vs. Prompt Run Status
- **Conflict**: `DB Schema.md` and `PRD.md` use `PENDING` for `eval_runs.status`. The prompt mandates `RUNNING`.
- **Resolution**: Aligned all database models in Phase 7 to use the prompt's `RUNNING` status definition.

### 2.2 Local Log Fallback System
- **Conflict**: `Architecture.md` describes a JSONL local database fallback system. The prompt forbids it.
- **Resolution**: Aligned all database persistence logic (Phases 7 and 8) to raise a hard `DATABASE_PERSISTENCE_ERROR` and abort execution, rather than writing fallback files.

### 2.3 Cleanup Supervisor Daemon
- **Conflict**: `Architecture.md` details a background cleanup daemon. The prompt advises against a daemon.
- **Resolution**: Replaced the daemon with an on-demand `vigil cleanup` CLI command mapped in the manual setup and verification phases.
