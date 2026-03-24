# 2026-03-19 Phase 6 Plan — FastAPI Streaming Endpoint

---

> **Build only what the checklist requires. No abstractions until you need them twice.**
> If a file, class, or function isn't referenced by something else in this phase, it shouldn't exist yet.
> Do not add compatibility shims, base classes, config flags, or "just in case" error paths not listed here.

---

## `backend/main.py`
Extends the Phase 1 skeleton with `POST /chat`, updated health check, and static file mount.

```python
import json
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, AIMessage

from backend.models import ChatRequest, HealthResponse
from backend.crisis import detect_crisis, CRISIS_RESPONSE
from backend.agent import run_agent_stream

load_dotenv()

app = FastAPI()

session_store: dict[str, list] = {}

def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"

@app.get("/health", response_model=HealthResponse)
def health():
    try:
        from backend.tools.rag_search import _vectorstore
        vector_status = "loaded" if _vectorstore else "not_loaded"
    except Exception:
        vector_status = "not_loaded"
    return {"status": "ok", "vector_store": vector_status}

@app.post("/chat")
async def chat(body: ChatRequest):
    if detect_crisis(body.message):
        async def crisis_stream():
            yield _sse({"type": "crisis", "content": CRISIS_RESPONSE})
            yield _sse({"type": "done"})
        return StreamingResponse(crisis_stream(), media_type="text/event-stream")

    history = session_store.setdefault(body.session_id, [])
    history.append(HumanMessage(content=body.message))

    async def event_stream():
        collected = []
        try:
            async for event in run_agent_stream(list(history)):
                collected.append(event)
                yield _sse(event)
        except Exception as e:
            yield _sse({"type": "error", "content": str(e)})
            yield _sse({"type": "done"})
            return

        full_text = "".join(
            e["content"] for e in collected if e.get("type") == "token"
        )
        history.append(AIMessage(content=full_text))

    return StreamingResponse(event_stream(), media_type="text/event-stream")

app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
```

> `HealthResponse` in `backend/models.py` needs a `vector_store: str` field added.

```python
class HealthResponse(BaseModel):
    status: str
    vector_store: str = "not_loaded"
```

---

## `tests/test_api.py`

```python
import json
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

async def mock_agent_stream_normal(messages):
    yield {"type": "token", "content": "Here is some help."}
    yield {"type": "done"}

async def mock_agent_stream_with_tool(messages):
    yield {"type": "tool_use", "tool": "rag_search"}
    yield {"type": "tool_done", "tool": "rag_search"}
    yield {"type": "token", "content": "CBT involves cognitive restructuring."}
    yield {"type": "done"}

async def mock_agent_stream_error(messages):
    raise RuntimeError("LLM unavailable")
    yield  # makes it an async generator

def parse_sse(response_text: str) -> list[dict]:
    events = []
    for line in response_text.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events

# --- Health ---

@pytest.mark.integration
def test_health_returns_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

@pytest.mark.integration
def test_health_has_vector_store_key():
    r = client.get("/health")
    assert "vector_store" in r.json()

# --- Normal chat ---

@pytest.mark.integration
def test_chat_normal_contains_token_and_done():
    with patch("backend.main.run_agent_stream", mock_agent_stream_normal):
        r = client.post("/chat", json={"message": "What is CBT?", "session_id": "s1"})
    events = parse_sse(r.text)
    types = [e["type"] for e in events]
    assert "token" in types
    assert types[-1] == "done"

# --- Crisis ---

@pytest.mark.integration
def test_chat_crisis_contains_crisis_event_not_token():
    r = client.post("/chat", json={"message": "I want to kill myself", "session_id": "s2"})
    events = parse_sse(r.text)
    types = [e["type"] for e in events]
    assert "crisis" in types
    assert "token" not in types

# --- Session memory ---

@pytest.mark.integration
def test_session_memory_persists_across_turns():
    with patch("backend.main.run_agent_stream", mock_agent_stream_normal):
        client.post("/chat", json={"message": "Hello", "session_id": "s3"})
        from backend.main import session_store
        assert len(session_store["s3"]) >= 2  # HumanMessage + AIMessage

# --- Error handling ---

@pytest.mark.integration
def test_chat_agent_exception_returns_error_event():
    with patch("backend.main.run_agent_stream", mock_agent_stream_error):
        r = client.post("/chat", json={"message": "Hello", "session_id": "s4"})
    events = parse_sse(r.text)
    types = [e["type"] for e in events]
    assert "error" in types

# --- Validation ---

@pytest.mark.integration
def test_chat_missing_message_returns_422():
    r = client.post("/chat", json={"session_id": "s5"})
    assert r.status_code == 422
```

---

## Verify
```bash
# Run integration + unit tests (no API keys needed)
pytest -m "unit or integration" -v

# Manual curl smoke test (server must be running)
uvicorn backend.main:app --reload --port 8000

curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is CBT?", "session_id": "test-1"}'
# Expected: data: {"type": "tool_use", ...}  data: {"type": "token", ...}  data: {"type": "done"}

curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to kill myself", "session_id": "test-2"}'
# Expected: data: {"type": "crisis", ...}  data: {"type": "done"}
```
