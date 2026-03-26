import logging
import operator
from typing import Annotated
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

from backend.tools.rag_search import rag_search
from backend.tools.web_search import web_search
from backend.tools.calculator import calculator

load_dotenv()

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a psychoeducational mental health companion. "
    "You are NOT a therapist and do not provide diagnosis or treatment.\n\n"
    "Guidelines:\n"
    "- For questions about mental health techniques (CBT, DBT, mindfulness, grounding, sleep), "
    "always use the rag_search tool and cite the source document by name.\n"
    "- For current research or information not in the knowledge base, use web_search.\n"
    "- For PHQ-9, GAD-7, or any arithmetic, use the calculator tool.\n"
    "- Always state which tool you used and cite your source.\n"
    "- Maintain a warm, non-judgmental, evidence-based tone at all times."
)


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
    state = {"messages": [SystemMessage(content=SYSTEM_PROMPT)] + messages}
    async for event in graph.astream_events(state, version="v2"):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"].content
            if chunk:
                yield {"type": "token", "content": chunk}
        elif kind == "on_tool_start":
            tool_name = event["name"]
            tool_input = event["data"].get("input", {})
            logger.info("TOOL_CALL tool=%s args=%s", tool_name, tool_input)
            yield {"type": "tool_use", "tool": tool_name}
        elif kind == "on_tool_end":
            tool_name = event["name"]
            tool_output = event["data"].get("output", "")
            preview = str(tool_output)[:200]
            logger.info("TOOL_RESULT tool=%s result_preview=%s", tool_name, preview)
            yield {"type": "tool_done", "tool": tool_name}
    yield {"type": "done"}
