import shlex
from typing import Union, List, Any
from langchain_core.tools import BaseTool
from pydantic import PrivateAttr

from vigil.core.tool_executor import ToolExecutor
from vigil.core.tool_models import ToolRequest

class VigilSandboxTool(BaseTool):
    name: str = "vigil_sandbox_exec"
    description: str = (
        "Execute a shell command inside the isolated sandbox container. "
        "The input command should be a list of strings, for example: ['ls', '-la'] or ['cat', 'file.txt']. "
        "If you want to run a python command, you can use ['python', '-c', 'your python code']. "
        "Returns the standard output of the command."
    )
    
    _executor: Any = None
    
    def __init__(self, executor: ToolExecutor, **kwargs: Any):
        super().__init__(**kwargs)
        object.__setattr__(self, "_executor", executor)
        
    def _run(self, command: Union[str, List[str]]) -> str:
        """
        Executes the command inside the sandbox container and returns the stdout.
        """
        if isinstance(command, str):
            # If the LLM sends a raw string, we route it through bash -c
            args = ["bash", "-c", command]
        elif isinstance(command, list):
            args = [str(arg) for arg in command]
        else:
            return "Error: Command must be a string or a list of strings."
            
        req = ToolRequest(
            tool_name=self.name,
            arguments=args,
            timeout_seconds=30
        )
        
        try:
            res = self._executor.execute(req)
            if res.exit_code != 0:
                err_msg = f"Command failed with exit code {res.exit_code}"
                if res.stderr:
                    err_msg += f"\nStderr: {res.stderr}"
                if res.stdout:
                    err_msg += f"\nStdout: {res.stdout}"
                return err_msg
            return res.stdout
        except Exception as e:
            return f"Harness Execution Error: {e}"
