# Implementation Plan: Vigil Roadmap Staged Delivery

This plan outlines the architecture-to-implementation planning process for **Vigil**, a portfolio-quality Autonomous Agent Evaluation Harness & Safe-Runtime Sandbox.

We are implementing the plan in three sequential batches to ensure high quality and detail across all deliverables.

---

## Proposed Roadmap Structure

The final deliverables will be written as a set of structured Markdown files in the artifacts directory.

### Completed: Batch 1 (Core MVP Chain)
- [Roadmap_Index.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Roadmap_Index.md) - Master Index linking all phases.
- [Phase_01_Project_Foundation.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_01_Project_Foundation.md) - Repository setup, PostgreSQL compose service, configuration settings, and baseline Pytest setup.
- [Phase_02_Sandbox_Foundation.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_02_Sandbox_Foundation.md) - Docker SDK manager, CPU/memory limits, capability drops, read-only root, and workspace mounts.
- [Phase_03_Tool_Execution.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_03_Tool_Execution.md) - Exec-run routing, stdout/stderr capture, exit codes, durations, timeouts, and sequential logs.
- [Phase_04_Evaluation_Definitions.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_04_Evaluation_Definitions.md) - YAML task configuration, Pydantic discriminated assertion schemas, context injection, and state evaluations.
- [Phase_05_Agent_Integration.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_05_Agent_Integration.md) - Abstract agent adapters and concrete LangGraph ReAct implementation.
- [Phase_06_Evaluation_Harness.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_06_Evaluation_Harness.md) - Pytest-integrated suite runner, reporting plugin, and cleanup guarantees.
- [Phase_07_Persistence.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_07_Persistence.md) - PostgreSQL persistence layer, database models (using TIMESTAMPTZ), migrations, and transaction management.

### Completed: Batch 2 (Verification, Setup, and Anomaly Detection)
- [Phase_08_MVP_Foundation_Verification.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_08_MVP_Foundation_Verification.md) - Verification tests (timeouts, failure cases, persistence issues, workspace leaks).
- [Phase_09_Manual_Setup_Integration.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_09_Manual_Setup_Integration.md) - Complete manual setup, environment files, and credentials configuration.
- [Phase_10_Anomaly_Detection.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_10_Anomaly_Detection.md) - Loop tracking, pre-execution path validation, and subprocess allowlist checks.
- [Phase_11_Metrics_Comparison.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_11_Metrics_Comparison.md) - Percentile latency calculations, token costs, and run comparison engine.
- [Phase_12_API_Dashboard.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_12_API_Dashboard.md) - FastAPI endpoints for metrics retrieval and version comparisons.
- [Phase_13_Final_Quality_Portfolio.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Phase_13_Final_Quality_Portfolio.md) - Full suite validations, readme/study guides compilation, and claims verification.

### Completed: Batch 3 (System & Support Documents)
- [Dependency_Graph.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Dependency_Graph.md) - Visual representation of task and module dependencies.
- [Milestones.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Milestones.md) - List of runnable checkpoints with verification plans.
- [Git_Strategy.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Git_Strategy.md) - Branching and commit workflow.
- [Manual_Setup_and_Integration_Guide.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Manual_Setup_and_Integration_Guide.md) - Consolidated setup steps.
- [Error_Taxonomy.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Error_Taxonomy.md) - Taxonomy mapping source errors to final results.
- [Configuration_Reference.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Configuration_Reference.md) - Mapping environment variables and options.
- [Open_Questions.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Open_Questions.md) - Architectural issues and design gaps.
- [Planning_Consistency_Audit.md](file:///C:/Users/vaibhav%20gupta/.gemini/antigravity-ide/brain/4c51019c-5537-4ce8-9773-b819facff749/Planning_Consistency_Audit.md) - Final audit of inconsistencies between planning documents and design constraints.

---

## Architectural Notes & Consistency Findings (Batch 1)

During the compilation of Batch 1, the following potential conflicts/decisions were resolved or noted:
1. **Network Policy:** Confirmed that `network_mode: none` is the default in `Architecture.md` and `tech_stack.md`. Will be mapped accordingly.
2. **Run Status:** The prompt dictates that `eval_runs.status` must strictly be `RUNNING`, `COMPLETED`, or `FAILED`. The planning docs listed `PENDING` instead of `RUNNING`. We have aligned the database models in Phase 7 to strictly use the prompt's `RUNNING` status definition.
3. **Negative Assertions:** Aligned YAML task files to use `negate: true` (Pydantic schema level) rather than `expect_value: false` (found in Spec example 3).
4. **Durable Fallbacks:** Handled database write failures as immediate, clean execution termination (`DATABASE_PERSISTENCE_ERROR`) instead of relying on undefined local JSONL fallback loops.

---

## Verification Plan

We will verify our deliverables as follows:
- Ensure all 8 Batch 1 files are successfully written, formatted correctly, and contain links targeting local file locations.
- Verify file locations and links are correct.
