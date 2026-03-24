# 2026-03-19 Phase 8 Roadmap — Integration & Polish
**Target:** Day 5  
**Status:** Not started

---

## Read First
- `aiDocs/context.md` — AI orientation and document map  
- `aiDocs/mvp.md §Definition of Done` — every item must be checked off before this phase is complete  
- `aiDocs/cliTestPlan.md` — full test inventory and run commands

---

## Goal
All three test tiers green, live E2E scenarios passing, linter clean, `README.md` complete. No new features — fix what's rough and verify what's built.

> **This phase is verification and documentation only.** If something new needs building, it should have been caught in an earlier phase gate. Add it there, don't expand scope here.

---

## Checklist

**Automated Tests — Run First**
- [ ] `pytest -m "unit or integration" -v` — must be 100% green before anything else
- [ ] Fix any regressions before proceeding

**Live E2E Scenarios (real LLM + real APIs)**
- [ ] CBT question → `rag_search` fires → source document name cited in response
- [ ] Current-events question → `web_search` fires → URL cited in response
- [ ] PHQ-9 scoring question → `calculator` fires → numeric result + clinical interpretation
- [ ] Crisis keyword → hardcoded response card renders; confirm LLM not called via server logs
- [ ] Conversational follow-up references the previous turn (multi-turn memory)
- [ ] 10-query tool-routing test — at least 9/10 route to the correct tool

**Linter**
- [ ] `ruff check .` — fix all errors before marking done

**`README.md`**
- [ ] Prerequisites: Python 3.11+, OpenAI and Tavily API keys
- [ ] Installation: `pip install -r requirements.txt`
- [ ] Configuration: copy `.env.example` → `.env`, fill in keys
- [ ] Ingest: `python backend/ingest.py`
- [ ] Run: `uvicorn backend.main:app --reload --port 8000`
- [ ] Test commands: `pytest -m unit -v` (no keys), `pytest -v` (all keys required)

**Final Checks**
- [ ] `git status` confirms `.env` and `faiss_index/` are untracked or ignored
- [ ] Review every item in `aiDocs/mvp.md §Definition of Done` — all 15 checked

---

## Phase Gate (Final)
```bash
pytest -v          # all tiers green
ruff check .       # zero errors
```

---

## Previous Phase
[Phase 7 — Frontend](./2026-03-19-phase-7-frontend-roadmap.md)
