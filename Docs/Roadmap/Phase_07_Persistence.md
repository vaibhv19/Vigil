# Phase 07: Persistence

## 1. Package / Folder Structure
```text
vigil/
├── db/
│   ├── __init__.py
│   ├── connection.py           # Database engine & session setup
│   ├── models.py               # SQLAlchemy ORM models
│   ├── repository.py           # Data access objects (DAOs) for database operations
│   └── migrations/             # Alembic migration scripts
│       ├── env.py
│       └── script.py.mako
alembic.ini                     # Migration configuration
└── tests/
    ├── integration/
    │   └── test_persistence.py # Integration tests for database operations
```

---

## 2. Purpose
This phase implements the data storage layer. It sets up database connection configurations, defines relational database models using SQLAlchemy ORM (including tables for suites, tasks, runs, results, tool calls, and anomalies), initializes database schema migrations via Alembic, and writes persistence adapters to record execution metrics, terminal statuses, and tool execution history directly into PostgreSQL.

---

## 3. Dependencies
### 3.1 Internal Modules
- `vigil.config` (For connection parameters)
- `vigil.eval.task_models` (To map task schemas to SQL tables)

### 3.2 External Libraries
- **sqlalchemy**: `^2.0.0` (ORM database wrapper)
- **alembic**: `^1.13.0` (Database migrations)
- **psycopg2-binary**: `^2.9.9` (Postgres driver)
- **pydantic**: (To validate execution configuration payloads)

### 3.3 Runtime / OS Dependencies
- **PostgreSQL 16.0**: Running and reachable (configured via Docker Compose in Phase 1).

---

## 4. Inputs
- Configuration metadata from active runs (`execution_config`).
- Execution records (`ToolResult`, `TaskScoringResult`).
- Anomaly alerts generated during execution.

---

## 5. Outputs
- Schema tables established in the database.
- Executed rows inserted into database tables.
- `DatabasePersistenceError` on database connection or serialization failure.

---

## 6. Public Interfaces
### 6.1 Database Models (`vigil/db/models.py`)
All timestamps use timezone-aware SQL datatypes (`TIMESTAMPTZ` / `DateTime(timezone=True)`).

```python
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Text, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class EvalSuite(Base):
    __tablename__ = "eval_suites"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    agent_version: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(Text)
    input_prompt: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[dict] = mapped_column(JSON) # Pydantic serialized schema
    max_steps: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(100))

class EvalSuiteTask(Base):
    __tablename__ = "eval_suite_tasks"
    suite_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eval_suites.id"), primary_key=True)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"), primary_key=True)
    execution_order: Mapped[int] = mapped_column(Integer)

class EvalRun(Base):
    __tablename__ = "eval_runs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    suite_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eval_suites.id"))
    status: Mapped[str] = mapped_column(String(50)) # Strictly: RUNNING, COMPLETED, FAILED
    total_cost: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0000)
    total_duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    execution_config: Mapped[dict] = mapped_column(JSON) # Snapshots versions, prompt settings, tools
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

class TaskResult(Base):
    __tablename__ = "task_results"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eval_runs.id"))
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id"))
    status: Mapped[str] = mapped_column(String(50)) # Strictly: PASS, FAIL, ERROR
    failure_reason: Mapped[str] = mapped_column(String(100), nullable=True) # LOOP_DETECTED, ASSERTION_FAILED, etc.
    final_output: Mapped[str] = mapped_column(Text, nullable=True)
    steps_taken: Mapped[int] = mapped_column(Integer, default=0)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class ToolCall(Base):
    __tablename__ = "tool_calls"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("task_results.id"))
    sequence_number: Mapped[int] = mapped_column(Integer)
    tool_name: Mapped[str] = mapped_column(String(255))
    input_args: Mapped[dict] = mapped_column(JSON)
    stdout_capture: Mapped[str] = mapped_column(Text)
    exit_code: Mapped[int] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

class Anomaly(Base):
    __tablename__ = "anomalies"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("task_results.id"))
    pattern_type: Mapped[str] = mapped_column(String(50)) # LOOP, PATH, PROCESS
    severity: Mapped[str] = mapped_column(String(50)) # WARNING, CRITICAL
    incident_data: Mapped[dict] = mapped_column(JSON)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
```

---

## 7. Internal Components
- **`DatabaseConnection`**: Manages connection pooling, engine initialization, session transactions, and exception mappings.
- **`ExecutionConfigSnapshotter`**: Helper class compiling current execution configuration parameters (agent version, LLM name, configurations) into a structured dictionary.
- **`PersistenceService`**: Central coordinator containing SQL insert/update commands for the runner.

---

## 8. Development Prerequisites & Environment Bootstrap Checklist
- [ ] **Database up**: Verify that PostgreSQL container is running on port `5432` from Phase 1.
- [ ] **Alembic Initialize**: Run `alembic init db/migrations` inside the directory, setting target path config inside `alembic.ini`.

---

## 9. Atomic Implementation Task List

| Task ID | Description | Size | Risk | Prerequisites | Dependencies | Expected Output | Testing | Definition of Done |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **TS-7.1** | Setup Alembic configuration mapping environment database URLs. | S | Low | TS-1.2, TS-1.4 | None | Validated `alembic.ini` pointing to correct environment variables. | Verify alembic runs `alembic current`. | Setup config loads target connection variables cleanly. |
| **TS-7.2** | Implement ORM database models using SQLAlchemy Declarative syntax. | M | Low | TS-1.4 | None | Models matching schema definitions, utilizing `TIMESTAMPTZ` and `JSON` columns. | Verify model class definitions load without warnings. | All tables and relationships are correctly declared. |
| **TS-7.3** | Generate and apply baseline database migrations using Alembic. | M | Med | TS-7.1, TS-7.2 | None | Auto-generated script applying columns on database. | Run `alembic upgrade head` and verify tables exist via client. | Database schema matches defined models. |
| **TS-7.4** | Implement connection pool and transaction manager (`vigil/db/connection.py`). | S | Low | TS-1.4 | None | Helper session manager handling context scopes. | Test opening connection, running query, and releasing connection. | Context managers cleanly close sessions and clean up resources. |
| **TS-7.5** | Implement `Repository` data access routines for runs and results persistence. | M | Med | TS-7.2, TS-7.4 | None | DAO functions inserting and updating execution tables. | Test saving `EvalSuite`, `Task`, `EvalRun` (status lifecycle). | DB commits occur safely and handle errors. |
| **TS-7.6** | Implement `Repository` data access routines for tool calls and anomalies. | M | Low | TS-7.2, TS-7.4 | None | DAO functions inserting rows into logs tables. | Save sample tool call and query output checks. | Records persist, maintaining foreign key linkages. |
| **TS-7.7** | Integrate persistence operations within `EvalRunner` lifecycle stages. | M | High | TS-6.2, TS-7.5, TS-7.6 | None | Runner updates execution runs and task results in DB in real-time. | Run full task runner, check database table contents. | All execution records are populated in database on run completion. |
| **TS-7.8** | Implement persistence error handling (`DATABASE_PERSISTENCE_ERROR`). | S | Med | TS-7.7 | None | Harness stops execution and raises clean error when database fails. | Block port 5432, run execution, check error outputs. | Database failures are detected; no silent silences or undocumented JSONL fallbacks. |

---

## 10. Definition of Done (DoD)
- Alembic database migration scripts initialize tables on PostgreSQL.
- ORM models represent defined schemas, using `DateTime(timezone=True)` (TIMESTAMPTZ) and JSONB columns.
- Runs log states (`RUNNING`, `COMPLETED`, `FAILED`) and outcomes (`PASS`, `FAIL`, `ERROR`) correctly.
- Task results capture specific failure reasons (e.g. `LOOP_DETECTED`, `ASSERTION_FAILED`) separately from statuses.
- Persistence integration in `EvalRunner` saves executions, tool details, and anomalies.
- Database persistence failures raise `DATABASE_PERSISTENCE_ERROR` and abort safely without fallback dumps.
- Full integration test suite passes.
