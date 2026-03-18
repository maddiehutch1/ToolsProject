# MVP Roadmap
## Mental Health Companion — Agentic Chat Application

**Version:** 1.1  
**Date:** March 16, 2026  
**Status:** Active

---

## Overview

This roadmap covers the complete build of the Mental Health Companion MVP: a streaming agentic chat app where a LangGraph-orchestrated LLM autonomously chooses between three tools (RAG knowledge base, live web search, safe math evaluator) to deliver grounded, evidence-based mental health guidance through a browser UI.

**Definition of done:** All 8 phases checked off, 17-item Definition of Done in `aiDocs/mvp.md` satisfied, full test suite green, linter clean.

---

## Architecture at a Glance

```
Browser (Vanilla JS)
  └── POST /chat → FastAPI (Python)
        ├── Crisis check (pre-LLM keyword gate)
        └── LangGraph StateGraph
              ├── call_model node  (ChatOpenAI gpt-4o-mini)
              ├── tools node       (ToolNode dispatcher)
              │     ├── rag_search    → FAISS vector store
              │     ├── web_search    → Tavily API
              │     └── calculator    → simpleeval
              └── SSE stream → browser
```

Full technical detail: [`aiDocs/architecture.md`](../../aiDocs/architecture.md)

---

## Testing Strategy

Tests are written **in the same phase as the code they cover** and run as a gate before the next phase begins. Catching breakage early is cheaper than untangling it later.

### Three Tiers

| Tier | What it tests | External deps | When to run |
|------|--------------|---------------|-------------|
| **Unit** | Single function in complete isolation — all I/O mocked | None (no API keys) | Every phase gate |
| **Integration** | A component wired to its real local deps, external APIs mocked | FAISS index on disk | Phases 4, 6, 8 gates |
| **E2E** | Full stack — real LLM, real APIs, real browser | OpenAI + Tavily keys | Phase 8 gate only |

### pytest Markers

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
markers =
    unit: isolated, no I/O, always mocked
    integration: real local deps, external APIs mocked
    e2e: full stack, real API keys required
```

Run commands:
```bash
pytest -m unit -v               # fast — no keys needed, run constantly
pytest -m "unit or integration" -v   # needs FAISS index on disk
pytest -v                       # everything (needs all API keys)
```

### Test File Map

| Test file | Tier | Phase written | What it covers |
|-----------|------|---------------|----------------|
| `tests/test_calculator.py` | unit | 3 | `simple_eval` wrapper, PHQ-9, error handling |
| `tests/test_crisis.py` | unit | 5 | `detect_crisis` — keyword hits and misses |
| `tests/test_rag_search.py` | unit | 2 | `rag_search` with mocked retriever; integration with real FAISS |
| `tests/test_web_search.py` | unit | 3 | `web_search` with mocked Tavily client |
| `tests/test_agent.py` | integration | 4 | Agent graph with mocked LLM — correct tool routing |
| `tests/test_api.py` | integration | 6 | FastAPI `TestClient` — all SSE event types, crisis gate, session memory |

---

## Phase Map

| Phase | Name | Day | Deliverable | Phase Gate |
|-------|------|-----|-------------|-----------|
| 1 | Project Scaffolding | 1 | Repo structure, deps, bare FastAPI `/health` | `pytest --co` (collect only — zero failures) |
| 2 | Knowledge Base & RAG Tool | 1–2 | 6 KB docs, ingest script, `rag_search` tool | `pytest -m unit -v` |
| 3 | Web Search & Calculator Tools | 2 | `web_search` + `calculator` tools | `pytest -m unit -v` |
| 4 | LangGraph Agent | 3 | `StateGraph` compiled, streaming generator working | `pytest -m "unit or integration" -v` |
| 5 | Crisis Detection & System Prompt | 3 | `crisis.py`, keyword gate, agent system prompt | `pytest -m unit -v` |
| 6 | FastAPI Streaming Endpoint | 4 | `POST /chat` SSE, session memory, `TestClient` verified | `pytest -m "unit or integration" -v` |
| 7 | Frontend | 4–5 | Single-page chat UI with streaming, tool badges, crisis card | Manual browser check (no automated tests) |
| 8 | Integration & Polish | 5 | All tiers green, `README.md`, linter clean | `pytest -v` (full suite) |

---

## Phase 1 — Project Scaffolding
**Target:** Day 1  
**Goal:** A clean repo skeleton that runs with no errors — including a working test harness — before any business logic is written.

### Checklist

**Repo & Config**
- [ ] Initialize folder structure per `aiDocs/mvp.md §4`
- [ ] Create `requirements.txt` with all pinned dependencies (see §Dependency Reference below)
- [ ] Create `.env.example` with `OPENAI_API_KEY` and `TAVILY_API_KEY` placeholders
- [ ] Create `.gitignore` — exclude `.env`, `faiss_index/`, `__pycache__/`, `*.pyc`

**FastAPI Skeleton**
- [ ] Scaffold `backend/main.py` — FastAPI app, `GET /health` returning `{"status": "ok"}`
- [ ] Scaffold `backend/models.py` — `ChatRequest` (message, session_id) Pydantic model
- [ ] Verify server starts: `uvicorn backend.main:app --reload --port 8000`

**Test Infrastructure (set up before any feature code)**
- [ ] Create `pytest.ini` — set `asyncio_mode = auto`, declare `unit`, `integration`, `e2e` markers
- [ ] Create `tests/conftest.py` — `monkeypatch` fixtures for `OPENAI_API_KEY`, `TAVILY_API_KEY`, `FAISS_INDEX_PATH`; shared `TestClient` fixture
- [ ] Verify `pytest --collect-only` exits 0 (no tests yet, but harness is healthy)

### Key Files Created
```
backend/main.py
backend/models.py
requirements.txt
.env.example
.gitignore
pytest.ini
tests/conftest.py
```

### `pytest.ini`
```ini
[pytest]
asyncio_mode = auto
markers =
    unit: isolated, no I/O, all external calls mocked
    integration: real local deps (FAISS), external APIs mocked
    e2e: full stack, real API keys required
```

### `tests/conftest.py` (starter)
```python
import pytest
from fastapi.testclient import TestClient

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    monkeypatch.setenv("FAISS_INDEX_PATH", "tests/fixtures/faiss_index")

@pytest.fixture
def client():
    from backend.main import app
    return TestClient(app)
```

### Phase Gate
```bash
pytest --collect-only   # must exit 0; no test failures
```

### Guide
See [`../guides/fastapi.md`](../guides/fastapi.md) for FastAPI setup patterns used in this project.

---

## Phase 2 — Knowledge Base & RAG Tool
**Target:** Day 1–2  
**Goal:** A working FAISS vector index built from real knowledge base documents, queryable via a LangChain `@tool`.

### Checklist

**Knowledge Base Documents**
- [ ] Author all 6 knowledge base markdown documents in `knowledge_base/` (substantive, not stubs):
  - `cbt_techniques.md` — Beck Institute CBT core techniques
  - `dbt_skills.md` — TIPP, DEAR MAN, PLEASE skills
  - `mindfulness_exercises.md` — MBSR body scan, breath awareness
  - `grounding_techniques.md` — 5-4-3-2-1, box breathing, cold water
  - `sleep_hygiene.md` — CBT-I guidelines, sleep restriction basics
  - `crisis_resources.md` — 988 Suicide & Crisis Lifeline, Crisis Text Line, NAMI, SAMHSA

**Ingest Script**
- [ ] Implement `backend/ingest.py`:
  - `TextLoader` per file → `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)`
  - `OpenAIEmbeddings(model="text-embedding-3-small")`
  - `FAISS.from_documents(docs, embeddings).save_local("faiss_index")`
- [ ] Run `python backend/ingest.py`; confirm `faiss_index/index.faiss` and `faiss_index/index.pkl` exist

**RAG Tool**
- [ ] Implement `backend/tools/rag_search.py`:
  - Load FAISS with `FAISS.load_local(..., allow_dangerous_deserialization=True)`
  - `retriever = vectorstore.as_retriever(search_kwargs={"k": 4})`
  - `@tool` decorated `rag_search(query: str) -> str` — returns top-4 chunks each prefixed `[source_filename]`

**Unit Tests**
- [ ] Write `tests/test_rag_search.py`:
  - Mock the `retriever` — do not hit FAISS or OpenAI in unit tests
  - 3+ tests: returns formatted `[source]\ncontent` strings, handles empty results, source attribution present
  - Mark all with `@pytest.mark.unit`
- [ ] *(Optional integration tests)* Add `@pytest.mark.integration` tests that load the real FAISS index and assert known source docs are returned for known queries

### Key Files Created
```
knowledge_base/*.md      (6 files)
backend/ingest.py
backend/tools/__init__.py
backend/tools/rag_search.py
tests/test_rag_search.py
faiss_index/             (generated, not in git)
```

### Phase Gate
```bash
pytest -m unit -v
# Expected: test_rag_search.py tests pass
# All prior tests still green (no regressions)
```

### Guides
- [`../guides/langchain-openai.md`](../guides/langchain-openai.md) — `OpenAIEmbeddings` setup
- [`../guides/faiss.md`](../guides/faiss.md) — FAISS ingest and load patterns

---

## Phase 3 — Web Search & Calculator Tools
**Target:** Day 2  
**Goal:** Two more working `@tool` functions with full unit test coverage before they are wired into the agent.

### Checklist

**Web Search Tool**
- [ ] Implement `backend/tools/web_search.py`:
  - `langchain-tavily` `TavilySearch` tool, `max_results=5`
  - Wrap in `@tool` decorated `web_search(query: str) -> str`
  - Format output: title, URL, snippet per result
  - Handle `Exception` → return descriptive error string
- [ ] Write `tests/test_web_search.py`:
  - Mock `TavilySearch.invoke` — never call the real API in unit tests
  - 3+ tests: formatted output contains title and URL, handles empty results, API error returns graceful string
  - Mark all with `@pytest.mark.unit`

**Calculator Tool**
- [ ] Implement `backend/tools/calculator.py`:
  - `simpleeval.simple_eval` with whitelisted functions: `sqrt`, `abs`, `round`, `pow`, `floor`, `ceil`
  - `@tool` decorated `calculator(expression: str) -> str`
  - Return numeric result as string, or descriptive error on invalid input
- [ ] Write `tests/test_calculator.py`:
  - 7+ tests: basic ops, PHQ-9 sum (`2+3+1+0+2+1+3+2+1` → `"15"`), GAD-7 sum, `sqrt(144)`, `ZeroDivisionError`, invalid syntax, `import os` attempt
  - Mark all with `@pytest.mark.unit`
  - No mocking required — `simpleeval` has no external dependencies

### Key Files Created
```
backend/tools/web_search.py
backend/tools/calculator.py
tests/test_web_search.py
tests/test_calculator.py
```

### Phase Gate
```bash
pytest -m unit -v
# Expected: all unit tests across phases 1–3 pass
# test_calculator.py: 7+ pass
# test_web_search.py: 3+ pass
# test_rag_search.py: 3+ pass (no regressions)
```

### Guides
- [`../guides/tavily.md`](../guides/tavily.md) — `langchain-tavily` `TavilySearch` integration
- [`../guides/simpleeval.md`](../guides/simpleeval.md) — safe expression evaluation

---

## Phase 4 — LangGraph Agent
**Target:** Day 3  
**Goal:** A compiled LangGraph `StateGraph` that routes across all three tools and streams events.

### Checklist

**Agent Implementation**
- [ ] Implement `backend/agent.py`:
  - `AgentState` TypedDict: `{ "messages": Annotated[list[BaseMessage], operator.add] }`
  - `call_model` node: `llm_with_tools.invoke(state["messages"])`
  - `tools` node: `ToolNode([rag_search, web_search, calculator])`
  - Conditional edge `should_continue`: returns `"tools"` if `last.tool_calls` else `END`
  - `graph.set_entry_point("call_model")` → compile with `graph.compile()`
- [ ] Implement `run_agent_stream(messages, session_id)` async generator:
  - `async for event in agent.astream_events(state, version="v2")`
  - Yield JSON strings for `on_chat_model_stream` → `token`, `on_tool_start` → `tool_use`, `on_tool_end` → `tool_done`
  - Yield final `{"type": "done"}` after loop

**Integration Tests**
- [ ] Write `tests/test_agent.py`:
  - Mock `ChatOpenAI` responses — return a fake `AIMessage` with `tool_calls` for tool-routing tests, and a plain `AIMessage` for direct-answer tests
  - 4+ tests: routes to `rag_search` for mental-health queries, routes to `calculator` for math expressions, routes to `web_search` for current-events queries, returns direct answer when no tool needed
  - Test that `run_agent_stream` yields at least one `token` event and a final `done` event
  - Mark all with `@pytest.mark.integration`
- [ ] Manually smoke-test in a scratch script with 5+ live prompts covering all three tool paths (confirms real LLM routing before wiring to HTTP)

### Key Files Created
```
backend/agent.py
tests/test_agent.py
```

### Phase Gate
```bash
pytest -m "unit or integration" -v
# Expected: all unit tests still green + new agent integration tests pass
# If mocking is correct, no API keys are consumed
```

### Guide
See [`../guides/langgraph.md`](../guides/langgraph.md) for `StateGraph` patterns and `astream_events` usage.

---

## Phase 5 — Crisis Detection & System Prompt
**Target:** Day 3  
**Goal:** A hard pre-LLM safety gate and a well-calibrated system prompt.

### Checklist

**Crisis Detection**
- [ ] Implement `backend/crisis.py`:
  - Keyword list: `["want to die", "end my life", "kill myself", "self-harm", "suicidal", "hurt myself", "don't want to be here"]`
  - `detect_crisis(message: str) -> bool` — case-insensitive substring match
  - `CRISIS_RESPONSE` string constant: 988 Suicide & Crisis Lifeline, Crisis Text Line (text HOME to 741741), NAMI Helpline, SAMHSA National Helpline

**System Prompt**
- [ ] Write the agent system prompt in `backend/agent.py`:
  - Role: psychoeducational companion, not a therapist
  - Prefer `rag_search` for questions about mental health techniques
  - Always cite which tool was used
  - Warm, non-judgmental, evidence-based tone

**Unit Tests**
- [ ] Write `tests/test_crisis.py`:
  - 6+ tests — `detect_crisis` returns `True` for each keyword variant (mixed case, mid-sentence, etc.)
  - 4+ tests — `detect_crisis` returns `False` for normal messages ("I'm feeling anxious", "help me sleep better", "what is CBT")
  - 1 test — `CRISIS_RESPONSE` string contains "988" and "741741"
  - Mark all with `@pytest.mark.unit`
  - No mocking needed — `crisis.py` is pure Python with zero external dependencies

### Key Files Created / Modified
```
backend/crisis.py
backend/agent.py  (system prompt added)
tests/test_crisis.py
```

### Phase Gate
```bash
pytest -m unit -v
# Expected: all prior unit tests still green + test_crisis.py passes
# crisis tests are the fastest in the suite — pure string matching, no I/O
```

---

## Phase 6 — FastAPI Streaming Endpoint
**Target:** Day 4  
**Goal:** A working `POST /chat` SSE endpoint that streams the full agent event protocol, verified with both `TestClient` integration tests and `curl`.

### Checklist

**Endpoint Implementation**
- [ ] Implement `POST /chat` in `backend/main.py`:
  - Accept `ChatRequest` (message, session_id)
  - Run `detect_crisis(body.message)` first; if true, stream hardcoded crisis SSE and return
  - Load/create `session_store[session_id]`; append `HumanMessage`
  - Wrap `run_agent_stream` in `StreamingResponse(..., media_type="text/event-stream")`
  - Format each event: `f"data: {json_str}\n\n"`
  - On error, stream `{"type": "error", "content": str(e)}`
  - After agent completes, append `AIMessage` to session history
- [ ] Update `GET /health` — add `"vector_store": "loaded" | "not_loaded"` field
- [ ] Mount static files: `app.mount("/", StaticFiles(directory="frontend"), name="static")`

**Integration Tests (FastAPI TestClient — the "widget test" layer)**  
These tests exercise a single HTTP route end-to-end without a browser or real external APIs. They are the closest equivalent to component/widget tests for this stack.

- [ ] Write `tests/test_api.py` using `fastapi.testclient.TestClient`:
  - Mock `run_agent_stream` to yield a fixed sequence of events — no real LLM or tool calls
  - `GET /health` → returns `{"status": "ok", "vector_store": "loaded"}` (2 tests: key present, correct values)
  - `POST /chat` normal message → SSE stream contains at least one `token` event and a `done` event
  - `POST /chat` crisis keyword → SSE stream contains a `crisis` event, no `token` events
  - `POST /chat` same `session_id` twice → second call's stream reflects prior conversation (session memory persisted)
  - `POST /chat` agent raises exception → stream contains an `error` event
  - `POST /chat` missing `message` field → returns HTTP 422
  - Mark all with `@pytest.mark.integration`

**Manual Smoke Test with curl**
- [ ] Verify all SSE event types appear in `curl` output:
  ```bash
  curl -N -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "What is CBT?", "session_id": "test-1"}'
  ```

### Key Files Modified / Created
```
backend/main.py
tests/test_api.py
```

### Phase Gate
```bash
pytest -m "unit or integration" -v
# Expected: all unit tests green + test_agent.py + test_api.py pass
# No API keys consumed — all external calls are mocked
```

### Guide
See [`../guides/fastapi.md`](../guides/fastapi.md) for `StreamingResponse` + SSE patterns.

---

## Phase 7 — Frontend
**Target:** Day 4–5  
**Goal:** A functional, calm single-page chat UI that consumes the SSE stream correctly.

> **Testing note:** The frontend is vanilla HTML/CSS/JS with no build system, so there is no automated test framework available at this tier. The phase gate for Phase 7 is a manual browser checklist — each user story verified in Chrome one-by-one before proceeding to Phase 8.

### Checklist

**HTML Structure**
- [ ] Build `frontend/index.html`:
  - Persistent banner: *"This tool is not a substitute for professional mental health care."*
  - Message list area, input field, Send button
  - Link `style.css` and `app.js`

**Styling**
- [ ] Style with `frontend/style.css`:
  - Soft, accessible color palette (blues/greens/greys)
  - Distinct user bubble (right-aligned) vs. agent bubble (left-aligned)
  - Tool badge chips (small pill labels per tool used)
  - Crisis card style (red/amber border, clear resource links)
  - Loading spinner animation

**JavaScript / SSE Client**
- [ ] Implement `frontend/app.js`:
  - Generate `session_id` (UUID) on page load
  - `sendMessage(text)` → `POST /chat` → `fetch` + `ReadableStream`
  - Append `token` chunks to current agent bubble in real time
  - Add tool badge on `tool_use` event
  - Render crisis card on `crisis` event (distinct styling + resource links)
  - Show spinner while waiting; auto-scroll to bottom; disable input during stream
  - Handle `error` event gracefully

### Key Files Created
```
frontend/index.html
frontend/style.css
frontend/app.js
```

### Phase Gate (Manual Browser Checklist)
Open `http://localhost:8000` in Chrome and verify each item:
- [ ] Disclaimer banner is visible and never disappears
- [ ] Typing a message and pressing Send appends user bubble immediately
- [ ] Agent response streams token-by-token (not a single delayed block)
- [ ] A RAG question shows a tool badge labeled `rag_search`
- [ ] A math question shows a tool badge labeled `calculator`
- [ ] A crisis keyword message shows the crisis card with red/amber styling and resource links
- [ ] A follow-up question correctly references the previous turn
- [ ] An `error` event displays a readable error message, not a crashed/blank UI

---

## Phase 8 — Integration & Polish
**Target:** Day 5  
**Goal:** All three test tiers green, the full system passes live E2E scenarios, linter clean, README complete.

> All prior phases should have caught unit and integration failures already. Phase 8 is for E2E validation with real API keys, final regression check, and documentation — not a first-time test run.

### Checklist

**Full Test Suite — Run First**
- [ ] Run `pytest -m "unit or integration" -v` — must be 100% green before touching anything else
- [ ] Fix any regressions before proceeding

**Live E2E Scenarios (real LLM + real APIs)**
- [ ] E2E: CBT question → `rag_search` tool fires → source document name cited in response
- [ ] E2E: Current-events question → `web_search` fires → URL cited in response
- [ ] E2E: PHQ-9 scoring question → `calculator` fires → numeric result + clinical interpretation
- [ ] E2E: Crisis keyword → hardcoded response card renders, no LLM invoked (verify via server logs)
- [ ] E2E: Conversational follow-up references the previous turn correctly (multi-turn memory)
- [ ] E2E: 10-query tool-routing test — at least 9/10 route to the correct tool

**Linter**
- [ ] Run `ruff check .` (or `flake8 .`); fix all errors

**Documentation**
- [ ] Write `README.md`:
  - Prerequisites (Python 3.11+, API keys)
  - Installation: `pip install -r requirements.txt`
  - Configuration: copy `.env.example` → `.env`, fill in keys
  - Ingest: `python backend/ingest.py`
  - Run: `uvicorn backend.main:app --reload --port 8000`
  - Test: `pytest -m unit -v` (unit only, no keys), `pytest -v` (full suite, keys required)
- [ ] Verify `.env` and `faiss_index/` are NOT tracked: `git status` shows them as untracked or ignored
- [ ] Final review against Definition of Done checklist in `aiDocs/mvp.md §8`

### Phase Gate (Final)
```bash
# Step 1: all automated tests
pytest -v
# Expected: every test across all tiers green

# Step 2: linter
ruff check .
# Expected: no errors
```

---

## Dependency Reference

```txt
# requirements.txt (target versions — verify latest at write time)

# Web framework
fastapi>=0.115.0
uvicorn[standard]>=0.30.0

# Config
python-dotenv>=1.0.0
pydantic>=2.0.0

# LangChain / LangGraph
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-community>=0.3.0
langchain-core>=0.3.0
langgraph>=0.2.0

# Vector store
faiss-cpu>=1.8.0

# Tools
langchain-tavily>=0.1.0
simpleeval>=1.0.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0        # required by FastAPI TestClient for async route testing
```

> **Note:** Always check PyPI for the latest stable version before pinning. Prefer exact pins (`==`) for reproducibility in a coursework submission.

---

## SSE Event Protocol

Every server-sent event from `POST /chat` follows this schema:

```
data: {"type": "<event_type>", ...fields}\n\n
```

| `type` | Trigger | Extra fields |
|--------|---------|-------------|
| `token` | LLM produces a text chunk | `"content": str` |
| `tool_use` | Agent calls a tool | `"tool": str` |
| `tool_done` | Tool returns a result | `"tool": str` |
| `crisis` | Crisis keyword detected | `"content": str` (full resource text) |
| `error` | Unhandled exception | `"content": str` |
| `done` | Stream complete | *(no extra fields)* |

---

## Risk Register (Summary)

| Risk | Mitigation |
|------|-----------|
| LangGraph streaming API changes | Pin version; test `.astream_events(version="v2")` in isolation first |
| RAG retrieval quality too low | Test retrieval early in Phase 2 before building the agent |
| Crisis false positives | Start with a minimal high-confidence keyword list |
| FAISS ingest failure | Run `ingest.py` early; verify files on disk before starting server |
| Tavily quota exceeded | Use mocked responses in tests; live key only for E2E |
| Scope creep | Strictly defer anything not in `aiDocs/mvp.md §2` |

---

## Related Documents

| Document | Purpose |
|----------|---------|
| [`aiDocs/prd.md`](../../aiDocs/prd.md) | Full product requirements — *what* and *why* |
| [`aiDocs/mvp.md`](../../aiDocs/mvp.md) | Detailed build plan, code sketches, Definition of Done |
| [`aiDocs/architecture.md`](../../aiDocs/architecture.md) | Component design, data flow, graph topology |
| [`ai/context.md`](../context.md) | AI assistant orientation document |
| [`ai/guides/`](../guides/) | Package-specific implementation guides |
