# Vigil: Open Questions & Planning Gaps

This document highlights architectural conflicts and technical gaps identified during the planning process.

---

## 1. Safety Scope & Network Policy Gap
- **Inconsistency**: `Safety Scope.md` does not mention network policies or isolation defaults. However, `Architecture.md` (Section 5.2) and `tech_stack.md` (Section 2.2) state that networking is disabled by default (`network_mode="none"`), unless external access is configured.
- **Resolution**: We have defined network isolation as the MVP default in the configurations, but this remains an open question to align with safety audits if task-specific network configurations require local firewalls.

---

## 2. Evaluation Run Status Lifecycle Conflict
- **Inconsistency**: Planning documents (`PRD.md` section 4.1, `DB Schema.md` section 2, and `Architecture.md` section 8) specify that the `eval_runs` status column uses values: `PENDING`, `COMPLETED`, and `FAILED`. However, the prompt dictates that `eval_runs.status` must remain strictly: `RUNNING`, `COMPLETED`, and `FAILED`.
- **Impact**: We have updated the ORM database schema models (Phase 7) to use `RUNNING`, `COMPLETED`, and `FAILED` to conform to the prompt's rules. We must update the `PRD.md` and `DB Schema.md` files in the workspace accordingly to prevent developer confusion.

---

## 3. Database Failure Fallback Strategy Conflict
- **Inconsistency**: `Architecture.md` (Section 6) details a fallback logging system where database connection issues trigger a local write to a `.jsonl` log file under `temp_run/`, which is later synced back to the database. However, the prompt explicitly states: *"Do not introduce an undefined JSONL fallback logging system into the MVP... database persistence failure must be handled as a clearly defined error condition. Do not invent: JSONL fallback schemas..."*
- **Impact**: We have excluded the JSONL fallback system from our execution roadmap (Phases 6 and 7). Instead, database failures raise `DATABASE_PERSISTENCE_ERROR`, which halts the suite immediately to prevent telemetry loss.

---

## 4. Stale Container Cleanup: Background Daemon vs. Command
- **Inconsistency**: `Architecture.md` (Section 5.4) details a last-resort cleanup mechanism using a persistent background daemon (`VigilSupervisor`) running every 5 minutes to sweep stale containers. The prompt dictates: *"Do not introduce a persistent background supervisor daemon into the MVP unless implementation genuinely proves it is necessary... A possible recovery capability is: `vigil cleanup`"*
- **Impact**: We have removed the background supervisor daemon from our planning phases (Phase 2 and 6). We have instead implemented the `vigil cleanup` command under the CLI command definitions to serve as an on-demand cleanup script.

---

## 5. Multiple Image Support per Task
- **Question**: Should we support custom images (e.g. `python:alpine`, `node:alpine`) specified per task in YAML files, or force all tasks to execute against a unified `vigil-sandbox-base:latest` image?
- **Current Choice**: For the MVP, we assume a single custom image containing minimal Python, bash, and curl. Multi-image support should be postponed to later versions.
