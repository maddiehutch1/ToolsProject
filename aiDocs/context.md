# Project Context
## Mental Health Companion — Agentic Chat Application

---

## What This Project Is

A web-based chat agent providing **evidence-based mental health guidance — not therapy**. Built as a coursework assignment demonstrating agentic LLM patterns: LangGraph orchestration, three tools (RAG, web search, calculator), SSE streaming, and responsible AI deployment in a sensitive domain.

---

## Scope

**In:** Single-page chat UI · SSE streaming · RAG over 6 KB docs · Web search (Tavily) · Calculator (PHQ-9/GAD-7) · In-session memory · Crisis keyword gate · Tool badges

**Out:** Diagnosis/therapy · Auth · Persistent history · Mobile layout · Docker · Fine-tuning · Rate limiting · LLM crisis detection · KB beyond 6 docs

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI |
| Agent | LangGraph `StateGraph` |
| LLM | `gpt-4o-mini` via `langchain-openai` |
| RAG | LangChain loaders + FAISS (local flat files) |
| Embeddings | `text-embedding-3-small` |
| Web search | `langchain-tavily` `TavilySearch` |
| Math eval | `simpleeval` |
| Frontend | Vanilla HTML/CSS/JS |
| Streaming | Server-Sent Events (SSE) |
| Config | `python-dotenv` |

---

## Key Conventions

- API keys in `.env` — never committed
- FAISS index built once via `backend/ingest.py`; persisted as `faiss_index/index.faiss` + `index.pkl`
- All tools are `@tool`-decorated LangChain functions — schemas auto-derived from docstrings
- SSE events: `{ "type": "token"|"tool_use"|"tool_done"|"crisis"|"error"|"done", ... }`
- Crisis check is a **hard pre-LLM gate** — runs before the agent, never delegates to the model
- System prompt instructs agent to always cite which tool and source document it used

---

## Before Implementing Any Phase

**Always read `aiDocs/mvp.md` before writing any code.** It contains:
- The canonical project folder/file structure (§ Project Structure) — all files must be created at the exact paths listed there
- The Definition of Done checklist — every item must be satisfied before the project is complete
- The tech stack with rationale — do not substitute libraries without explicit instruction

Then read the per-phase roadmap file for the phase you are implementing. It will tell you which additional guide files in `ai/guides/` to consult.

---

## Document Map

| File | Read for... |
|------|------------|
| `aiDocs/prd.md` | What the product does, API contracts, success criteria |
| `aiDocs/mvp.md` | Build phases, tech stack, project structure, Definition of Done — **read before any implementation** |
| `aiDocs/architecture.md` | Component map, graph topology, RAG pipeline, SSE protocol, crisis logic |
| `aiDocs/cliTestPlan.md` | Test tiers, pytest setup, test inventory, phase gate commands |
| `ai/roadmaps/2026-03-16-mvp-roadmap.md` | Phase-by-phase build plan with detailed checklists |
| `ai/guides/` | Per-package implementation guides (FastAPI, LangGraph, FAISS, Tavily, etc.) |
