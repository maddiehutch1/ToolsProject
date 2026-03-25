# Changelog

All product changes are documented here. Entries are ordered newest-first. Phase entries map to git commits; patch entries capture individual fixes and improvements made outside of a phase commit.

---

## [Patch] – 2026-03-25 · Markdown Rendering, Bubble Layout & Changelog
_No commit yet_

### Changed
- `frontend/index.html` – Added `marked.js` CDN script tag so the browser can parse markdown before rendering
- `frontend/app.js` – Added `renderMarkdown()` helper using `marked.parse()` with `breaks: true`
- `frontend/app.js` – `appendBubble()` now sets `innerHTML` via `renderMarkdown()` instead of `textContent`, so bold, bullets, headers, and code blocks display correctly
- `frontend/app.js` – Streaming token handler now accumulates raw markdown in a `rawText` variable and re-renders the full bubble on each token (prevents asterisks and hyphens from appearing as raw characters mid-stream)
- `frontend/style.css` – Added scoped `.bubble` markdown styles: `p`, `ul`, `ol`, `li`, `h1–h6`, `code`, and `pre` rules restore margins/padding stripped by the global reset, keeping all rendered content inside the bubble

### Added
- `ai/changelog.md` – This file; tracks all product changes going forward, sourced from git history for Phases 1–7

---

## [Phase 7] – 2026-03-25 · Chat Frontend
**Commit:** `eccc32b`

### Added
- `frontend/index.html` – Full chat UI shell with disclaimer banner, chat container, and input area
- `frontend/app.js` – SSE streaming client: token-by-token rendering, tool badge chips, crisis card, loading spinner, session UUID, Enter/Send handling
- `frontend/style.css` – Styling for disclaimer banner, chat bubbles (user/agent), tool badges, crisis card, spinner, and input bar

---

## [Phase 6] – 2026-03-25 · REST API & Session Memory
**Commit:** `75ffc7b`

### Added
- `backend/main.py` – `POST /chat` SSE endpoint with crisis gate, streaming agent response, and structured event types (`token`, `tool_use`, `crisis`, `error`, `done`)
- `backend/main.py` – In-memory session store for multi-turn conversation history
- `backend/main.py` – Static file mount to serve the frontend
- `backend/main.py` – `/health` endpoint update
- `backend/models.py` – `ChatRequest` model updated with `session_id` field
- `tests/test_api.py` – 8 integration tests covering tool_use, crisis, and error paths (all 47 tests green)

---

## [Phase 5] – 2026-03-25 · Crisis Detection Gate
**Commit:** `2b78f1b`

### Added
- `backend/crisis.py` – `detect_crisis()` with 8-keyword list (including "hurting myself" multi-word fix)
- `backend/crisis.py` – `CRISIS_RESPONSE` constant with 988 Suicide & Crisis Lifeline, Crisis Text Line (741741), NAMI, and SAMHSA links
- `backend/agent.py` – `SYSTEM_PROMPT` prepended to every agent run
- `backend/agent.py` – Crisis gate wired into `run_agent_stream` before LLM call
- `tests/test_crisis.py` – 16 unit tests covering keyword detection and non-crisis cases (all 33 tests passing)

---

## [Phase 4] – 2026-03-25 · LangGraph Agent
**Commit:** `75996b1`

### Added
- `backend/agent.py` – `StateGraph` with `ToolNode` routing across `rag_search`, `web_search`, and `calculator`
- `backend/agent.py` – `run_agent_stream` async generator for token-by-token streaming
- `tests/test_agent.py` – 6 integration tests covering all three tool routing paths

---

## [Phase 3] – 2026-03-25 · Web Search & Calculator Tools
**Commit:** `d904511`

### Added
- `backend/tools/web_search.py` – `web_search` LangChain tool wrapping TavilySearch
- `backend/tools/calculator.py` – `calculator` LangChain tool using `simpleeval` (no code execution)
- `tests/test_web_search.py` – 4 unit tests with fully mocked Tavily API
- `tests/test_calculator.py` – 9 unit tests covering arithmetic, edge cases, and safe expression validation (17 total unit tests passing)

---

## [Phase 2] – 2026-03-24 · Knowledge Base & RAG Tool
**Commits:** `47d28f1`, `12d379a`

### Added
- `knowledge_base/cbt_techniques.md` – CBT reference document
- `knowledge_base/dbt_skills.md` – DBT skills reference document
- `knowledge_base/crisis_resources.md` – Crisis resources reference document
- `knowledge_base/grounding_techniques.md` – Grounding techniques reference document
- `knowledge_base/mindfulness_exercises.md` – Mindfulness exercises reference document
- `knowledge_base/sleep_hygiene.md` – Sleep hygiene reference document
- `backend/ingest.py` – FAISS ingest pipeline for chunking and embedding KB documents
- `backend/tools/rag_search.py` – `rag_search` LangChain `@tool` with source attribution
- `tests/test_rag_search.py` – 4 unit tests for RAG retrieval
- `tests/fixtures/faiss_index/` – Committed FAISS index (`index.faiss`, `index.pkl`) for deterministic integration tests

---

## [Phase 1] – 2026-03-24 · Project Scaffold
**Commit:** `0b96523`

### Added
- `backend/main.py` – FastAPI app skeleton with `/health` endpoint
- `backend/models.py` – `ChatRequest` Pydantic model
- `backend/__init__.py` – Package marker
- `requirements.txt` – Pinned dependencies (FastAPI, LangChain, LangGraph, FAISS, etc.)
- `pytest.ini` – Test configuration with `asyncio_mode = auto`
- `.env.example` – Template for `OPENAI_API_KEY` and `TAVILY_API_KEY`
- `.gitignore` – Ignores `.env`, `__pycache__`, FAISS indexes, and virtual environments
- `tests/conftest.py` – Shared pytest fixtures
- `tests/__init__.py` – Package marker
