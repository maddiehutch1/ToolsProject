# CLI Test Plan
## Mental Health Companion — Agentic Chat Application

**Version:** 1.0 | **Date:** March 16, 2026

---

## Test Tiers

| Tier | Scope | External I/O | API Keys | Run at |
|------|-------|-------------|----------|--------|
| **Unit** | Single function, all I/O mocked | None | No | Every phase gate |
| **Integration** | Component + real local deps, APIs mocked | FAISS fixture on disk | No | Phases 4, 6, 8 |
| **E2E** | Full stack, real LLM + APIs | OpenAI + Tavily | Yes | Phase 8 only |

**Rule:** Unit tests never touch the network or filesystem. Integration tests never call OpenAI or Tavily.

---

## Setup

### `pytest.ini`
```ini
[pytest]
asyncio_mode = auto
markers =
    unit: isolated, no I/O, all external calls mocked
    integration: real local deps (FAISS fixture), external APIs mocked
    e2e: full stack, real API keys required
```

### `tests/conftest.py`
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

`autouse=True` ensures fake keys are set before any module import that reads `OPENAI_API_KEY`.

**FAISS fixture index:** Build once from a small `tests/fixtures/sample_kb.md` document using a real key, commit the resulting `tests/fixtures/faiss_index/` (≈50KB). Integration tests then never need an API key.

---

## Run Commands

```bash
pytest --collect-only                  # Phase 1 gate — verify harness only
pytest -m unit -v                      # Phase 2, 3, 5 gates
pytest -m "unit or integration" -v     # Phase 4, 6 gates — needs FAISS fixture
pytest -v                              # Phase 8 gate — full suite
pytest tests/test_calculator.py -v     # single file
```

---

## Test Inventory

| File | Tier | Phase | Covers | Min tests |
|------|------|-------|--------|-----------|
| `tests/test_calculator.py` | unit | 3 | `simple_eval` wrapper, PHQ-9, GAD-7, `sqrt`, ZeroDivisionError, invalid syntax, blocked `import` | 9 |
| `tests/test_web_search.py` | unit | 3 | Formatted output, empty results, API error → graceful string; mock asserts live API never called | 4 |
| `tests/test_rag_search.py` | unit | 2 | Source prefix format, multiple chunks, empty retriever; mock retriever — no FAISS in unit tier | 4 |
| `tests/test_crisis.py` | unit | 5 | Each keyword variant fires `True`; normal messages fire `False`; `CRISIS_RESPONSE` contains 988 + 741741 | 14 |
| `tests/test_agent.py` | integration | 4 | Routes to correct tool (rag/calc/web); direct answer path; `run_agent_stream` yields `token` + `done` | 6 |
| `tests/test_api.py` | integration | 6 | `GET /health`, normal SSE stream, crisis gate (agent not called), session memory, error event, HTTP 422 | 8 |

---

## Mocking Strategy

| Component | Mock target | Pattern |
|-----------|------------|---------|
| Tavily | `backend.tools.web_search._tavily` | `unittest.mock.patch` |
| FAISS retriever | `backend.tools.rag_search.retriever` | `unittest.mock.patch` |
| LLM / ChatOpenAI | `FakeListChatModel` or patch `call_model` | deterministic tool routing |
| `run_agent_stream` | `backend.main.run_agent_stream` | `patch(side_effect=async_gen)` |
| Env vars | `conftest.py` `autouse` `monkeypatch` | scoped per test, auto-reverted |

---

## Phase Gate Summary

| Phase | Command | Pass condition |
|-------|---------|---------------|
| 1 | `pytest --collect-only` | Exit 0, no errors |
| 2 | `pytest -m unit -v` | `test_rag_search` 4+ pass |
| 3 | `pytest -m unit -v` | All unit tests pass (17+) |
| 4 | `pytest -m "unit or integration" -v` | All prior + `test_agent` 6+ pass |
| 5 | `pytest -m unit -v` | All prior + `test_crisis` 14+ pass |
| 6 | `pytest -m "unit or integration" -v` | All prior + `test_api` 8+ pass |
| 7 | Manual browser checklist | 8 user stories verified in Chrome |
| 8 | `pytest -v` then `ruff check .` | 100% green + no lint errors |

---

## What Is Not Automated

| Area | Reason | Verified by |
|------|--------|------------|
| Frontend HTML/CSS/JS | No build system; no JS test framework | Manual Phase 7 browser checklist |
| LLM response quality | Non-deterministic | Manual E2E review in Phase 8 |
| Real SSE in browser | `TestClient` reads full response | Manual `curl -N` + browser test |
