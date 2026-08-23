import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """
    SQLAlchemy Declarative Base
    """
    pass

class EvalSuite(Base):
    __tablename__ = "eval_suites"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    agent_version: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(Text)
    input_prompt: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[dict] = mapped_column(JSON)  # Serialized Pydantic models schema
    max_steps: Mapped[int] = mapped_column(Integer)
    category: Mapped[str] = mapped_column(String(100))

class EvalSuiteTask(Base):
    __tablename__ = "eval_suite_tasks"
    suite_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eval_suites.id", ondelete="CASCADE"), primary_key=True)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    execution_order: Mapped[int] = mapped_column(Integer)

class EvalRun(Base):
    __tablename__ = "eval_runs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    suite_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eval_suites.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(50))  # RUNNING, COMPLETED, FAILED
    total_cost: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0000)
    total_duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    execution_config: Mapped[dict] = mapped_column(JSON)  # Snapshots of LLM name, settings, config
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

class TaskResult(Base):
    __tablename__ = "task_results"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eval_runs.id", ondelete="CASCADE"))
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(50))  # PASS, FAIL, ERROR
    failure_reason: Mapped[str] = mapped_column(String(100), nullable=True)  # LOOP_DETECTED, ASSERTION_FAILED, etc.
    final_output: Mapped[str] = mapped_column(Text, nullable=True)
    steps_taken: Mapped[int] = mapped_column(Integer, default=0)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class ToolCall(Base):
    __tablename__ = "tool_calls"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("task_results.id", ondelete="CASCADE"))
    sequence_number: Mapped[int] = mapped_column(Integer)
    tool_name: Mapped[str] = mapped_column(String(255))
    input_args: Mapped[dict] = mapped_column(JSON)
    stdout_capture: Mapped[str] = mapped_column(Text)
    exit_code: Mapped[int] = mapped_column(Integer, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class Anomaly(Base):
    __tablename__ = "anomalies"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("task_results.id", ondelete="CASCADE"))
    pattern_type: Mapped[str] = mapped_column(String(50))  # LOOP, PATH, PROCESS
    severity: Mapped[str] = mapped_column(String(50))  # WARNING, CRITICAL
    incident_data: Mapped[dict] = mapped_column(JSON)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
