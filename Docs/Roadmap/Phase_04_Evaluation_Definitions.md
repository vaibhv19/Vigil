# Phase 04: Evaluation Definitions & Deterministic Scoring

## 1. Package / Folder Structure
```text
vigil/
├── eval/
│   ├── __init__.py
│   ├── assertion_models.py     # Pydantic Discriminated Assertion Schema
│   ├── task_models.py          # TaskDefinition and SuiteDefinition Pydantic models
│   ├── task_loader.py          # Loads YAML configurations and validates them
│   └── scoring_engine.py       # Executes state assertions against the sandbox
└── tests/
    ├── unit/
    │   ├── test_assertions.py  # Unit tests for assertion matching logic
    │   └── test_task_loader.py # Unit tests for task YAML validation
```

---

## 2. Purpose
This phase builds the evaluation engine. It handles loading and parsing of YAML task definitions, validates them against the strict Pydantic Discriminated Assertion Schema (rejecting invalid setups before run), injects starting files into the sandbox's workspace, inspects the terminal state of the sandbox filesystem after agent completion, dispatches assertions, and deterministically scores the results as PASS, FAIL, or ERROR.

---

## 3. Dependencies
### 3.1 Internal Modules
- `vigil.core.sandbox_manager` (To read files or verify paths inside the workspace)
- `vigil.core.tool_executor` (To inspect cumulative execution outcomes like stdout and tool counts)

### 3.2 External Libraries
- `pydantic` (For schema validation)
- `pyyaml` (For file parsing)
- `jsonschema` (For validating sandbox JSON files against custom schemas)

---

## 4. Inputs
- YAML task files containing prompts, context files, assertions, max steps, and categories.
- Workspace directory files and tool history logs after execution finishes.

---

## 5. Outputs
- Validated `TaskDefinition` settings objects.
- `TaskScoringResult` object containing overall status (PASS/FAIL/ERROR) and boolean result mapping for each assertion.

---

## 6. Public Interfaces
### 6.1 Assertion Schema (`vigil/eval/assertion_models.py`)
Matches the Pydantic Discriminated Assertion Schema defined in the Evaluation Harness Spec. It requires `negate: bool` (defaulting to `False`) for negative assertions. Undocumented alternatives like `expect_value` are strictly rejected by the validator.

```python
from typing import Literal, Union, Optional
from pydantic import BaseModel, Field

class BaseAssertion(BaseModel):
    negate: bool = Field(default=False, description="If True, asserts that the condition is NOT met.")

class FileExistsAssertion(BaseAssertion):
    type: Literal["file_exists"]
    path: str = Field(..., description="Path to target file relative to /workspace")

class FileContentMatchAssertion(BaseAssertion):
    type: Literal["file_content_match"]
    path: str = Field(..., description="Path to target file relative to /workspace")
    pattern: str = Field(..., description="Pattern to match in file content")
    strategy: Literal["exact", "regex"] = Field(default="exact", description="Matching strategy to use")

class ExitCodeAssertion(BaseAssertion):
    type: Literal["exit_code"]
    expected_value: int = Field(default=0, description="Expected process exit code")

class StdoutContainsAssertion(BaseAssertion):
    type: Literal["stdout_contains"]
    pattern: str = Field(..., description="Substring or pattern expected in cumulative stdout")
    strategy: Literal["exact", "regex"] = Field(default="exact", description="Matching strategy to use")

class ToolCallCountAssertion(BaseAssertion):
    type: Literal["tool_call_count"]
    expected_value: int = Field(..., description="Maximum allowed tool calls")

class JsonSchemaAssertion(BaseAssertion):
    type: Literal["json_schema"]
    path: str = Field(..., description="Path to target JSON file relative to /workspace")
    schema_path: str = Field(..., description="Path to expected JSON schema file or JSON schema string")

AssertionSchema = Union[
    FileExistsAssertion,
    FileContentMatchAssertion,
    ExitCodeAssertion,
    StdoutContainsAssertion,
    ToolCallCountAssertion,
    JsonSchemaAssertion
]
```

### 6.2 Task & Suite Models (`vigil/eval/task_models.py`)
```python
class ContextFile(BaseModel):
    path: str = Field(..., description="Target file path inside the sandbox workspace")
    content: str = Field(..., description="Initial contents of the file")

class TaskDefinition(BaseModel):
    task_id: str
    description: str
    input_prompt: str
    context: Optional[dict[str, list[ContextFile]]] = None
    expected_output: dict[str, list[AssertionSchema]]
    max_steps: int = Field(default=10, ge=1)
    category: str
```

### 6.3 Scoring Engine Interface (`vigil/eval/scoring_engine.py`)
```python
class ScoringEngine:
    def __init__(self, workspace_path: str, tool_calls_log: list[Any]): ...
    def evaluate(self, assertions: list[AssertionSchema]) -> bool: ... # Returns True if all pass
```

---

## 7. Internal Components
- **`AssertionDispatcher`**: Map matching assertion types to specific execution functions (`assert_file_exists`, `assert_regex_match`, etc.).
- **`TaskLoader`**: Utility reading file paths, resolving references, parsing YAML, and throwing `TaskDefinitionValidationError` if syntax or schema constraints fail.
- **`ContextInjector`**: Handles writing seed files defined in task yaml into the local host folder before Docker startup.

---

## 8. Development Prerequisites & Environment Bootstrap Checklist
- [ ] **Sample Task Definitions**: Prepare sample task YAML files under `tests/fixtures/tasks/` mapping assertions.
- [ ] **Validation tests**: Setup tests asserting Pydantic catches missing fields.

---

## 9. Atomic Implementation Task List

| Task ID | Description | Size | Risk | Prerequisites | Dependencies | Expected Output | Testing | Definition of Done |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **TS-4.1** | Implement Pydantic assertion models mapping discrimination types. | M | Low | TS-1.4 | None | Python models enforcing strict attributes. | Unit tests verifying correct schema generation. | Schema matches spec; reject attributes like `expect_value`. |
| **TS-4.2** | Implement Pydantic `TaskDefinition` and `SuiteDefinition` models. | S | Low | TS-4.1 | None | Parsing container classes validating config YAML structure. | Verify nested models parse sample configurations successfully. | Nested structures (including contexts) parse correctly. |
| **TS-4.3** | Implement `TaskLoader` class parsing and validating YAML structures. | M | Low | TS-4.2 | None | Parser loading files and throwing `TASK_DEFINITION_VALIDATION_ERROR` on failure. | Write unit tests for missing fields, bad types, and invalid assertions. | Invalid yaml files fail parsing safely and return clear errors. |
| **TS-4.4** | Implement `ContextInjector` writing initial sandbox files. | S | Low | TS-2.4, TS-4.2 | None | Directory prepared with initial files prior to container start. | Test verifying target folder contents match context config parameters. | Files are created with correct content and permissions. |
| **TS-4.5** | Implement standard assertions: `file_exists`, `file_content_match`. | M | Med | TS-4.1 | None | Evaluators checking workspace folder files. | Unit tests running exact and regex searches on sample files. | Correctly handles files, matching strategies, and the `negate` flag. |
| **TS-4.6** | Implement programmatic assertions: `exit_code`, `stdout_contains`, `tool_call_count`. | M | Low | TS-4.1 | None | Evaluators validating tool call structures. | Test checking list of mock tool outcomes. | Evaluation returns correct outcomes based on execution histories. |
| **TS-4.7** | Implement structured schema assertion: `json_schema`. | M | Med | TS-4.1 | None | JSON file content validation using `jsonschema` engine. | Test verifying JSON structures against schemas. | Evaluator correctly checks path, reads files, and parses structures. |
| **TS-4.8** | Implement `ScoringEngine` dispatching lists of assertions. | S | Low | TS-4.5, TS-4.6, TS-4.7 | None | Dispatched runner returning unified PASS/FAIL outcomes. | Integration tests checking combinations of mixed assertions. | Returns PASS only if all conditions evaluate successfully. |

---

## 10. Definition of Done (DoD)
- Discriminated models are validated correctly, ensuring negative checks rely on `negate: true`.
- Task definitions load and validate cleanly from file paths.
- Context injection writes starting directories and seed files correctly.
- Evaluators execute all six core assertion types, applying appropriate negation logic.
- Scoring engine returns PASS/FAIL/ERROR accurately based on physical states and execution logs.
- Validation suite passes.
