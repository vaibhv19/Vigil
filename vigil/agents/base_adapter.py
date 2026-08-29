from abc import ABC, abstractmethod
from vigil.core.tool_executor import ToolExecutor


class BaseAgentAdapter(ABC):
    @abstractmethod
    def run_task(self, prompt: str, tool_executor: ToolExecutor) -> str:
        """
        Executes the agent reasoning loop against the prompt, registering
        available tools that route command execution to the tool_executor.
        Returns the agent's final text response.
        """
        pass
