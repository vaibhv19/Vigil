import os
import shutil
import tempfile
import json
import pytest

from vigil.eval.assertion_models import (
    FileExistsAssertion, FileContentMatchAssertion, ExitCodeAssertion,
    StdoutContainsAssertion, ToolCallCountAssertion, JsonSchemaAssertion
)
from vigil.eval.scoring_engine import ScoringEngine

class MockToolCall:
    def __init__(self, stdout: str, exit_code: int):
        self.stdout = stdout
        self.exit_code = exit_code

def test_assertions_scoring():
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create test files
        with open(os.path.join(temp_dir, "test.txt"), "w", encoding="utf-8") as f:
            f.write("Vigil evaluation engine assertions test.")
            
        json_data = {"status": "healthy", "metrics": {"cpu": 0.4}}
        with open(os.path.join(temp_dir, "data.json"), "w", encoding="utf-8") as f:
            json.dump(json_data, f)
            
        json_schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "metrics": {"type": "object"}
            },
            "required": ["status", "metrics"]
        }
        with open(os.path.join(temp_dir, "schema.json"), "w", encoding="utf-8") as f:
            json.dump(json_schema, f)

        # Mock tool call logs (exit code of the final tool call is 1)
        tool_calls = [
            MockToolCall("Initializing environment...\n", 0),
            MockToolCall("Processing math... completed successfully\n", 0),
            MockToolCall("Failed process call\n", 1)
        ]
        
        engine = ScoringEngine(temp_dir, tool_calls)
        
        # 1. file_exists
        assert engine.evaluate([FileExistsAssertion(type="file_exists", path="test.txt")])
        assert not engine.evaluate([FileExistsAssertion(type="file_exists", path="missing.txt")])
        assert engine.evaluate([FileExistsAssertion(type="file_exists", path="missing.txt", negate=True)])
        
        # 2. file_content_match exact
        assert engine.evaluate([
            FileContentMatchAssertion(type="file_content_match", path="test.txt", pattern="Vigil evaluation")
        ])
        assert not engine.evaluate([
            FileContentMatchAssertion(type="file_content_match", path="test.txt", pattern="Not found pattern")
        ])
        
        # 3. file_content_match regex
        assert engine.evaluate([
            FileContentMatchAssertion(
                type="file_content_match", path="test.txt", pattern="engine [a-z]+ test", strategy="regex"
            )
        ])
        
        # 4. exit_code
        assert engine.evaluate([ExitCodeAssertion(type="exit_code", expected_value=1)])
        assert not engine.evaluate([ExitCodeAssertion(type="exit_code", expected_value=0)])
        assert engine.evaluate([ExitCodeAssertion(type="exit_code", expected_value=0, negate=True)])
        
        # 5. stdout_contains exact
        assert engine.evaluate([StdoutContainsAssertion(type="stdout_contains", pattern="completed successfully")])
        assert not engine.evaluate([StdoutContainsAssertion(type="stdout_contains", pattern="Not printed stdout")])
        
        # 6. stdout_contains regex
        assert engine.evaluate([
            StdoutContainsAssertion(type="stdout_contains", pattern="Initial.*env", strategy="regex")
        ])
        
        # 7. tool_call_count
        assert engine.evaluate([ToolCallCountAssertion(type="tool_call_count", expected_value=5)])
        assert not engine.evaluate([ToolCallCountAssertion(type="tool_call_count", expected_value=2)])
        
        # 8. json_schema validation with file path
        assert engine.evaluate([
            JsonSchemaAssertion(type="json_schema", path="data.json", schema_path="schema.json")
        ])
        
        # 9. json_schema validation with raw string
        raw_schema = '{"type": "object", "properties": {"status": {"type": "string"}}}'
        assert engine.evaluate([
            JsonSchemaAssertion(type="json_schema", path="data.json", schema_path=raw_schema)
        ])
        
        # 10. json_schema mismatch failure
        bad_schema = '{"type": "object", "required": ["non_existent_field"]}'
        assert not engine.evaluate([
            JsonSchemaAssertion(type="json_schema", path="data.json", schema_path=bad_schema)
        ])
        
        # 11. Mixed assertions
        mixed = [
            FileExistsAssertion(type="file_exists", path="test.txt"),
            ExitCodeAssertion(type="exit_code", expected_value=1),
            ToolCallCountAssertion(type="tool_call_count", expected_value=3)
        ]
        assert engine.evaluate(mixed)
        assert len(engine.assertion_results) == 16

    finally:
        shutil.rmtree(temp_dir)
