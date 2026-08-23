from typing import TypedDict, Annotated, Sequence, Any
import logging
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphRecursionError

from vigil.agents.base_adapter import BaseAgentAdapter
from vigil.agents.tools import VigilSandboxTool
from vigil.core.tool_executor import ToolExecutor
from vigil.core.exceptions import AgentExecutionError

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]

class LangGraphAgentAdapter(BaseAgentAdapter):
    """
    Concrete adapter for LangGraph ReAct agent loop.
    Enforces maximum execution steps and routes tools into the sandbox.
    """
    def __init__(self, model_provider: str = "openai", model_name: str = "gpt-4o-mini", **kwargs: Any):
        self.model_provider = model_provider
        self.model_name = model_name
        self.config = kwargs.copy()
        # Extract llm if passed directly (for testing with mock LLM)
        self._llm = self.config.pop("llm", None)
        # Default maximum allowed reasoning loops
        self.max_steps = self.config.pop("max_steps", 10)

    def _get_llm(self, tools: list):
        if self._llm:
            if hasattr(self._llm, "bind_tools"):
                return self._llm.bind_tools(tools)
            return self._llm
            
        if self.model_provider == "openai":
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                raise AgentExecutionError("langchain-openai package is not installed.")
            llm = ChatOpenAI(model=self.model_name, **self.config)
            return llm.bind_tools(tools)
        else:
            raise AgentExecutionError(f"Unsupported model provider: {self.model_provider}")

    def run_task(self, prompt: str, tool_executor: ToolExecutor) -> str:
        # 1. Instantiate the sandbox tool
        sandbox_tool = VigilSandboxTool(executor=tool_executor)
        tools = [sandbox_tool]
        tools_map = {t.name: t for t in tools}
        
        # 2. Initialize LLM
        try:
            llm_with_tools = self._get_llm(tools)
        except Exception as e:
            raise AgentExecutionError(f"Failed to initialize LLM: {e}")

        # 3. Define ReAct nodes
        def agent_node(state: AgentState):
            try:
                response = llm_with_tools.invoke(state["messages"])
                return {"messages": [response]}
            except Exception as e:
                raise AgentExecutionError(f"LLM invocation failed: {e}")

        def call_tool_node(state: AgentState):
            last_message = state["messages"][-1]
            tool_outputs = []
            for tool_call in last_message.tool_calls:
                tool = tools_map.get(tool_call["name"])
                if not tool:
                    tool_message = ToolMessage(
                        content=f"Error: Tool {tool_call['name']} not found.",
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"]
                    )
                else:
                    output = tool.invoke(tool_call)
                    tool_message = ToolMessage(
                        content=str(output),
                        name=tool_call["name"],
                        tool_call_id=tool_call["id"]
                    )
                tool_outputs.append(tool_message)
            return {"messages": tool_outputs}

        def should_continue(state: AgentState):
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return END

        # 4. Construct StateGraph
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", call_tool_node)
        
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
        workflow.add_edge("tools", "agent")
        
        graph = workflow.compile()
        
        # 5. Execute Graph with recursion limit
        initial_state = {"messages": [HumanMessage(content=prompt)]}
        # In LangGraph, each transition (node run) counts as a step.
        # We multiply max_steps * 2 to account for (agent -> tools) transitions.
        recursion_limit = self.max_steps * 2 + 2
        
        try:
            result = graph.invoke(initial_state, config={"recursion_limit": recursion_limit})
            final_message = result["messages"][-1]
            return final_message.content
        except GraphRecursionError:
            raise AgentExecutionError(f"Agent exceeded maximum step limit of {self.max_steps}.")
        except Exception as e:
            if isinstance(e, AgentExecutionError):
                raise e
            raise AgentExecutionError(f"LangGraph execution crashed: {e}")
