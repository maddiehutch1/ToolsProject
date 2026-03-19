# 2026-03-19 Phase 1 Roadmap — Project Scaffolding
**Target:** Day 1  
**Status:** Not started

---

## Read First
- `aiDocs/context.md` — AI orientation and document map  
- `aiDocs/mvp.md` — canonical project structure and Definition of Done  
- `ai/guides/fastapi.md` — FastAPI setup patterns used in this project  
- `aiDocs/cliTestPlan.md` — `pytest.ini` config and `conftest.py` implementation

---

## Goal
A clean repo skeleton that runs with no errors — including a working test harness — before any business logic is written.

---

## Checklist

**Repo & Config**
- [ ] Initialize folder structure per `aiDocs/mvp.md §Project Structure`
- [ ] Create `requirements.txt` with all pinned dependencies (see Dependency Reference in main roadmap)
- [ ] Create `.env.example` with `OPENAI_API_KEY` and `TAVILY_API_KEY` placeholders
- [ ] Create `.gitignore` — exclude `.env`, `faiss_index/`, `__pycache__/`, `*.pyc`

**FastAPI Skeleton**
- [ ] `backend/main.py` — FastAPI app, `GET /health` returning `{"status": "ok"}`
- [ ] `backend/models.py` — `ChatRequest` (message, session_id) Pydantic model
- [ ] Verify server starts: `uvicorn backend.main:app --reload --port 8000`

**Test Infrastructure**
- [ ] `pytest.ini` — `asyncio_mode = auto`, declare `unit`, `integration`, `e2e` markers
- [ ] `tests/conftest.py` — env var fixtures, shared `TestClient` fixture
- [ ] Verify `pytest --collect-only` exits 0

---

## Key Files Created
```
backend/main.py
backend/models.py
requirements.txt
.env.example
.gitignore
pytest.ini
tests/conftest.py
```

---

## Phase Gate
```bash
pytest --collect-only   # must exit 0; zero test failures
```

---

## Next Phase
[Phase 2 — Knowledge Base & RAG Tool](./2026-03-19-phase-2-rag-roadmap.md)
