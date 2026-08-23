from typing import Any, List, Optional
import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

from vigil.agents.langgraph_adapter import LangGraphAgentAdapter
from vigil.core.sandbox_config import SandboxConfig
from vigil.core.sandbox_manager import Sandbox
from vigil.core.tool_executor import ToolExecutor
from vigil.core.exceptions import AgentExecutionError
from vigil.config import get_settings

class MockChatModel(BaseChatModel):
    """
    Mock LLM that returns a pre-defined sequence of responses.
    """
    messages_to_return: List[AIMessage]
    calls_count: int = 0
    
    def _generate(self, messages: List[BaseMessage], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        if self.calls_count >= len(self.messages_to_return):
            # Default fallback
            msg = AIMessage(content="Fallback final response")
        else:
            msg = self.messages_to_return[self.calls_count]
            self.calls_count += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])
        
    def bind_tools(self, tools: list, **kwargs: Any) -> Any:
        return self

    @property
    def _llm_type(self) -> str:
        return "mock-chat-model"


def test_langgraph_adapter_success():
    # Define tool call sequence
    tool_call = {
        "name": "vigil_sandbox_exec",
        "args": {"command": ["echo", "Mocked Output"]},
        "id": "call_123",
        "type": "tool_call"
    }
    
    responses = [
        AIMessage(content="", tool_calls=[tool_call]),
        AIMessage(content="Final response from mock agent.")
    ]
    
    mock_llm = MockChatModel(messages_to_return=responses)
    
    # Initialize adapter with mock LLM
    adapter = LangGraphAgentAdapter(llm=mock_llm, max_steps=5)
    
    config = SandboxConfig()
    settings = get_settings()
    
    with Sandbox(config, settings.WORKSPACE_BASE_DIR, "test-langgraph-success") as manager:
        executor = ToolExecutor(manager)
        final_answer = adapter.run_task("Task prompt", executor)
        
        assert final_answer == "Final response from mock agent."
        
        # Verify tool calls history logged in executor
        assert len(executor.tool_calls) == 1
        assert executor.tool_calls[0].tool_name == "vigil_sandbox_exec"
        assert executor.tool_calls[0].exit_code == 0
        assert executor.tool_calls[0].stdout.strip() == "Mocked Output"


def test_langgraph_adapter_step_limit_error():
    # Define an infinite tool call loop
    tool_call = {
        "name": "vigil_sandbox_exec",
        "args": {"command": ["echo", "Looping"]},
        "id": "call_loop",
        "type": "tool_call"
    }
    
    # Keep returning tool calls to trigger infinite loops
    responses = [
        AIMessage(content="", tool_calls=[tool_call]),
        AIMessage(content="", tool_calls=[tool_call]),
        AIMessage(content="", tool_calls=[tool_call]),
        AIMessage(content="", tool_calls=[tool_call]),
        AIMessage(content="", tool_calls=[tool_call])
    ]
    
    mock_llm = MockChatModel(messages_to_return=responses)
    
    # Initialize adapter with very small step limit (max_steps = 2)
    adapter = LangGraphAgentAdapter(llm=mock_llm, max_steps=2)
    
    config = SandboxConfig()
    settings = get_settings()
    
    with Sandbox(config, settings.WORKSPACE_BASE_DIR, "test-langgraph-loop") as manager:
        executor = ToolExecutor(manager)
        
        with pytest.raises(AgentExecutionError) as exc_info:
            adapter.run_task("Task prompt", executor)
            
        assert "exceeded maximum step limit" in str(exc_info.value)
