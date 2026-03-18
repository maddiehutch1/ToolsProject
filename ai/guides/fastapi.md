# FastAPI Guide
## Usage in This Project

**Source:** [FastAPI Official Docs](https://fastapi.tiangolo.com) — verified March 2026  
**Package:** `fastapi>=0.115.0` + `uvicorn[standard]>=0.30.0`  
**Used in:** `backend/main.py`

---

## Why FastAPI

FastAPI is chosen for this project because:
- Native `async`/`await` support — required for non-blocking SSE streaming
- `StreamingResponse` built in — no third-party SSE library needed
- `StaticFiles` mount — serves the frontend with zero extra config
- Pydantic v2 integration — request body validation is automatic
- Auto-generated `/docs` (Swagger UI) — useful for manual testing during development

---

## Installation

```bash
pip install fastapi uvicorn[standard]
```

---

## Minimal App Structure

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

app = FastAPI(title="Mental Health Companion")

@app.get("/health")
async def health():
    return {"status": "ok", "vector_store": "loaded"}
```

Run with:
```bash
uvicorn backend.main:app --reload --port 8000
```

---

## Server-Sent Events (SSE) with StreamingResponse

SSE is a browser-native protocol for server-to-client streaming over a single HTTP connection.  
FastAPI delivers SSE via `StreamingResponse` with `media_type="text/event-stream"`.

### Format Rules
Each SSE event must follow this exact format:
```
data: <payload>\n\n
```
- Two newlines (`\n\n`) terminate each event — this is the SSE spec boundary
- The payload here is always a JSON string matching the project's event protocol

### Async Generator Pattern

```python
from fastapi.responses import StreamingResponse

async def event_generator(messages, session_id):
    async for json_str in run_agent_stream(messages, session_id):
        yield f"data: {json_str}\n\n"

@app.post("/chat")
async def chat(body: ChatRequest):
    return StreamingResponse(
        event_generator(messages, body.session_id),
        media_type="text/event-stream",
    )
```

### With Crisis Check (pre-LLM gate)

```python
from backend.crisis import detect_crisis, CRISIS_RESPONSE

@app.post("/chat")
async def chat(body: ChatRequest):
    if detect_crisis(body.message):
        async def crisis_stream():
            yield f"data: {json.dumps({'type': 'crisis', 'content': CRISIS_RESPONSE})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return StreamingResponse(crisis_stream(), media_type="text/event-stream")

    # ... normal agent flow
```

### Error Handling Inside the Stream

Because headers are already sent once streaming starts, errors can't be returned as HTTP status codes. Instead, stream an error event:

```python
async def event_generator(messages, session_id):
    try:
        async for json_str in run_agent_stream(messages, session_id):
            yield f"data: {json_str}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    finally:
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
```

---

## Pydantic Request Models

Define request bodies in `backend/models.py`. FastAPI validates incoming JSON automatically.

```python
# backend/models.py
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: str

class HealthResponse(BaseModel):
    status: str
    vector_store: str
```

Use in endpoint:
```python
@app.post("/chat")
async def chat(body: ChatRequest):
    # body.message and body.session_id are validated strings
    ...
```

---

## Serving the Frontend (Static Files)

FastAPI can serve the `frontend/` folder directly, eliminating the need for a separate web server.

```python
from fastapi.staticfiles import StaticFiles

# Mount LAST — after all API routes are defined
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
```

> **Important:** Mount the static files **after** all route definitions. FastAPI matches routes in registration order; mounting `/` first would intercept all API calls.

With this setup, opening `http://localhost:8000` serves `frontend/index.html`.

---

## CORS (if needed for local dev)

If you open `frontend/index.html` directly from the filesystem (rather than through the FastAPI static mount), the browser will block cross-origin requests. Add CORS middleware:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## In-Memory Session Store

This project uses a simple in-memory dict for conversation history. It lives in `main.py` or a dedicated module:

```python
from langchain_core.messages import HumanMessage, AIMessage
from typing import Dict, List
from langchain_core.messages import BaseMessage

session_store: Dict[str, List[BaseMessage]] = {}

def get_or_create_history(session_id: str) -> List[BaseMessage]:
    if session_id not in session_store:
        session_store[session_id] = []
    return session_store[session_id]
```

> Sessions are lost on server restart — this is acceptable for the MVP.

---

## Testing the SSE Endpoint with curl

```bash
# Basic test
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is CBT?", "session_id": "test-123"}'

# Crisis keyword test
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to kill myself", "session_id": "crisis-test"}'

# Health check
curl http://localhost:8000/health
```

Expected output: a stream of `data: {...}` lines, ending with `data: {"type": "done"}`.

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| SSE stream cuts off immediately | Ensure the async generator uses `yield`, not `return` |
| Browser buffers the stream | Set `media_type="text/event-stream"` exactly — no charset suffix |
| Static files intercept `/chat` | Mount `StaticFiles` **after** all `@app.post` / `@app.get` registrations |
| Session state shared between tests | Reset `session_store` in test fixtures |
| Uvicorn logs pollute test output | Use `--log-level warning` in dev; suppress in test with pytest config |

---

## Key References

- [FastAPI Docs — StreamingResponse](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)
- [FastAPI Docs — Static Files](https://fastapi.tiangolo.com/tutorial/static-files/)
- [FastAPI Docs — Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [Uvicorn Docs](https://www.uvicorn.org)
