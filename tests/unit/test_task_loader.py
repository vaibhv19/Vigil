import os
import shutil
import tempfile
import pytest
from vigil.eval.task_loader import TaskLoader, ContextInjector
from vigil.core.exceptions import TaskDefinitionValidationError

def test_load_valid_task():
    task = TaskLoader.load_task("tests/fixtures/tasks/valid_task.yaml")
    assert task.task_id == "create-and-write-file"
    assert task.max_steps == 3
    assert len(task.context.files) == 1
    assert task.context.files[0].path == "config.json"
    assert len(task.expected_output["assertions"]) == 6

def test_load_invalid_task_raises_error():
    with pytest.raises(TaskDefinitionValidationError) as exc_info:
        TaskLoader.load_task("tests/fixtures/tasks/invalid_task.yaml")
    # Pydantic validation error should mention expected_output or max_steps
    assert "expected_output" in str(exc_info.value) or "max_steps" in str(exc_info.value)

def test_load_non_existent_file_raises_error():
    with pytest.raises(TaskDefinitionValidationError) as exc_info:
        TaskLoader.load_task("tests/fixtures/tasks/non_existent.yaml")
    assert "Task definition file not found" in str(exc_info.value)

def test_context_injector():
    task = TaskLoader.load_task("tests/fixtures/tasks/valid_task.yaml")
    
    # Create temp directory as our workspace
    temp_dir = tempfile.mkdtemp()
    try:
        ContextInjector.inject_context(temp_dir, task)
        
        # Verify injected file content
        injected_file_path = os.path.join(temp_dir, "config.json")
        assert os.path.exists(injected_file_path)
        with open(injected_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert content == '{"debug": true}'
    finally:
        shutil.rmtree(temp_dir)

def test_context_injector_directory_traversal_prevention():
    # Attempting a directory traversal escape in path should raise ValueError
    from vigil.eval.task_models import TaskDefinition, ContextFile, TaskContext
    task = TaskDefinition(
        task_id="traversal-test",
        description="test",
        input_prompt="test",
        category="test",
        expected_output={"assertions": []},
        context=TaskContext(files=[ContextFile(path="../escaped.txt", content="escape")])
    )
    
    temp_dir = tempfile.mkdtemp()
    try:
        with pytest.raises(ValueError) as exc_info:
            ContextInjector.inject_context(temp_dir, task)
        assert "escaped.txt" in str(exc_info.value) or "workspace" in str(exc_info.value)
    finally:
        shutil.rmtree(temp_dir)
