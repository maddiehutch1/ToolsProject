# 2026-03-19 Phase 3 Roadmap — Web Search & Calculator Tools
**Target:** Day 2  
**Status:** Complete

---

## Read First
- `aiDocs/context.md` — AI orientation and document map  
- `aiDocs/mvp.md` — canonical project structure and Definition of Done  
- `ai/guides/tavily.md` — `langchain-tavily` `TavilySearch` integration  
- `ai/guides/simpleeval.md` — safe expression evaluation

---

## Goal
Two more working `@tool` functions with full unit test coverage before they are wired into the agent.

---

## Checklist

**Web Search Tool**
- [x] Implement `backend/tools/web_search.py` — `TavilySearch(max_results=5)`, `@tool` decorated `web_search(query: str) -> str`, format output as title + URL + snippet per result, catch all exceptions and return a descriptive error string
- [x] Write `tests/test_web_search.py` — mock `_tavily.invoke` (no real API calls), 4+ tests: formatted output contains title and URL, all results present, empty results handled, API error returns graceful string
- [x] All tests marked `@pytest.mark.unit`

**Calculator Tool**
- [x] Implement `backend/tools/calculator.py` — `simpleeval.simple_eval` with whitelisted functions (`sqrt`, `abs`, `round`, `pow`, `floor`, `ceil`), `@tool` decorated `calculator(expression: str) -> str`, return result as string or descriptive error
- [x] Write `tests/test_calculator.py` — 9+ tests: basic arithmetic, PHQ-9 sum, GAD-7 sum, `sqrt(144)`, sleep efficiency formula, zero division, invalid syntax, `import os` attempt blocked
- [x] All tests marked `@pytest.mark.unit`
- [x] No mocking required — `simpleeval` has no external dependencies

---

## Key Files Created
```
backend/tools/web_search.py
backend/tools/calculator.py
tests/test_web_search.py
tests/test_calculator.py
```

---

## Phase Gate
```bash
pytest -m unit -v
# Expected: test_calculator.py (9 pass), test_web_search.py (4 pass),
#           test_rag_search.py (4 — no regressions)
```

---

## Previous Phase
[Phase 2 — Knowledge Base & RAG Tool](./2026-03-19-phase-2-rag-roadmap.md)

## Next Phase
[Phase 4 — LangGraph Agent](./2026-03-19-phase-4-agent-roadmap.md)
