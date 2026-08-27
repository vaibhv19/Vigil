# Vigil: Autonomous Agent Evaluation Harness & Safe-Runtime Sandbox

Vigil is a programmatic evaluation harness that runs AI agents inside ephemeral, resource-constrained Docker sandboxes. It replaces subjective "vibes" with hard, state-based assertions while ensuring the host system is never at risk.

> **Vigil does not train, fine-tune, or modify agents.** It observes, measures, and reports what they actually do.

---

## Related Writing

* [Designing for Failure](https://vaibhav19.vercel.app/writing/when-model-answered-isnt-enough)
* [Building Agents Twice](https://vaibhav19.vercel.app/writing/building-multi-agent-systems-twice-from-context-unification-to-agent-evaluation)
* [ENGINEERING JOURNEY](https://vaibhav19.vercel.app/writing/engineering-journey)

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Sandboxed Execution** | Every agent task runs inside an isolated Docker container with CPU, memory, network, and filesystem limits. |
| **Tool Execution Engine** | Intercepts and records every tool call (bash, file write, file read) with stdout capture, exit codes, and duration. |
| **State-Based Assertions** | Evaluates agent output using pluggable assertion strategies — file existence, content matching, exit code checks. |
| **Anomaly Detection** | Real-time monitoring for path traversals, shell injection metacharacters, banned commands, and infinite loops. |
| **Database Persistence** | All runs, task results, tool call logs, and anomalies are persisted to PostgreSQL via SQLAlchemy + Alembic. |
| **Metrics & Comparison** | Aggregates P50/P90 latency percentiles, pass rates, and provides side-by-side run differential comparisons. |
| **REST API & Dashboard** | FastAPI-powered REST endpoints with a premium dark-mode single-page dashboard for browsing runs and comparing versions. |
| **CLI Tooling** | `vigil run` to execute evaluation suites, `vigil bootstrap` to diagnose environment setup. |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Vigil CLI                           │
│                  (Typer / Click)                         │
├─────────────────────────────────────────────────────────┤
│                   EvalRunner                            │
│          (Orchestrates suite execution)                  │
├────────────┬────────────┬───────────────────────────────┤
│  Sandbox   │    Tool    │        Anomaly                │
│  Manager   │  Executor  │       Detector                │
│ (Docker)   │ (bash/rw)  │  (path/proc/loop)             │
├────────────┴────────────┴───────────────────────────────┤
│              Agent Adapter Layer                        │
│         (LangGraph / Custom Agents)                     │
├─────────────────────────────────────────────────────────┤
│            Database Persistence                         │
│      (PostgreSQL / SQLAlchemy / Alembic)                │
├─────────────────────────────────────────────────────────┤
│          FastAPI REST API + Dashboard                   │
│       (Runs, Metrics, Comparisons, SPA UI)              │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- **Python** ≥ 3.12
- **Docker Desktop** (running)
- **PostgreSQL** (local or containerized)
- **Poetry** (dependency management)

### Installation

```bash
# Clone the repository
git clone https://github.com/vaibhv19/Vigil.git
cd Vigil

# Install dependencies
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your database URL and Docker settings
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | *(Required)* |
| `DOCKER_HOST_URL` | Docker daemon URL | `unix:///var/run/docker.sock` |
| `WORKSPACE_BASE_DIR` | Absolute host path for temp workspaces | *(Required)* |
| `ENV` | Application environment | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Database Setup

```bash
# Run migrations
poetry run alembic upgrade head

# Verify environment
poetry run vigil bootstrap
```

### Running an Evaluation

```bash
# Execute a suite of evaluation tasks
poetry run vigil run --suite path/to/tasks/ --name "My Suite" --agent-version v1.0

# Start the dashboard
poetry run uvicorn vigil.api.main:app --reload
# Open http://localhost:8000
```

### Running Tests

```bash
# Run full test suite
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run specific test categories
poetry run pytest tests/unit/          # Unit tests only
poetry run pytest tests/integration/   # Integration tests only
```

---

## Project Structure

```
vigil/
├── cli/                    # CLI commands (run, bootstrap)
│   ├── main.py             # Typer application entry point
│   └── commands/           # Subcommand implementations
├── core/                   # Core domain logic
│   ├── config.py           # Pydantic settings configuration
│   ├── sandbox_manager.py  # Docker container lifecycle
│   ├── sandbox_config.py   # Resource limit dataclasses
│   ├── tool_executor.py    # Tool call interception & recording
│   ├── anomaly_detector.py # Real-time anomaly monitoring
│   ├── path_validator.py   # Filesystem escape detection
│   ├── subprocess_monitor.py # Shell injection detection
│   └── exceptions.py       # Domain exception hierarchy
├── eval/                   # Evaluation engine
│   ├── runner.py           # Suite/task orchestration
│   ├── assertions.py       # Pluggable assertion strategies
│   ├── task_loader.py      # YAML task definition parser
│   ├── task_models.py      # Task/Suite Pydantic models
│   ├── metrics.py          # Statistical aggregation engine
│   └── comparator.py       # Run differential comparison
├── agents/                 # Agent adapter layer
│   └── langgraph_adapter.py # LangGraph integration
├── db/                     # Database layer
│   ├── models.py           # SQLAlchemy ORM models
│   ├── connection.py       # Session factory & transactions
│   ├── repository.py       # Data access object (DAO)
│   └── migrations/         # Alembic migration scripts
├── api/                    # REST API & Dashboard
│   ├── main.py             # FastAPI application
│   ├── routes/             # API endpoint routers
│   └── static/             # SPA dashboard (HTML/CSS/JS)
└── tests/
    ├── unit/               # Pure logic tests
    └── integration/        # Docker + DB integration tests
```

---

## Dashboard

The Vigil dashboard is a premium dark-mode single-page application served directly from the FastAPI backend. It provides:

- **Runs List** — Browse historical evaluation runs with status badges and duration indicators.
- **Run Detail** — View per-task results, metrics (P50/P90 latency, pass rates), and anomaly logs.
- **Tool Call Inspector** — Click through individual tool call sequences with stdout output and exit codes.
- **Run Comparison** — Select two runs for side-by-side differential analysis showing status changes, latency deltas, and regression indicators.

Start the dashboard:
```bash
poetry run uvicorn vigil.api.main:app --reload
```

---

## Safety & Isolation

Vigil enforces strict security boundaries:

- **Container Isolation**: Each task runs in its own ephemeral Docker container with no host filesystem access.
- **Resource Caps**: CPU, memory, and PID limits prevent resource exhaustion attacks.
- **Network Disabled**: Containers cannot make outbound network requests by default.
- **Path Validation**: All tool arguments are scanned for directory traversals (`..`) and absolute path escapes.
- **Process Monitoring**: Shell metacharacters (`|`, `;`, `&`, `` ` ``) and banned commands (`curl`, `nc`, `ssh`, `wget`) are blocked.
- **Loop Detection**: Runaway agent loops are terminated after exceeding configurable step limits.
- **Signal Cleanup**: Emergency container pruning on SIGINT/SIGTERM ensures no orphaned containers persist.

---

## License

This project is for portfolio and educational purposes.
