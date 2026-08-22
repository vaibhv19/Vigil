# Phase 11: Metrics & Comparison

## 1. Package / Folder Structure
```text
vigil/
├── eval/
│   ├── __init__.py
│   ├── metrics.py              # Statistical aggregations and latency percentiles
│   └── comparator.py           # Differential runs and version comparisons
└── tests/
    └── unit/
        ├── test_metrics.py     # Unit tests for latency and rate math
        └── test_comparator.py  # Unit tests for differential comparison logic
```

---

## 2. Purpose
This phase builds the evaluation analytics engine. It provides functions to query and aggregate historical execution logs stored in PostgreSQL, compute statistical metrics (P50/P90 latency percentiles, pass rates, and model usage costs), and compare runs (comparing Run A vs Run B to show how a prompt, model, or tool configuration change affected execution speeds and accuracy).

---

## 3. Dependencies
### 3.1 Internal Modules
- `vigil.db.connection` (To query database tables)
- `vigil.db.models` (To read ORM rows)

### 3.2 External Libraries
- **numpy**: `^1.26.0` (Optional / used for fast percentile math, or standard math library)
- **pydantic**: (To structure dashboard metrics JSON models)

---

## 4. Inputs
- Database rows from `eval_runs`, `task_results`, `tool_calls`, and `anomalies` tables.
- Query parameters (run IDs, suite IDs, agent version identifiers).

---

## 5. Outputs
- `SuiteMetrics` DTO summarizing execution statistics.
- `RunComparison` DTO displaying side-by-side changes in pass rates, execution latencies, tool counts, and anomaly logs.

---

## 6. Public Interfaces
### 6.1 Metrics Aggregator (`vigil/eval/metrics.py`)
```python
from pydantic import BaseModel
from datetime import datetime

class RunSummaryMetrics(BaseModel):
    run_id: str
    suite_id: str
    agent_version: str
    pass_rate: float
    total_tasks: int
    p50_latency_ms: float
    p90_latency_ms: float
    total_cost: float
    total_anomalies: int

class MetricsEngine:
    def __init__(self, session_factory): ...
    def get_run_metrics(self, run_id: str) -> RunSummaryMetrics: ...
```

### 6.2 Run Comparator (`vigil/eval/comparator.py`)
```python
class TaskComparison(BaseModel):
    task_id: str
    status_change: str # e.g. "PASS -> FAIL", "NO_CHANGE"
    latency_delta_ms: int
    steps_delta: int
    anomaly_delta: int

class RunComparison(BaseModel):
    run_id_a: str
    run_id_b: str
    pass_rate_delta: float
    task_changes: list[TaskComparison]

class RunComparator:
    def __init__(self, session_factory): ...
    def compare_runs(self, run_id_a: str, run_id_b: str) -> RunComparison: ...
```

---

## 7. Internal Components
- **`PercentileCalculator`**: Fast mathematical implementations parsing lists of integer durations to extract median (P50) and tail (P90) latencies.
- **`CostCalculator`**: Maps LLM token counts (if stored in execution settings) to monetary rates to log total run costs.

---

## 8. Development Prerequisites & Environment Bootstrap Checklist
- [ ] **Test run datasets**: Execute multiple tasks with different simulated latencies and versions to populate test rows in PostgreSQL.

---

## 9. Atomic Implementation Task List

| Task ID | Description | Size | Risk | Prerequisites | Dependencies | Expected Output | Testing | Definition of Done |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **TS-11.1** | Implement `RunSummaryMetrics` and `RunComparison` Pydantic models. | S | Low | TS-1.4 | None | Python DTO data classes. | Test validation of nested comparison fields. | Models validate correctly. |
| **TS-11.2** | Implement `PercentileCalculator` for P50 and P90 execution durations. | S | Low | TS-1.6 | None | Math helper returning percentiles from list data. | Unit test with known lists (e.g. 1 to 100). | Percentile math is correct and handles empty arrays. |
| **TS-11.3** | Implement database queries extracting metrics data per run. | M | Med | TS-7.5, TS-11.2 | None | Database query returning aggregated counts and arrays. | Mock database sessions and test queries. | Queries fetch latencies, costs, task results, and anomalies. |
| **TS-11.4** | Implement task-by-task differential logic in `RunComparator`. | M | Med | TS-7.5, TS-11.1 | None | Logic comparing task status, duration, steps, and anomalies. | Unit test passing mock task results for Run A and Run B. | Correctly maps status changes, step differentials, and deltas. |
| **TS-11.5** | Implement suite-level aggregate comparator showing version trends. | M | Low | TS-11.4 | None | Summary reports comparing Suite A vs Suite B. | Run comparator against mock databases and check outputs. | Reports track regression trends between agent versions. |
| **TS-11.6** | Create integration test verifying metrics calculation against real database data. | M | Med | TS-8.1, TS-11.3 | None | End-to-end analytics verified against real execution runs. | Run test suites, call metrics engine, check database values. | Calculated database stats match expected values. |

---

## 10. Definition of Done (DoD)
- The metrics engine queries PostgreSQL and calculates P50/P90 latencies and pass rates.
- The comparison engine calculates side-by-side differentials (status changes, step counts, latency deltas, and anomalies) between runs.
- Analytics models validate inputs and serialize summaries correctly.
- Integration tests confirm statistical calculations match database data.
