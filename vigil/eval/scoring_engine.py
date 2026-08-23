import json
import logging
import os
import re
from typing import Any
import jsonschema

from vigil.eval.assertion_models import (
    AssertionSchema,
    FileExistsAssertion,
    FileContentMatchAssertion,
    ExitCodeAssertion,
    StdoutContainsAssertion,
    ToolCallCountAssertion,
    JsonSchemaAssertion,
)

logger = logging.getLogger(__name__)

class ScoringEngine:
    """
    Scoring engine to evaluate container terminal state and execution logs against assertions.
    """
    def __init__(self, workspace_path: str, tool_calls_log: list[Any]):
        self.workspace_path = workspace_path
        self.tool_calls_log = tool_calls_log
        self._assertion_results = {}

    @property
    def assertion_results(self) -> dict[str, bool]:
        """
        Returns a dictionary mapping assertion string representation to its boolean result.
        """
        return self._assertion_results

    def evaluate(self, assertions: list[AssertionSchema]) -> bool:
        """
        Evaluates a list of assertions.
        Returns True if ALL assertions pass (evaluate to True).
        """
        if not assertions:
            return True
            
        all_passed = True
        for assertion in assertions:
            # Perform assertion check
            passed = self._dispatch(assertion)
            
            # Apply negation logic
            final_result = passed if not assertion.negate else not passed
            
            # Store result
            assertion_key = f"{assertion.type}:{assertion.model_dump_json(exclude={'type', 'negate'})}"
            self._assertion_results[assertion_key] = final_result
            
            if not final_result:
                all_passed = False
                
        return all_passed

    def _dispatch(self, assertion: AssertionSchema) -> bool:
        try:
            if assertion.type == "file_exists":
                return self._assert_file_exists(assertion)
            elif assertion.type == "file_content_match":
                return self._assert_file_content_match(assertion)
            elif assertion.type == "exit_code":
                return self._assert_exit_code(assertion)
            elif assertion.type == "stdout_contains":
                return self._assert_stdout_contains(assertion)
            elif assertion.type == "tool_call_count":
                return self._assert_tool_call_count(assertion)
            elif assertion.type == "json_schema":
                return self._assert_json_schema(assertion)
        except Exception as e:
            logger.error(f"Assertion {assertion.type} failed with unhandled exception: {e}")
            return False
        return False

    def _assert_file_exists(self, assertion: FileExistsAssertion) -> bool:
        target_path = os.path.abspath(os.path.join(self.workspace_path, assertion.path.lstrip("/\\")))
        if not target_path.startswith(os.path.abspath(self.workspace_path)):
            return False
        return os.path.exists(target_path)

    def _assert_file_content_match(self, assertion: FileContentMatchAssertion) -> bool:
        target_path = os.path.abspath(os.path.join(self.workspace_path, assertion.path.lstrip("/\\")))
        if not target_path.startswith(os.path.abspath(self.workspace_path)) or not os.path.exists(target_path):
            return False
            
        try:
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return False
            
        if assertion.strategy == "exact":
            return assertion.pattern in content
        elif assertion.strategy == "regex":
            return bool(re.search(assertion.pattern, content))
        return False

    def _assert_exit_code(self, assertion: ExitCodeAssertion) -> bool:
        if not self.tool_calls_log:
            return False
        final_call = self.tool_calls_log[-1]
        return final_call.exit_code == assertion.expected_value

    def _assert_stdout_contains(self, assertion: StdoutContainsAssertion) -> bool:
        cumulative_stdout = "".join([call.stdout for call in self.tool_calls_log])
        if assertion.strategy == "exact":
            return assertion.pattern in cumulative_stdout
        elif assertion.strategy == "regex":
            return bool(re.search(assertion.pattern, cumulative_stdout))
        return False

    def _assert_tool_call_count(self, assertion: ToolCallCountAssertion) -> bool:
        return len(self.tool_calls_log) <= assertion.expected_value

    def _assert_json_schema(self, assertion: JsonSchemaAssertion) -> bool:
        target_path = os.path.abspath(os.path.join(self.workspace_path, assertion.path.lstrip("/\\")))
        if not target_path.startswith(os.path.abspath(self.workspace_path)) or not os.path.exists(target_path):
            return False
            
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return False
            
        # Determine and load schema (could be a path in workspace, file on host, or raw JSON string)
        schema = None
        
        # 1. Try loading as relative path inside workspace
        schema_work_path = os.path.abspath(os.path.join(self.workspace_path, assertion.schema_path.lstrip("/\\")))
        if schema_work_path.startswith(os.path.abspath(self.workspace_path)) and os.path.exists(schema_work_path):
            try:
                with open(schema_work_path, "r", encoding="utf-8") as f:
                    schema = json.load(f)
            except Exception:
                pass
                
        # 2. Try loading as absolute/relative path on host
        if schema is None and os.path.exists(assertion.schema_path):
            try:
                with open(assertion.schema_path, "r", encoding="utf-8") as f:
                    schema = json.load(f)
            except Exception:
                pass
                
        # 3. Try parsing as raw JSON string
        if schema is None:
            try:
                schema = json.loads(assertion.schema_path)
            except Exception:
                pass

        if schema is None:
            logger.error(f"JSON Schema could not be loaded from: {assertion.schema_path}")
            return False
            
        try:
            jsonschema.validate(instance=data, schema=schema)
            return True
        except jsonschema.ValidationError as e:
            logger.info(f"JSON Schema validation failed: {e.message}")
            return False
        except Exception as e:
            logger.error(f"Unhandled error during JSON Schema validation: {e}")
            return False
