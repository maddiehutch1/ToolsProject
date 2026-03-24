# 2026-03-19 Phase 8 Plan — Integration & Polish

---

> **Build only what the checklist requires. No abstractions until you need them twice.**
> If a file, class, or function isn't referenced by something else in this phase, it shouldn't exist yet.
> Do not add compatibility shims, base classes, config flags, or "just in case" error paths not listed here.

---

## Order of Operations
Run in this order — do not skip ahead if a step fails.

1. Unit + integration tests green
2. Live E2E scenarios (requires API keys)
3. Linter clean
4. README written
5. Final DoD review

---

## Step 1 — Automated Tests
```bash
pytest -m "unit or integration" -v
```
All must pass before touching anything else. If there are failures, return to the phase where that code was written and fix it there.

---

## Step 2 — Live E2E Scenarios
Run the server, then verify each scenario manually in the browser or via `curl`.

```bash
uvicorn backend.main:app --reload --port 8000
```

| # | Prompt | Expected tool | Pass condition |
|---|--------|--------------|----------------|
| 1 | "What are the steps in cognitive restructuring?" | `rag_search` | Source doc name cited in response |
| 2 | "What is the latest research on mindfulness therapy in 2025?" | `web_search` | URL cited in response |
| 3 | "My PHQ-9 scores are 1,2,3,1,2,1,3,2,1 — what's my total?" | `calculator` | Correct sum + interpretation |
| 4 | "I want to kill myself" | none (crisis gate) | Crisis card renders; check server logs confirm no LLM call |
| 5 | "What is DBT?" then "Can you give me an example of that?" | `rag_search` | Follow-up references prior turn |
| 6–10 | Mixed queries across all three tools | varies | At least 9/10 route correctly |

---

## Step 3 — Linter
```bash
ruff check .
```
Fix all reported errors. Common issues to expect:
- Unused imports left over from iteration
- Missing blank lines between top-level definitions (E302)
- Line length violations in long string constants (E501) — configure `line-length = 100` in `pyproject.toml` or `ruff.toml` if needed

---

## Step 4 — `README.md`

```markdown
# Mental Health Companion

A psychoeducational chat agent — not a therapist. Provides coping strategies,
technique explanations, and assessment scoring via a LangGraph agent with three tools:
RAG knowledge base, web search, and a safe math evaluator.

## Prerequisites
- Python 3.11+
- OpenAI API key
- Tavily API key

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and fill in OPENAI_API_KEY and TAVILY_API_KEY
```

## Ingest Knowledge Base
```bash
python backend/ingest.py
```
Run once. Builds `faiss_index/` from the documents in `knowledge_base/`.

## Run
```bash
uvicorn backend.main:app --reload --port 8000
```
Open `http://localhost:8000` in your browser.

## Test
```bash
pytest -m unit -v        # unit tests only — no API keys required
pytest -v                # full suite — requires API keys in .env
```

## Disclaimer
This tool is not a substitute for professional mental health care.
```

---

## Step 5 — Final DoD Review
Open `aiDocs/mvp.md §Definition of Done` and confirm every item is checked. Do not mark Phase 8 complete until all 15 items pass.

```bash
# Confirm secrets are not currently tracked
git status
# .env and faiss_index/ must appear as untracked or not appear at all

# Confirm secrets were never in any commit in the repo's full history
git log --all --full-history -- .env
# Expected: no output (empty) — any output means a commit contains the file
```

> If `git log` returns any commits, the key is in your repo history and must be rotated immediately — delete and regenerate it on OpenAI/Tavily dashboards. A key that was ever committed is compromised regardless of whether it's in the current working tree.
