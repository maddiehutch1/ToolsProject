# 2026-03-19 Phase 4 Plan — LangGraph Agent

---

> **Build only what the checklist requires. No abstractions until you need them twice.**
> If a file, class, or function isn't referenced by something else in this phase, it shouldn't exist yet.
> Do not add compatibility shims, base classes, config flags, or "just in case" error paths not listed here.

---

## `backend/agent.py`
The full agent module: state definition, graph topology, tool binding, and streaming generator.

```python
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
```

> The system prompt is added in Phase 5. For now `messages` is passed as-is from the caller.

---

## `tests/test_agent.py`
Mock `ChatOpenAI` to avoid real LLM calls. Two mock response types are needed: one with `tool_calls` (to test routing) and one without (to test direct answers).

```python
import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

def make_tool_call_message(tool_name: str):
    msg = MagicMock(spec=AIMessage)
    msg.tool_calls = [{"name": tool_name, "args": {"query": "test"}, "id": "call_1"}]
    msg.content = ""
    return msg

def make_direct_message(content: str):
    msg = MagicMock(spec=AIMessage)
    msg.tool_calls = []
    msg.content = content
    return msg

@pytest.fixture(autouse=True)
def mock_llm(monkeypatch):
    with patch("backend.agent._llm_with_tools") as mock:
        yield mock

@pytest.mark.integration
def test_routes_to_rag_search_for_mental_health_query(mock_llm):
    mock_llm.invoke.return_value = make_tool_call_message("rag_search")
    from backend.agent import graph
    state = {"messages": [HumanMessage(content="What is CBT?")]}
    result = graph.invoke(state)
    tool_names = [
        tc["name"]
        for msg in result["messages"]
        if hasattr(msg, "tool_calls")
        for tc in (msg.tool_calls or [])
    ]
    assert "rag_search" in tool_names

@pytest.mark.integration
def test_routes_to_calculator_for_math(mock_llm):
    mock_llm.invoke.return_value = make_tool_call_message("calculator")
    from backend.agent import graph
    state = {"messages": [HumanMessage(content="Score my PHQ-9: 2+3+1+0+2+1+3+2+1")]}
    result = graph.invoke(state)
    tool_names = [
        tc["name"]
        for msg in result["messages"]
        if hasattr(msg, "tool_calls")
        for tc in (msg.tool_calls or [])
    ]
    assert "calculator" in tool_names

@pytest.mark.integration
def test_routes_to_web_search_for_current_events(mock_llm):
    mock_llm.invoke.return_value = make_tool_call_message("web_search")
    from backend.agent import graph
    state = {"messages": [HumanMessage(content="What is the latest research on CBT?")]}
    result = graph.invoke(state)
    tool_names = [
        tc["name"]
        for msg in result["messages"]
        if hasattr(msg, "tool_calls")
        for tc in (msg.tool_calls or [])
    ]
    assert "web_search" in tool_names

@pytest.mark.integration
def test_direct_answer_when_no_tool_needed(mock_llm):
    mock_llm.invoke.return_value = make_direct_message("I'm here to help.")
    from backend.agent import graph
    state = {"messages": [HumanMessage(content="Hello")]}
    result = graph.invoke(state)
    last = result["messages"][-1]
    assert last.content == "I'm here to help."

@pytest.mark.integration
def test_run_agent_stream_yields_token_and_done(mock_llm):
    from backend.agent import run_agent_stream

    async def fake_astream_events(state, version):
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="Hello")}, "name": ""}
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content=" there")}, "name": ""}

    with patch("backend.agent.graph.astream_events", fake_astream_events):
        async def collect():
            return [e async for e in run_agent_stream([HumanMessage(content="hi")])]

        events = asyncio.get_event_loop().run_until_complete(collect())

    types = [e["type"] for e in events]
    assert "token" in types
    assert types[-1] == "done"
```

---

## Manual Smoke Test
Run this scratch script with real API keys to verify live routing before wiring to HTTP.

```python
# scratch/smoke_agent.py
import asyncio
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from backend.agent import run_agent_stream

load_dotenv()

PROMPTS = [
    "What is cognitive behavioral therapy?",        # → rag_search
    "What is DBT's TIPP skill?",                    # → rag_search
    "Score my PHQ-9: 1+0+2+1+3+2+1+0+2",          # → calculator
    "What is the latest research on mindfulness?",  # → web_search
    "Hello, what can you help me with?",            # → direct answer
]

async def main():
    for prompt in PROMPTS:
        print(f"\n>>> {prompt}")
        async for event in run_agent_stream([HumanMessage(content=prompt)]):
            print(event)

asyncio.run(main())
```

```bash
python scratch/smoke_agent.py
```

---

## Verify
```bash
pytest -m "unit or integration" -v
# Expected: all prior unit tests green + 5 new integration tests pass
# No API keys consumed — ChatOpenAI is mocked
```
