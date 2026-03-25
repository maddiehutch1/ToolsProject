# 2026-03-19 Phase 6 Roadmap — FastAPI Streaming Endpoint
**Target:** Day 4  
**Status:** Complete

---

## Read First
- `aiDocs/context.md` — AI orientation and document map  
- `aiDocs/mvp.md` — canonical project structure and Definition of Done  
- `aiDocs/architecture.md §Request Lifecycle` — full request flow from POST to SSE  
- `aiDocs/prd.md §API Contracts` — SSE event schema and all response paths  
- `ai/guides/fastapi.md` — `StreamingResponse` + SSE patterns

---

## Goal
A working `POST /chat` SSE endpoint that streams the full agent event protocol, with session memory, verified by `TestClient` integration tests and `curl`.

---

## Checklist

**`POST /chat` Endpoint**
- [x] Accept `ChatRequest(message, session_id)`
- [x] Run `detect_crisis(body.message)` first — if true, stream crisis SSE and return immediately
- [x] Load/create `session_store[session_id]`; append `HumanMessage`
- [x] Wrap `run_agent_stream` in `StreamingResponse(media_type="text/event-stream")`
- [x] Format each event: `f"data: {json.dumps(event)}\n\n"`
- [x] On exception, stream `{"type": "error", "content": str(e)}`
- [x] After stream completes, append `AIMessage` to session history

**`GET /health` Update**
- [x] Add `"vector_store": "loaded" | "not_loaded"` to response

**Static File Mount**
- [x] `app.mount("/", StaticFiles(directory="frontend"), name="static")`

**Integration Tests — `tests/test_api.py`**
- [x] Mock `run_agent_stream` to yield a fixed event sequence — no real LLM or tool calls
- [x] `GET /health` → `{"status": "ok", "vector_store": "loaded"}` (2 tests: key present, correct values)
- [x] `POST /chat` normal message → stream contains `token` event and `done` event
- [x] `POST /chat` with tool response → stream contains `tool_use` and `tool_done` events
- [x] `POST /chat` crisis keyword → stream contains `crisis` event, no `token` events
- [x] `POST /chat` same `session_id` twice → session memory persisted (history length ≥ 2)
- [x] `POST /chat` agent raises exception → stream contains `error` event
- [x] `POST /chat` missing `message` field → HTTP 422
- [x] All marked `@pytest.mark.integration`

**Manual Smoke Test**
- [x] Verify all SSE event types appear in `curl` output (see Verify section in plan)

---

## Key Files Modified / Created
```
backend/main.py     (POST /chat, health update, static mount)
tests/test_api.py   (new)
```

---

## Phase Gate
```bash
pytest -m "unit or integration" -v
# Expected: all unit tests green + test_agent.py (6) + test_api.py (8) pass
# No API keys consumed — all external calls are mocked
```

---

## Previous Phase
[Phase 5 — Crisis Detection & System Prompt](./2026-03-19-phase-5-crisis-roadmap.md)

## Next Phase
[Phase 7 — Frontend](./2026-03-19-phase-7-frontend-roadmap.md)
