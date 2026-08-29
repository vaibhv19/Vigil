from typing import Optional
from pydantic import BaseModel, Field
from vigil.eval.assertion_models import AssertionSchema

class ContextFile(BaseModel):
    path: str = Field(..., description="Target file path inside the sandbox workspace (relative to /workspace)")
    content: str = Field(..., description="Initial contents of the file")

class TaskContext(BaseModel):
    files: list[ContextFile] = Field(default_factory=list, description="List of files to seed in workspace")

class TaskDefinition(BaseModel):
    task_id: str
    description: str
    input_prompt: str
    context: Optional[TaskContext] = Field(default=None, description="Initial workspace files to inject")
    expected_output: dict[str, list[AssertionSchema]] = Field(
        ..., 
        description="Scoring criteria assertions. Usually maps 'assertions' -> list of AssertionSchema"
    )
    max_steps: int = Field(default=10, ge=1, description="Maximum execution steps allowed for this task")
    category: str = Field(..., description="Evaluation category (e.g. safety, bash_execution)")

