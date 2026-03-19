# Phase 1 Plan — Project Scaffolding

---

## `backend/main.py`
Bare FastAPI app with a single health endpoint. No business logic yet.

```python
from fastapi import FastAPI
from backend.models import HealthResponse

app = FastAPI()

@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok"}
```

---

## `backend/models.py`
Two Pydantic models used across the app. Define both now even though `ChatRequest` isn't wired yet.

```python
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: str

class HealthResponse(BaseModel):
    status: str
```

---

## `requirements.txt`
Pin all dependencies. Verify latest stable versions on PyPI before committing.

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
python-dotenv>=1.0.0
pydantic>=2.0.0
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-community>=0.3.0
langchain-core>=0.3.0
langgraph>=0.2.0
faiss-cpu>=1.8.0
langchain-tavily>=0.1.0
simpleeval>=1.0.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
```

> Prefer exact pins (`==`) for a reproducible coursework submission.

---

## `.env.example`
```
OPENAI_API_KEY=your-openai-key-here
TAVILY_API_KEY=your-tavily-key-here
```

---

## `.gitignore`
```
.env
faiss_index/
__pycache__/
*.pyc
*.pyo
.pytest_cache/
```

---

## `pytest.ini`
Full config is in `aiDocs/cliTestPlan.md`. Minimum required:

```ini
[pytest]
asyncio_mode = auto
markers =
    unit: no external deps or API keys
    integration: requires FAISS index on disk
    e2e: requires live API keys
```

---

## `tests/conftest.py`
Full implementation is in `aiDocs/cliTestPlan.md`. Minimum required: env var fixtures and a shared `TestClient`.

```python
import pytest
from fastapi.testclient import TestClient
from backend.main import app

@pytest.fixture
def client():
    return TestClient(app)
```

---

## Verify
```bash
# Start server
uvicorn backend.main:app --reload --port 8000

# In a second terminal — confirm health endpoint
curl http://localhost:8000/health
# Expected: {"status":"ok"}

# Confirm test harness is healthy
pytest --collect-only
# Expected: exit 0, no errors
```
