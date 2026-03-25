import operator
from typing import Annotated
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from backend.tools.rag_search import rag_search
from backend.tools.web_search import web_search
from backend.tools.calculator import calculator

load_dotenv()


# --- State ---

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]


# --- LLM + tools ---

_tools = [rag_search, web_search, calculator]
_llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
_llm_with_tools = _llm.bind_tools(_tools)


# --- Nodes ---

def call_model(state: AgentState) -> AgentState:
    response = _llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# --- Graph ---

def should_continue(state: AgentState):
    last = state["messages"][-1]
    return "tools" if last.tool_calls else END


builder = StateGraph(AgentState)
builder.add_node("call_model", call_model)
builder.add_node("tools", ToolNode(_tools))
builder.set_entry_point("call_model")
builder.add_conditional_edges("call_model", should_continue)
builder.add_edge("tools", "call_model")

graph = builder.compile()


# --- Streaming generator ---

async def run_agent_stream(messages: list[BaseMessage]):
    state = {"messages": messages}
    async for event in graph.astream_events(state, version="v2"):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"].content
            if chunk:
                yield {"type": "token", "content": chunk}
        elif kind == "on_tool_start":
            yield {"type": "tool_use", "tool": event["name"]}
        elif kind == "on_tool_end":
            yield {"type": "tool_done", "tool": event["name"]}
    yield {"type": "done"}
