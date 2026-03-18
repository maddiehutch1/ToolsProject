# LangGraph Guide
## Usage in This Project

**Source:** [LangGraph Docs](https://langchain-ai.github.io/langgraph/) — verified March 2026  
**Package:** `langgraph>=0.2.0`  
**Used in:** `backend/agent.py`

---

## Why LangGraph

LangGraph is chosen because:
- Explicit, inspectable graph topology — nodes and edges are declared, not hidden in a chain
- Native async streaming via `.astream_events()` — required for token-by-token SSE output
- `ToolNode` handles tool dispatch automatically — no manual routing logic
- Conditional edges model the "call model → maybe call tool → call model again" loop cleanly
- State is typed (`TypedDict`) — predictable and debuggable

---

## Installation

```bash
pip install langgraph langchain-core
```

---

## Core Concepts for This Project

### AgentState

The graph's state is a typed dict that accumulates messages across the loop:

```python
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
```

`Annotated[list[BaseMessage], operator.add]` tells LangGraph to **append** new messages to the list rather than overwriting it. This is what gives the agent multi-turn memory within a single invocation.

---

## Full Agent Implementation

```python
# backend/agent.py
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
from typing import TypedDict, Annotated
import operator
import json

from backend.tools.rag_search import rag_search
from backend.tools.web_search import web_search
from backend.tools.calculator import calculator

SYSTEM_PROMPT = SystemMessage(content="""You are a psychoeducational mental health companion. \
You are NOT a therapist and cannot diagnose or treat conditions. \
For questions about mental health techniques, ALWAYS use the rag_search tool first. \
For current or factual information not in the knowledge base, use web_search. \
For arithmetic or assessment scoring (PHQ-9, GAD-7), use the calculator tool. \
Always cite which tool you used and include the source document name in your response. \
Use a warm, non-judgmental, evidence-based tone.""")

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]

tools = [rag_search, web_search, calculator]
llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
llm_with_tools = llm.bind_tools(tools)

def call_model(state: AgentState) -> dict:
    messages = [SYSTEM_PROMPT] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

tool_node = ToolNode(tools)

graph = StateGraph(AgentState)
graph.add_node("call_model", call_model)
graph.add_node("tools", tool_node)
graph.set_entry_point("call_model")
graph.add_conditional_edges("call_model", should_continue)
graph.add_edge("tools", "call_model")

agent = graph.compile()
```

### Graph Topology

```
START
  │
  ▼
call_model  ──(has tool_calls)──►  tools
  ▲                                  │
  └──────────────────────────────────┘
  │
  ▼ (no tool_calls)
 END
```

---

## Streaming with `.astream_events()`

`.astream_events(version="v2")` is the correct streaming method. It yields a stream of typed event dicts from every node and LLM call inside the graph.

```python
# backend/agent.py
async def run_agent_stream(messages: list[BaseMessage], session_id: str):
    """Async generator that yields SSE-ready JSON strings."""
    state = {"messages": messages}

    async for event in agent.astream_events(state, version="v2"):
        kind = event["event"]

        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"].content
            if chunk:
                yield json.dumps({"type": "token", "content": chunk})

        elif kind == "on_tool_start":
            yield json.dumps({"type": "tool_use", "tool": event["name"]})

        elif kind == "on_tool_end":
            yield json.dumps({"type": "tool_done", "tool": event["name"]})

    yield json.dumps({"type": "done"})
```

### Event Types Reference (`version="v2"`)

| Event name | When it fires | Useful fields |
|------------|--------------|---------------|
| `on_chat_model_start` | LLM call begins | `event["data"]["input"]` |
| `on_chat_model_stream` | LLM produces a token | `event["data"]["chunk"].content` |
| `on_chat_model_end` | LLM call finishes | `event["data"]["output"]` |
| `on_tool_start` | Tool call begins | `event["name"]`, `event["data"]["input"]` |
| `on_tool_end` | Tool returns | `event["name"]`, `event["data"]["output"]` |
| `on_chain_start` | A graph node begins | `event["name"]` (node name) |
| `on_chain_end` | A graph node finishes | `event["name"]` |

### Filtering Events

If you only want events from specific nodes or tools, use the filtering params:

```python
async for event in agent.astream_events(
    state,
    version="v2",
    include_names=["call_model", "rag_search", "web_search", "calculator"],
):
    ...
```

---

## ToolNode

`ToolNode` is a prebuilt LangGraph node that automatically dispatches `AIMessage.tool_calls` to the correct `@tool` function and returns the results as `ToolMessage` objects.

```python
from langgraph.prebuilt import ToolNode

tool_node = ToolNode([rag_search, web_search, calculator])
```

Requirements:
- Each tool must be a LangChain `@tool` decorated function (see `langchain_core.tools.tool`)
- The tool name in the `@tool` decorator must match what the LLM sees — keep names short and descriptive

---

## Defining LangChain Tools for LangGraph

Each tool used in this project is a `@tool`-decorated function. LangGraph's `ToolNode` reads the function's name and docstring to build the tool schema sent to the LLM.

```python
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """Evaluates a mathematical expression. Use for PHQ-9, GAD-7, or any arithmetic."""
    # ... implementation
```

The docstring becomes the tool description — write it clearly, as the LLM uses it to decide when to call the tool.

---

## Multi-Turn Memory

To give the agent conversation history, pass the accumulated message list as the initial state:

```python
# In main.py / chat endpoint
history = session_store.get(session_id, [])
history.append(HumanMessage(content=user_message))

async for chunk in run_agent_stream(history, session_id):
    yield f"data: {chunk}\n\n"

# After streaming completes, save the full updated history
# (requires capturing the final AIMessage separately)
```

Because `AgentState.messages` uses `operator.add`, the graph will append to whatever you pass in. The session store accumulates the full dialogue.

---

## Compiling and Inspecting the Graph

```python
agent = graph.compile()

# View the graph as ASCII art (useful for debugging)
print(agent.get_graph().draw_ascii())

# Or generate a Mermaid diagram
print(agent.get_graph().draw_mermaid())
```

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| `astream_events` yields nothing | Confirm you're passing `version="v2"` — v1 has a different schema |
| Tool not called despite correct prompt | Check the `@tool` docstring — the LLM uses it to decide when to invoke |
| `operator.add` not applied | Verify the `Annotated` syntax exactly — missing it causes state to be overwritten |
| Infinite tool loop | Add a max_iterations check or use `recursion_limit` in `graph.compile()` |
| System prompt not included | The `AgentState` only stores messages; prepend `SystemMessage` manually in `call_model` |
| `ToolNode` key error | Tool names in `bind_tools` must exactly match the `@tool`-decorated function names |

---

## Key References

- [LangGraph Concepts — Streaming](https://langchain-ai.github.io/langgraph/concepts/streaming/)
- [LangGraph How-To — astream_events](https://langchain-ai.github.io/langgraph/how-tos/streaming-events-from-within-tools/)
- [LangGraph Reference — StateGraph](https://langchain-ai.github.io/langgraph/reference/graphs/)
- [LangGraph Prebuilt — ToolNode](https://langchain-ai.github.io/langgraph/reference/prebuilt/#langgraph.prebuilt.tool_node.ToolNode)
