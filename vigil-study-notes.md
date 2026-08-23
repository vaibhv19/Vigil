# Vigil — Architecture & Engineering Study Notes

> A deep-dive into the design decisions, engineering trade-offs, and lessons learned building Vigil — an autonomous AI agent evaluation harness with sandboxed execution.

---

## 1. System Design Philosophy

Vigil was designed around a core principle: **measure agents by what they do, not what they say.** Rather than evaluating agent outputs textually, Vigil observes the actual side effects of agent execution — files created, commands run, processes spawned — inside a controlled environment.

### Key Design Constraints
- **Zero trust in agent behavior**: Agents are treated as untrusted code. Every action is sandboxed, monitored, and recorded.
- **Deterministic evaluation**: Results must be reproducible. Identical tasks with identical agents should produce comparable metrics.
- **Host safety is non-negotiable**: No agent action should ever affect the host filesystem, network, or resources.

---

## 2. Sandbox Architecture

### Why Docker over VM-based isolation?
Docker containers provide the right balance of isolation strength and operational speed for an evaluation harness:

| Factor | Docker Containers | Full VMs |
|--------|------------------|----------|
| Startup time | ~1-3 seconds | 30-60 seconds |
| Resource overhead | ~10-50 MB per container | ~512 MB+ per VM |
| Isolation strength | Process + namespace level | Hardware level |
| API maturity | Docker SDK is excellent | Varies by hypervisor |

For evaluation workloads where we spin up dozens of containers per suite, the startup time advantage alone makes containers the clear choice. The isolation trade-off is acceptable because we layer additional security (network disable, resource caps, anomaly detection) on top.

### Container Lifecycle Pattern

```
create → start → execute tools → capture state → stop → remove
                                                    ↑
                                          Signal handler cleanup
                                          (SIGINT/SIGTERM guard)
```

**Critical lesson learned**: On Windows with Docker Desktop, WSL2's memory overcommit behavior means OOM kills aren't always fatal — the kernel may use host swap instead. Tests must allow for both exit code 137 (OOM killed) and 0 (survived via swap).

### Active Container Registry

A global registry tracks all running containers by ID. This enables:
1. Emergency cleanup on process signals (SIGINT/SIGTERM)
2. Test auditing to verify zero container leakage
3. Concurrent container management for parallel task execution

---

## 3. Tool Execution Model

### Interception Architecture

Rather than letting agents call tools directly, Vigil interposes a recording layer:

```
Agent → ToolExecutor → AnomalyDetector → SandboxManager → Container
              ↓                                      ↓
        Record to DB                          Capture stdout/stderr
```

Every tool invocation captures:
- **Input arguments** (command string, file paths, content)
- **Standard output** (truncated to configurable limits)
- **Exit code** (process return status)
- **Duration** (wall-clock milliseconds)
- **Sequence number** (ordered position in the execution trace)

### Trade-off: Synchronous vs Async Execution

Vigil uses synchronous tool execution within each task. This was deliberate:
- **Simpler reasoning** about tool ordering and state dependencies
- **Cleaner error propagation** — a failed tool call immediately terminates the task
- **Deterministic replay** — tool sequences can be replayed in exact order

The cost is that parallel tool execution within a single task isn't supported. For evaluation purposes, this is acceptable — we want to observe sequential agent behavior, not optimize for throughput.

---

## 4. Anomaly Detection Layers

### Defense in Depth

Vigil implements three independent detection layers, each addressing a different attack surface:

1. **PathValidationLayer** — Scans for directory traversals (`../`) and absolute path escapes outside `/workspace`. Prevents filesystem breakout attempts.

2. **SubprocessAllowListScanner** — Blocks shell metacharacters (`|`, `;`, `&`, `` ` ``, `$`) and banned network commands (`curl`, `nc`, `ssh`, `wget`, `netcat`, `nmap`). Prevents command injection and data exfiltration.

3. **Loop Detector** — Tracks cumulative tool invocations per task against a configurable `max_tool_calls` limit. Prevents infinite loop resource exhaustion.

### Why Pre-Execution, Not Post-Execution?

Anomaly checks run **before** tool execution, not after. This is a deliberate security choice:
- A post-execution check would allow the dangerous action to complete before detection
- Pre-execution blocking prevents the attack vector entirely
- The trade-off is potential false positives, but safety trumps convenience in an eval harness

---

## 5. Database & Persistence Strategy

### Schema Design

The database schema follows a hierarchical model:

```
EvalSuite (1) ──→ (N) EvalRun (1) ──→ (N) TaskResult (1) ──→ (N) ToolCall
                                                            ↘ (N) Anomaly
```

**Key decision**: Suite definitions are stored by name + agent version composite. This enables version-over-version comparison without duplicating task definitions.

### Session Management Pattern

All database access goes through a scoped `get_session()` context manager that:
1. Creates a session from the factory
2. Yields it for use
3. Commits on success, rolls back on any exception
4. Maps all SQLAlchemy errors to `DatabasePersistenceError`

**Gotcha discovered**: Raising non-DB exceptions (like `ValueError`) inside the session context causes them to be caught by the generic `except Exception` handler and wrapped as `DatabasePersistenceError`. API routes must handle both exception types.

### Alembic Migration Verification

The `vigil bootstrap` command compares database migration heads (returned as tuples from queries) against filesystem heads (returned as lists from the config). Comparing them requires converting both to sets — a subtle type mismatch that caused false "migrations out of sync" warnings during development.

---

## 6. Metrics & Comparison Engine

### Percentile Calculation

Vigil computes P50 (median) and P90 (tail) latency percentiles using the **linear interpolation method** (Excel PERCENTILE.INC variant):

```
rank = (percentile / 100) × (n - 1)
result = values[floor(rank)] + fraction × (values[ceil(rank)] - values[floor(rank)])
```

This provides smooth percentile estimates even for small sample sizes, which is important for evaluation suites that may only have 5-10 tasks.

### Run Comparison Differential

The comparator produces task-level diffs between two runs:
- **Status changes**: `PASS → FAIL` (regression) or `FAIL → PASS` (improvement)
- **Latency deltas**: Per-task duration differences in milliseconds
- **Step count deltas**: Changes in the number of tool invocations needed
- **Anomaly deltas**: Changes in detected anomaly counts

This enables data-driven decisions about prompt changes, model swaps, or tool modifications.

---

## 7. API & Dashboard Design

### Why FastAPI + Vanilla JS?

- **FastAPI**: Automatic OpenAPI/Swagger docs, Pydantic model integration, excellent Python async support. The auto-generated `/docs` endpoint alone saves significant development time.
- **Vanilla JS**: No build step, no node_modules, no framework churn. For an internal developer dashboard, framework complexity is unnecessary overhead.
- **Static file serving**: The SPA is mounted directly from FastAPI's `StaticFiles`, eliminating the need for a separate web server.

### Dashboard UX Decisions

- **Dark mode only**: Evaluation dashboards are developer tools, typically used in code-heavy environments where dark themes reduce eye strain.
- **Glassmorphism cards**: Subtle `backdrop-filter: blur()` effects provide visual depth without the performance cost of heavy animations.
- **Modal tool inspector**: Tool call sequences are shown in a modal overlay rather than inline, keeping the task results table scannable.

---

## 8. Testing Strategy

### Test Pyramid

```
                    ┌──────────┐
                    │   E2E    │  2 tests (happy path, full pipeline)
                   ┌┴──────────┴┐
                   │ Integration │  ~35 tests (Docker, DB, API, anomalies)
                  ┌┴────────────┴┐
                  │   Unit Tests  │  ~39 tests (config, assertions, metrics, models)
                  └──────────────┘
```

### Container Test Isolation

Integration tests that create Docker containers must:
1. **Label containers** with unique task IDs (`task-id={uuid}`) for filtering
2. **Audit after cleanup** to verify zero leaked containers matching the label
3. **Handle Windows Docker Desktop quirks** (swap-based OOM survival, named pipe connections)

### Database Test Isolation

Each integration test creates unique suite names and task slugs to avoid collisions with other tests. Tests use the same `get_session()` context manager as production code, ensuring realistic transaction behavior.

---

## 9. Lessons Learned

1. **Always raise exceptions outside context managers** that have generic `except` clauses. HTTPException raised inside `get_session()` gets wrapped as `DatabasePersistenceError`.

2. **Windows Docker Desktop uses named pipes** (`npipe:////./pipe/docker_engine`), not Unix sockets. The Docker SDK handles this transparently, but configuration must account for it.

3. **Signal handlers must explicitly unregister containers** from the active registry inside `finally` blocks. Without this, test auditors report phantom container leaks.

4. **Floating point percentile math** requires `pytest.approx()` assertions. Linear interpolation on sorted lists produces values like `90.10000000000001` rather than exact `90.1`.

5. **Alembic migration head comparison** must use set equality (`set(db_heads) == set(fs_heads)`) because the database returns tuples while the filesystem returns lists.

---

## 10. Future Considerations

- **Parallel task execution**: Running multiple tasks concurrently within a suite for faster evaluation cycles.
- **Streaming tool output**: WebSocket-based real-time tool output streaming to the dashboard.
- **Custom assertion plugins**: A plugin registry allowing users to define custom assertion strategies.
- **Multi-model comparison**: Automated A/B testing across different LLM providers with statistical significance testing.
- **Cost tracking**: Integrating LLM API token usage into the metrics engine for cost-per-evaluation reporting.
