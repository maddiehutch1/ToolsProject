# Phase 2 Roadmap — Knowledge Base & RAG Tool
**Target:** Day 1–2  
**Status:** Not started

---

## Read First
- `aiDocs/context.md` — AI orientation and document map  
- `aiDocs/mvp.md` — canonical project structure and Definition of Done  
- `ai/guides/langchain-openai.md` — `OpenAIEmbeddings` setup  
- `ai/guides/faiss.md` — FAISS ingest and load patterns

---

## Goal
A working FAISS vector index built from real knowledge base documents, queryable via a LangChain `@tool`.

---

## Checklist

**Knowledge Base Documents**
- [ ] Author all 6 markdown documents in `knowledge_base/` — substantive content, no stubs:
  - `cbt_techniques.md` — thought records, cognitive restructuring, behavioral activation
  - `dbt_skills.md` — TIPP, DEAR MAN, PLEASE skills
  - `mindfulness_exercises.md` — MBSR body scan, breath awareness
  - `grounding_techniques.md` — 5-4-3-2-1, box breathing, cold water
  - `sleep_hygiene.md` — CBT-I guidelines, sleep restriction, sleep efficiency formula
  - `crisis_resources.md` — 988 Lifeline, Crisis Text Line (741741), NAMI, SAMHSA

**Ingest Script**
- [ ] Implement `backend/ingest.py` — `TextLoader` → `RecursiveCharacterTextSplitter(500/50)` → `OpenAIEmbeddings("text-embedding-3-small")` → `FAISS.save_local("faiss_index")`
- [ ] Run `python backend/ingest.py`; confirm `faiss_index/index.faiss` and `faiss_index/index.pkl` exist on disk

**RAG Tool**
- [ ] Implement `backend/tools/rag_search.py` — load FAISS, `retriever(k=4)`, `@tool` decorated `rag_search(query: str) -> str` returning top-4 chunks each prefixed `[source_filename]`
- [ ] Create `backend/tools/__init__.py` (empty)

**Unit Tests**
- [ ] Write `tests/test_rag_search.py` — mock the retriever (no FAISS or OpenAI hits), 3+ tests: formatted `[source]\ncontent` output, empty results handled, source attribution present
- [ ] All tests marked `@pytest.mark.unit`

---

## Key Files Created
```
knowledge_base/cbt_techniques.md
knowledge_base/dbt_skills.md
knowledge_base/mindfulness_exercises.md
knowledge_base/grounding_techniques.md
knowledge_base/sleep_hygiene.md
knowledge_base/crisis_resources.md
backend/ingest.py
backend/tools/__init__.py
backend/tools/rag_search.py
tests/test_rag_search.py
faiss_index/             (generated, not in git)
```

---

## Phase Gate
```bash
pytest -m unit -v
# Expected: test_rag_search.py passes; all Phase 1 tests still green
```

---

## Previous Phase
[Phase 1 — Project Scaffolding](./phase-1-scaffolding-roadmap.md)

## Next Phase
[Phase 3 — Web Search & Calculator Tools](./phase-3-tools-roadmap.md)
