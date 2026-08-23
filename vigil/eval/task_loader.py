import os
import logging
import yaml
from pydantic import ValidationError
from vigil.eval.task_models import TaskDefinition, SuiteDefinition
from vigil.core.exceptions import TaskDefinitionValidationError

logger = logging.getLogger(__name__)

class ContextInjector:
    """
    Handles writing seed files defined in task YAML into the local host folder before container starts.
    """
    @staticmethod
    def inject_context(workspace_path: str, task_def: TaskDefinition) -> None:
        """
        Writes all context files into the workspace directory.
        """
        if not task_def.context or not task_def.context.files:
            return
            
        for context_file in task_def.context.files:
            if os.path.isabs(context_file.path) or ".." in context_file.path:
                raise ValueError(f"Context file path contains invalid absolute path or directory traversal: {context_file.path}")
                
            target_path = os.path.abspath(os.path.join(workspace_path, context_file.path))
            
            if not target_path.startswith(os.path.abspath(workspace_path)):
                raise ValueError(f"Context file path tries to escape workspace: {context_file.path}")
                
            try:
                # Ensure parent directories exist
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(context_file.content)
                    
                # Ensure the file is writable inside the container
                os.chmod(target_path, 0o666)
                logger.info(f"Injected context file: {target_path}")
            except Exception as e:
                raise OSError(f"Failed to inject context file {context_file.path}: {e}")


class TaskLoader:
    """
    Utility to load and parse YAML configurations for tasks and suites.
    """
    @staticmethod
    def load_task(file_path: str) -> TaskDefinition:
        """
        Loads and validates a TaskDefinition from a YAML file.
        Raises TaskDefinitionValidationError on failure.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                raise TaskDefinitionValidationError(f"Task file is empty: {file_path}")
            return TaskDefinition.model_validate(data)
        except FileNotFoundError:
            raise TaskDefinitionValidationError(f"Task definition file not found: {file_path}")
        except yaml.YAMLError as e:
            raise TaskDefinitionValidationError(f"Invalid YAML syntax in {file_path}: {e}")
        except ValidationError as e:
            raise TaskDefinitionValidationError(f"Schema validation failed for {file_path}: {e}")

    @staticmethod
    def load_suite(file_path: str) -> SuiteDefinition:
        """
        Loads and validates a SuiteDefinition from a YAML file.
        Raises TaskDefinitionValidationError on failure.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                raise TaskDefinitionValidationError(f"Suite file is empty: {file_path}")
            return SuiteDefinition.model_validate(data)
        except FileNotFoundError:
            raise TaskDefinitionValidationError(f"Suite definition file not found: {file_path}")
        except yaml.YAMLError as e:
            raise TaskDefinitionValidationError(f"Invalid YAML syntax in {file_path}: {e}")
        except ValidationError as e:
            raise TaskDefinitionValidationError(f"Schema validation failed for {file_path}: {e}")
