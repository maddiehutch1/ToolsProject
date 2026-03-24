# 2026-03-19 Phase 4 Roadmap — LangGraph Agent
**Target:** Day 3  
**Status:** Not started

---

## Read First
- `aiDocs/context.md` — AI orientation and document map  
- `aiDocs/mvp.md` — canonical project structure and Definition of Done  
- `ai/guides/langgraph.md` — `StateGraph` patterns and `astream_events` usage

---

## Goal
A compiled LangGraph `StateGraph` that routes across all three tools and streams events through an async generator. No HTTP layer yet — that comes in Phase 6.

---

## Checklist

**Agent Graph**
- [ ] Implement `backend/agent.py`:
  - `AgentState` TypedDict: `{ "messages": Annotated[list[BaseMessage], operator.add] }`
  - `call_model` node: `llm_with_tools.invoke(state["messages"])`
  - `tools` node: `ToolNode([rag_search, web_search, calculator])`
  - Conditional edge `should_continue`: returns `"tools"` if `last.tool_calls` else `END`
  - `llm_with_tools = ChatOpenAI(model="gpt-4o-mini", streaming=True).bind_tools([...])`
  - Compile: `graph = builder.compile()`

**Streaming Generator**
- [ ] Implement `run_agent_stream(messages)` async generator in `backend/agent.py`:
  - `async for event in graph.astream_events(state, version="v2")`
  - `on_chat_model_stream` → yield `{"type": "token", "content": chunk}`
  - `on_tool_start` → yield `{"type": "tool_use", "tool": name}`
  - `on_tool_end` → yield `{"type": "tool_done", "tool": name}`
  - After loop → yield `{"type": "done"}`

**Integration Tests**
- [ ] Write `tests/test_agent.py` — mock `ChatOpenAI`, 6 tests: routes to `rag_search` for mental-health queries, routes to `calculator` for math, routes to `web_search` for current-events, returns direct answer when no tool needed, `run_agent_stream` yields `token` + `done` events, `run_agent_stream` yields `tool_use` + `tool_done` events when tool fires
- [ ] All tests marked `@pytest.mark.integration`

**Manual Smoke Test**
- [ ] Run 5+ live prompts covering all three tool paths in a scratch script before wiring to HTTP

---

## Key Files Created
```
backend/agent.py
tests/test_agent.py
```

---

## Phase Gate
```bash
pytest -m "unit or integration" -v
# Expected: all prior unit tests still green + 6 agent integration tests pass
# No API keys consumed if mocking is correct
```

---

## Previous Phase
[Phase 3 — Web Search & Calculator Tools](./2026-03-19-phase-3-tools-roadmap.md)

## Next Phase
[Phase 5 — Crisis Detection & System Prompt](./2026-03-19-phase-5-crisis-roadmap.md)
