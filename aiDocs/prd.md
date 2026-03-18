# Product Requirements Document
## Mental Health Companion — Agentic Chat Application

**Version:** 2.0 | **Date:** March 9, 2026

---

## Product

Psychoeducational chat agent grounded in a local knowledge base (RAG) and live web search. **Not a therapist.** Provides coping strategies, technique explanations, and assessment scoring via three autonomous tools. Persistent disclaimer required at all times.

**Ethical requirement:** Crisis messages (suicidal ideation, self-harm) must trigger a hardcoded resource response *before* the LLM is invoked — never delegate to the model.

---

## Scope

**In:** Single-page chat UI · SSE streaming · RAG tool (FAISS) · Web search (Tavily) · Calculator (PHQ-9/GAD-7) · LangGraph agent · In-session memory · Crisis injection · Tool badges

**Out:** Auth · Persistent history · Mobile layout · Docker · Fine-tuning · Rate limiting · LLM-evaluated crisis detection · Expanded KB (20+ docs)

---

## User Stories

| ID | User wants to... | Agent does... |
|----|-----------------|---------------|
| US-01 | Ask about coping strategies | Returns sourced technique from knowledge base |
| US-02 | Ask about current research | Searches web, summarizes results |
| US-03 | Get PHQ-9 / GAD-7 score | Uses calculator, interprets result |
| US-04 | See response stream word-by-word | SSE token streaming |
| US-05 | See which tool was used | Tool badge in chat bubble |
| US-06 | Ask a follow-up question | In-session history maintains context |
| US-07 | Submit via Enter or click | Standard form UX |
| US-08 | Express acute distress | Hardcoded crisis resources, no LLM |

---

## Functional Requirements

### Chat UI
- Scrollable history; distinct user/agent message bubbles
- SSE streaming token rendering; complete response on finish is acceptable fallback
- Loading indicator during agent processing; auto-scroll to newest message
- Tool badge displayed on `tool_use` event (e.g., "Knowledge Base", "Web Search", "Calculator")
- Persistent disclaimer: *"This tool is not a substitute for professional mental health care."*

### RAG Tool
- ≥5 real authored knowledge base documents — no stubs
- Pipeline: `TextLoader → RecursiveCharacterTextSplitter(500/50) → OpenAIEmbeddings → FAISS`
- Returns top-4 chunks, each prefixed with source filename
- Agent response must cite source document(s) by name

### Web Search Tool
- Tavily API; returns top-5 results (title, URL, snippet)
- Handles API errors gracefully with a descriptive return string

### Calculator Tool
- `simpleeval` — no raw `eval`
- Supports arithmetic, exponentiation, `sqrt`, `abs`, `round`
- Used for PHQ-9, GAD-7, sleep efficiency scoring

### Agent / Backend
- `POST /chat` → SSE stream (`StreamingResponse`, `media_type="text/event-stream"`)
- LangGraph `StateGraph`: `call_model` → conditional → `tools` → `call_model` → `END`
- `gpt-4o-mini` with `bind_tools`; stream via `.astream_events(version="v2")`
- In-memory `session_store[session_id]`; full history passed every turn
- System prompt: role as companion (not therapist), prefer `rag_search` for KB questions, cite source, warm tone

---

## API Contracts

### `POST /chat`
**Request:** `{ "message": str, "session_id": str }`

**Response — SSE stream:**
```
data: {"type": "tool_use",  "tool": "rag_search"}
data: {"type": "tool_done", "tool": "rag_search"}
data: {"type": "token",     "content": "Here are some grounding..."}
data: {"type": "done"}
```

**Crisis path:**
```
data: {"type": "crisis", "content": "Please call or text 988..."}
data: {"type": "done"}
```

**Error path:**
```
data: {"type": "error", "content": "..."}
data: {"type": "done"}
```

### `GET /health`
```json
{ "status": "ok", "vector_store": "loaded" }
```

### Tool Docstrings (LangChain derives schemas automatically)
- `rag_search(query: str)` — *"Searches the mental health knowledge base for evidence-based techniques. Use for any question about CBT, DBT, mindfulness, grounding, sleep, or crisis resources."*
- `web_search(query: str)` — *"Searches the web for current information not in the knowledge base."*
- `calculator(expression: str)` — *"Evaluates a math expression safely. Use for PHQ-9, GAD-7, sleep efficiency, or any arithmetic."*

---

## Success Criteria

- RAG tool invoked and source cited for ≥5 knowledge base questions
- Web search invoked for ≥3 current-information questions
- Calculator correctly scores PHQ-9 and GAD-7 inputs
- Correct tool routing ≥90% of a 10-query test set
- Crisis keyword triggers hardcoded response 100% of the time, LLM never called
- Multi-turn follow-up resolves correctly within the same session
- First token appears within 3 seconds under local conditions
- No API keys in version control; `.env` in `.gitignore`
