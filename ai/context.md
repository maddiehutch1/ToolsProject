# Project Context
## Mental Health Companion — Agentic Chat Application

---

## What This Project Is

A web-based conversational AI agent that provides **evidence-based mental health guidance** — not therapy. The agent draws from a curated local knowledge base of recognized therapeutic frameworks (CBT, DBT, mindfulness, ACT, CBT-I) and can search the web for current resources. Users interact through a streaming chat UI in the browser.

The project was built as a coursework assignment to demonstrate **agentic LLM patterns**: a LangGraph orchestration loop, three distinct tools (RAG search, web search, calculator), Server-Sent Event streaming, and responsible deployment of AI in a sensitive domain.

**The agent is a psychoeducational companion. It does not diagnose, treat, or replace professional mental health care.**

---

## Core Capabilities

| Capability | Implementation |
|-----------|---------------|
| Conversational chat UI | Vanilla HTML/CSS/JS, single-page |
| Streaming responses | Server-Sent Events (SSE) via FastAPI |
| Agent orchestration | LangGraph `StateGraph` |
| Knowledge base retrieval (RAG) | LangChain + FAISS + OpenAI embeddings |
| Live web search | Tavily API |
| Math / assessment scoring | `simpleeval` (safe expression evaluator) |
| Crisis safety net | Server-side keyword detection → hardcoded resource response |

---

## What Is In Scope

- A single-page chat interface with a persistent disclaimer
- Streaming LLM responses delivered token-by-token
- Three agentic tools the LLM can invoke autonomously:
  - **RAG tool** — semantic search over the local mental health knowledge base
  - **Web search tool** — live Tavily search for current information
  - **Calculator tool** — safe math evaluation for scoring tools (PHQ-9, GAD-7, sleep efficiency)
- A curated local knowledge base of 6 markdown documents
- In-session conversation history
- Crisis keyword detection with a hardcoded resource response (988, Crisis Text Line)
- Tool-use indicators visible in the chat UI

## What Is Out of Scope

- **Clinical diagnosis, treatment, or therapy** — the agent explicitly cannot and should not attempt this
- User authentication or accounts
- Persistent chat history across browser sessions
- Mobile-native or responsive mobile layout
- Cloud deployment or containerization (Docker)
- Fine-tuning or training a custom model
- Rate limiting, cost controls, or usage analytics
- LLM-evaluated (vs. keyword-based) crisis detection
- An expanded knowledge base beyond the initial 6 documents

---

## Tech Stack at a Glance

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI |
| Agent loop | LangGraph `StateGraph` |
| LLM | OpenAI `gpt-4o-mini` via `langchain-openai` |
| RAG pipeline | LangChain loaders → FAISS (local flat files) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Web search | `tavily-python` |
| Math eval | `simpleeval` |
| Frontend | Vanilla HTML + CSS + JavaScript |
| Streaming | Server-Sent Events (SSE) |
| Config | `python-dotenv` |

---

## Project Documents

### [`aiDocs/prd.md`](../aiDocs/prd.md) — Product Requirements Document
The full product specification. Covers:
- Problem statement and goals
- Ethical guardrails and safety requirements
- Complete user stories
- Functional requirements for all three tools, the agent, and the UI
- Non-functional requirements (performance, security, safety, maintainability)
- API contracts (request/response shapes, SSE event types, tool schemas)
- Assumptions, open questions, and success criteria

**Read this first** to understand *what* the product does and *why*.

---

### [`aiDocs/mvp.md`](../aiDocs/mvp.md) — Minimum Viable Product Document
The scoped build plan for the first working version. Covers:
- What is in/out of the MVP
- Full tech stack with rationale for each choice
- Proposed folder and file structure
- 8-phase implementation plan with day-by-day checkboxes
- Code sketches for the four core pieces (LangGraph agent, SSE endpoint, RAG tool, frontend consumer)
- Environment variable reference
- Definition of Done checklist
- Risk register with mitigations
- Estimated 5-day timeline

**Read this** to understand *how* and *when* the product gets built.

---

### [`aiDocs/architecture.md`](../aiDocs/architecture.md) — Architecture Document
The technical design reference. Covers:
- Component diagram and data flow
- LangGraph state graph design (nodes, edges, state shape)
- RAG pipeline design (ingest flow, retrieval flow)
- SSE streaming event protocol
- Knowledge base document inventory
- Crisis detection logic
- Environment and configuration reference

**Read this** to understand the system's internal structure before writing or reviewing code.

---

## Key Conventions

- All API keys live in `.env` and are never committed to version control
- The FAISS index is built once via `backend/ingest.py` and persisted to `faiss_index/` as two flat files (`index.faiss` + `index.pkl`)
- The LangGraph agent uses `@tool`-decorated LangChain functions — tool schemas are derived automatically
- SSE events follow a consistent shape: `{ "type": "token" | "tool_use" | "tool_done" | "crisis" | "error" | "done", ... }`
- The crisis check runs **before** the LLM is invoked — it is a hard gate, not a soft suggestion
- The agent's system prompt instructs it to always cite which tool it used

---

## Environment Variables Required

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | LLM calls (`gpt-4o-mini`) and embeddings (`text-embedding-3-small`) |
| `TAVILY_API_KEY` | Tavily web search |
| `PORT` | FastAPI server port (optional, default `8000`) |
| `FAISS_INDEX_PATH` | Path to persisted FAISS index directory (optional, default `"faiss_index"`) |
