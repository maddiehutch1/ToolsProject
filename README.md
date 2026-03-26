# Innerly — Mental Wellness Companion

A psychoeducational chat agent that provides evidence-based coping strategies, technique explanations, and assessment scoring. **Not a therapist.** If you are in crisis, call or text **988**.

Built as an agentic LLM application using LangGraph, FastAPI, and a vanilla JS frontend with SSE streaming.

---

## Architecture

```
Browser (Vanilla JS / SSE)
  └── POST /chat → FastAPI
        ├── Crisis keyword gate  (pre-LLM, hardcoded response)
        └── LangGraph StateGraph
              ├── call_model      (gpt-4o-mini)
              └── tools
                    ├── rag_search   → FAISS vector store (6 KB docs)
                    ├── web_search   → Tavily API
                    └── calculator   → simpleeval (safe math)
```

---

## Prerequisites

- Python 3.11+
- [OpenAI API key](https://platform.openai.com/api-keys)
- [Tavily API key](https://app.tavily.com/)

---

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure environment**
```bash
cp .env.example .env
```
Open `.env` and fill in your keys:
```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

**3. Build the knowledge base index**

Run once. Chunks and embeds the 6 documents in `knowledge_base/` into a local FAISS index.
```bash
python backend/ingest.py
```

---

## Run

```bash
uvicorn backend.main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## Test

```bash
# Unit tests only — no API keys required
pytest -m unit -v

# Unit + integration tests — no API keys required
pytest -m "unit or integration" -v

# Full suite (E2E) — requires API keys in .env
pytest -v
```

---

## Project Structure

```
ToolsProject/
├── backend/
│   ├── main.py           # FastAPI app — POST /chat, GET /health, static mount
│   ├── agent.py          # LangGraph StateGraph + run_agent_stream generator
│   ├── crisis.py         # Keyword detection + hardcoded crisis response
│   ├── ingest.py         # One-time: load → chunk → embed → save FAISS index
│   ├── models.py         # Pydantic models: ChatRequest
│   └── tools/
│       ├── rag_search.py # FAISS retriever — top-4 chunks with source attribution
│       ├── web_search.py # TavilySearch — top-5 results
│       └── calculator.py # simpleeval wrapper (PHQ-9 / GAD-7 scoring)
├── knowledge_base/       # 6 markdown documents (CBT, DBT, mindfulness, etc.)
├── frontend/
│   ├── index.html        # Single-page chat UI
│   ├── style.css         # Innerly design system
│   └── app.js            # SSE streaming client
├── tests/                # Unit + integration test suite (47 tests)
├── ai/                   # Roadmaps, guides, and changelog
├── aiDocs/               # PRD, MVP spec, architecture, test plan
├── .env.example
├── requirements.txt
└── pytest.ini
```

---

## SSE Event Protocol

Every server event from `POST /chat` follows this shape:

```
data: {"type": "<event_type>", ...fields}\n\n
```

| `type` | Trigger | Extra fields |
|--------|---------|-------------|
| `token` | LLM text chunk | `"content": str` |
| `tool_use` | Agent calls a tool | `"tool": str` |
| `crisis` | Crisis keyword detected | `"content": str` |
| `error` | Unhandled exception | `"content": str` |
| `done` | Stream complete | — |

---

## Disclaimer

This tool is not a substitute for professional mental health care. It is a coursework project demonstrating agentic LLM patterns and does not provide diagnosis, therapy, or clinical advice.
