from typing import Literal, Union, Annotated
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

# Discriminated Union definition using Pydantic v2 Annotated syntax
AssertionSchema = Annotated[
    Union[
        FileExistsAssertion,
        FileContentMatchAssertion,
        ExitCodeAssertion,
        StdoutContainsAssertion,
        ToolCallCountAssertion,
        JsonSchemaAssertion
    ],
    Field(discriminator="type")
]
