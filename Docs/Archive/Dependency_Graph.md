# Vigil: Architecture-to-Implementation Dependency Graph

This document details the sequential relationships and dependency trees governing Vigil's modules and task implementation order. The project strictly prioritizes the shortest dependency chain over parallel development to optimize sequential implementation for a single developer.

---

## 1. Module-Level Dependency Graph

This diagram illustrates how the core layers of Vigil depend on one another. The trusted configuration, DB, and sandbox layers form the baseline, upon which execution logic, agent adapters, and evaluation harnesses are built.

```mermaid
graph TD
    classDef trusted fill:#1f2937,stroke:#3b82f6,stroke-width:2px,color:#fff;
    classDef untrusted fill:#374151,stroke:#f59e0b,stroke-width:2px,color:#fff;
    classDef logic fill:#111827,stroke:#10b981,stroke-width:2px,color:#fff;

    Config["Configuration (Settings)"]:::trusted
    DB["PostgreSQL (Persistence)"]:::trusted
    Sandbox["Sandbox Manager (Docker SDK)"]:::trusted
    Exec["Tool Executor (Execution Layer)"]:::logic
    Adapter["Agent Adapter (LangGraph)"]:::untrusted
    Harness["Evaluation Harness (Pytest)"]:::logic
    Anomalies["Anomaly Detection (Monitor)"]:::logic
    API["FastAPI / Dashboard (Web UI)"]:::logic

    %% Dependencies
    Config --> DB
    Config --> Sandbox
    Sandbox --> Exec
    Exec --> Adapter
    Adapter --> Harness
    Harness --> DB
    Anomalies --> Exec
    Anomalies --> DB
    DB --> API
    Harness --> API
```

---

## 2. Phase-by-Phase Development Order

The sequential roadmap of phases is designed as a linear path with feedback gates. Every milestone leaves the codebase in a runnable and testable state.

```mermaid
graph LR
    P1["P01: Project Setup"] --> P2["P02: Sandbox Core"]
    P2 --> P3["P03: Tool Execution"]
    P3 --> P4["P04: Eval Definitions"]
    P4 --> P5["P05: Agent Adapter"]
    P5 --> P6["P06: Pytest Harness"]
    P6 --> P7["P07: DB Persistence"]
    P7 --> P8["P08: MVP Verification"]
    P8 --> P9["P09: Manual Dev Guide"]
    P9 --> P10["P10: Anomaly Detection"]
    P10 --> P11["P11: Metrics Math"]
    P11 --> P12["P12: API & UI"]
    P12 --> P13["P13: Portfolio Gate"]
```

---

## 3. Detailed Component Task Dependencies

Below is the atomic task dependency mapping for critical engineering paths. Implement tasks in order of their prerequisite layers.

```mermaid
graph TD
    subgraph Sandbox Core Path
        TS21["TS-2.1: Alpine Base Image"] --> TS26["TS-2.6: Create Sandbox"]
        TS22["TS-2.2: SandboxConfig Model"] --> TS25["TS-2.5: SDK Argument Mapper"]
        TS25 --> TS26
        TS23["TS-2.3: Docker Client Factory"] --> TS26
        TS24["TS-2.4: Workspace Temp Factory"] --> TS26
        TS26 --> TS27["TS-2.7: Destroy Sandbox"]
        TS27 --> TS28["TS-2.8: Teardown context wrapper"]
    end

    subgraph Scoring Path
        TS41["TS-4.1: Discriminated Assertion Schema"] --> TS42["TS-4.2: Task/Suite Models"]
        TS42 --> TS43["TS-4.3: TaskLoader YAML Parser"]
        TS41 --> TS45["TS-4.5: File Assertions"]
        TS41 --> TS46["TS-4.6: Exec Assertions"]
        TS41 --> TS47["TS-4.7: JSON Schema Assertions"]
        TS45 --> TS48["TS-4.8: Scoring Engine Dispatcher"]
        TS46 --> TS48
        TS47 --> TS48
    end

    subgraph Integration & Harness Path
        TS28 --> TS34["TS-3.4: Sandbox Exec Routing"]
        TS34 --> TS52["TS-5.2: Virtual Sandbox Tool"]
        TS52 --> TS54["TS-5.4: LangGraph Adapter Compile"]
        TS48 --> TS62["TS-6.2: run_task Orchestrator"]
        TS54 --> TS62
        TS62 --> TS77["TS-7.7: Persistence Service Hooks"]
    end
```

---

## 4. Cross-Module Interface Summary

1. **`core` to `eval`**: The `EvalRunner` requires `SandboxManager` to spin up environments, mount temporary directories, and clean up post-execution states.
2. **`agents` to `core`**: The agent adapter registers `VigilSandboxTool` which forwards payload requests to the `ToolExecutor` running inside the active task container.
3. **`db` to `eval` / `api`**: The `PersistenceService` hooks write runs, results, and anomalies directly to tables, which the FastAPI `MetricsEngine` later aggregates.
