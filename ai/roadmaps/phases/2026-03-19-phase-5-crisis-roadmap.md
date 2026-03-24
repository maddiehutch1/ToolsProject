# 2026-03-19 Phase 5 Roadmap — Crisis Detection & System Prompt
**Target:** Day 3  
**Status:** Not started

---

## Read First
- `aiDocs/context.md` — AI orientation and document map  
- `aiDocs/mvp.md` — canonical project structure and Definition of Done  
- `aiDocs/architecture.md §Crisis Detection` — keyword list, `CRISIS_RESPONSE` format, gate behavior

---

## Goal
A hard pre-LLM safety gate that intercepts crisis messages before the agent runs, plus a calibrated system prompt added to the agent.

---

## Checklist

**Crisis Detection**
- [ ] Implement `backend/crisis.py`:
  - Keyword list: `["want to die", "end my life", "kill myself", "self-harm", "suicidal", "hurt myself", "don't want to be here"]`
  - `detect_crisis(message: str) -> bool` — case-insensitive substring match
  - `CRISIS_RESPONSE` string constant — must include 988 Lifeline, Crisis Text Line (text HOME to 741741), NAMI Helpline, SAMHSA National Helpline

**System Prompt**
- [ ] Add `SYSTEM_PROMPT` constant to `backend/agent.py`:
  - Role: psychoeducational companion, not a therapist
  - Prefer `rag_search` for mental health technique questions
  - Always cite which tool and source document was used
  - Warm, non-judgmental, evidence-based tone
- [ ] Prepend `SystemMessage(content=SYSTEM_PROMPT)` to messages inside `run_agent_stream`

**Unit Tests**
- [ ] Write `tests/test_crisis.py`:
  - 6+ tests — `detect_crisis` returns `True` for keyword variants (mixed case, mid-sentence)
  - 4+ tests — `detect_crisis` returns `False` for normal messages
  - 1 test — `CRISIS_RESPONSE` contains `"988"` and `"741741"`
  - All marked `@pytest.mark.unit`
  - No mocking needed — `crisis.py` is pure Python, zero external dependencies

---

## Key Files Created / Modified
```
backend/crisis.py          (new)
backend/agent.py           (system prompt added)
tests/test_crisis.py       (new)
```

---

## Phase Gate
```bash
pytest -m unit -v
# Expected: all prior unit tests green + test_crisis.py (11+ tests) passes
```

---

## Previous Phase
[Phase 4 — LangGraph Agent](./2026-03-19-phase-4-agent-roadmap.md)

## Next Phase
[Phase 6 — FastAPI Streaming Endpoint](./2026-03-19-phase-6-api-roadmap.md)
