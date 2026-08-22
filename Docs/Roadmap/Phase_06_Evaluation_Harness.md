# Phase 06: Evaluation Harness & Pytest Integration

## 1. Package / Folder Structure
```text
vigil/
├── eval/
│   ├── __init__.py
│   ├── runner.py               # EvalRunner orchestrator
│   └── reporter.py             # Console and file report compiler
├── conftest.py                 # Project-level Pytest fixtures (sandbox mounts)
└── tests/
    └── integration/
        └── test_eval_runner.py # Integration tests for complete task evaluation flow
```

---

## 2. Purpose
This phase constructs the central evaluation driver. It creates the `EvalRunner` which orchestrates the complete execution lifecycle (loading tasks, launching sandboxes, writing initial context files, starting adapters, waiting for completion, checking state assertions, and generating run reports). Additionally, this phase integrates the harness with **Pytest** via custom fixtures and reporting plugins, allowing developers to trigger evaluation runs using standard test commands.

---

## 3. Dependencies
### 3.1 Internal Modules
- `vigil.core.sandbox_manager` (For sandbox provisioning)
- `vigil.core.tool_executor` (For capturing tool logs)
- `vigil.eval.task_loader` (For loading and validating tasks)
- `vigil.eval.scoring_engine` (For state scoring logic)
- `vigil.agents.base_adapter` (To invoke agents)

### 3.2 External Libraries
- `pytest` (Testing framework lifecycle)
- `rich` (For rendering progress bars and stdout tables)

---

## 4. Inputs
- Path to task YAML file or directories containing tasks.
- Target agent adapter instance.
- System configurations (timeout values, output directories).

---

## 5. Outputs
- Harness execution reports saved as JSON files (e.g. `report-<timestamp>.json`).
- Nicely formatted console output displaying progress and summaries.
- Clean exit codes signaling test success/failure.

---

## 6. Public Interfaces
### 6.1 Eval Runner (`vigil/eval/runner.py`)
```python
from typing import Any
from vigil.agents.base_adapter import BaseAgentAdapter
from vigil.eval.task_models import TaskDefinition

class EvalRunner:
    def __init__(self, agent_adapter: BaseAgentAdapter, host_workspace_base: str):
        self.agent_adapter = agent_adapter
        self.host_workspace_base = host_workspace_base

    def run_task(self, task: TaskDefinition) -> dict[str, Any]:
        """
        Orchestrates sandbox startup, context injection, agent execution,
        assertion scoring, and teardown. Guarantees cleanup on failure.
        """
        pass

    def run_suite(self, task_dir: str) -> list[dict[str, Any]]: ...
```

### 6.2 Pytest Integration (`vigil/conftest.py`)
```python
import pytest
from vigil.core.sandbox_manager import SandboxManager

@pytest.fixture
def sandbox(request):
    """
    Fixture providing an isolated SandboxManager instance for testing.
    Guarantees container removal and temporary directory cleanup.
    """
    # Setup
    manager = SandboxManager(...)
    yield manager
    # Teardown
    manager.destroy_sandbox()
```

---

## 7. Internal Components
- **`VigilEvalReporter`**: Custom Pytest reporter hooks (`pytest_runtest_logreport`) translating test outcomes into structured reports.
- **`ExecutionLifecycleWrapper`**: Try/finally blocks safeguarding execution scopes.
- **`ConsoleFormatter`**: Generates CLI summary tables showing status (PASS/FAIL/ERROR) per task.

---

## 8. Development Prerequisites & Environment Bootstrap Checklist
- [ ] **Mocks compiled**: Ensure all components (Sandbox manager, Tool executor, Scoring engine, Agent adapter) are functional and verified.
- [ ] **Pytest configuration**: Set up pytest default arguments inside `pyproject.toml` or `pytest.ini`.

---

## 9. Atomic Implementation Task List

| Task ID | Description | Size | Risk | Prerequisites | Dependencies | Expected Output | Testing | Definition of Done |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **TS-6.1** | Implement project-level `conftest.py` with custom `sandbox` fixture. | S | Low | TS-2.8 | None | Shareable pytest fixture providing clean container instances. | Test using fixture inside mock test file, check teardown. | Fixture provides sandbox and cleanly destroys it after test exits. |
| **TS-6.2** | Implement `EvalRunner.run_task` lifecycle execution manager. | L | High | TS-3.5, TS-4.4, TS-4.8, TS-5.4 | None | Orchestrated execution function running end-to-end steps. | Integration test utilizing mock agent and mock assertions. | Coordinates container spin-up, injection, exec, scoring, cleanup. |
| **TS-6.3** | Implement robust error mapping inside `EvalRunner` (e.g. `SANDBOX_PROVISION_ERROR`). | M | Med | TS-6.2 | TS-3.1 | Uncaught exceptions map to proper statuses. | Force provisioning fail and verify task logs output `ERROR`. | Uncaught exceptions map to `ERROR` and execute cleanup. |
| **TS-6.4** | Implement `EvalRunner.run_suite` reading directories and metadata files. | S | Low | TS-4.3, TS-6.2 | None | Sequentially executes multiple tasks inside folder. | Verify runner loops over task suite folder. | Runs suite sequentially, returning list of results. |
| **TS-6.5** | Implement `VigilEvalReporter` translating execution runs to reports. | M | Low | TS-6.2 | None | JSON file compiler outputting suite summary metrics. | Run suite, check JSON file keys and correctness. | Saves structured JSON summaries with accurate counts. |
| **TS-6.6** | Implement console CLI formatter using `rich` framework. | S | Low | TS-6.5 | None | Formatted table output printed to developer console. | Execute suite; verify terminal displays output. | Console renders details of PASS/FAIL/ERROR per task. |
| **TS-6.7** | Write integration tests checking cleanup under failure and timeouts. | M | High | TS-6.2 | None | Container is stopped and removed, temp directory is deleted. | Simulate runner timeout or assertion error, verify host cleanup. | No docker container or host folder leaks remain. |

---

## 10. Definition of Done (DoD)
- Pytest fixtures provide clean sandbox instances with automated teardown.
- `EvalRunner` orchestrates the complete execution flow from loading definitions to running assertions.
- Errors are mapped to PASS/FAIL/ERROR correctly, and uncaught execution issues result in ERROR.
- Teardown of Docker containers and temporary directories is guaranteed (100% cleanup) under all conditions (pass, fail, crash, or timeouts).
- Execution produces console tables and structured JSON reports.
- Comprehensive integration tests pass.
