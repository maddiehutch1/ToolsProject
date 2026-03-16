# Product Requirements Document (PRD)
## Mental Health Companion — Agentic Chat Application

**Version:** 2.0  
**Date:** March 9, 2026  
**Status:** Draft

---

## 1. Overview

### 1.1 Product Summary
A web-based chat application powered by an AI agent that provides evidence-based mental health guidance. The agent draws from a curated knowledge base of well-established therapeutic frameworks (CBT, DBT, mindfulness, ACT) and can search the web for current resources — all delivered through a conversational, streaming chat UI. The agent is **not a therapist** and does not diagnose or treat; it offers psychoeducation, coping strategies, and skill-based suggestions grounded in recognized research and clinical best practices.

### 1.2 Problem Statement
People seeking mental health support often face long wait times for professional care, high costs, or simply don't know where to start. General-purpose AI assistants hallucinate advice and cannot cite specific therapeutic techniques reliably. This project demonstrates how an LLM agent equipped with a curated RAG knowledge base, live web search, and a simple utility calculator can serve as a trustworthy, grounded first-line companion — pointing users toward evidence-based techniques and professional resources rather than improvising guidance.

### 1.3 Goals
- Deliver a single conversational interface where users can explore mental health techniques, coping strategies, and self-assessment tools in plain language.
- Ground every substantive response in either the local knowledge base (RAG) or live web search results — not LLM parametric memory alone.
- Demonstrate a production-quality agentic pattern: LangGraph orchestration, three distinct tools, and a streaming response pipeline.
- Serve as an educational reference implementation for tool-augmented LLM agents in a sensitive domain.

### 1.4 Ethical Guardrails
- The system prompt must clearly establish the agent's role as a psychoeducational tool, not a licensed therapist.
- Every conversation session must surface a persistent disclaimer visible in the UI.
- Any message that signals acute crisis (suicidal ideation, self-harm) must trigger an immediate, hardcoded response that provides crisis resources (988 Suicide & Crisis Lifeline, Crisis Text Line) regardless of the LLM's output.

---

## 2. Stakeholders

| Role | Name / Group | Responsibility |
|------|-------------|----------------|
| Product Owner | Course Instructor | Defines acceptance criteria |
| Developer | Student Team | Design, build, and deploy |
| End Users | Classmates / Graders | Chat with the agent and evaluate UX |

---

## 3. Scope

### 3.1 In Scope
- Conversational chat UI (web browser, single-page)
- Streaming LLM responses via Server-Sent Events (SSE)
- RAG tool: semantic search over a curated mental health knowledge base (Chroma + LangChain)
- Web search tool: live search results via the Tavily API
- Calculator tool: safe evaluation of mathematical expressions (e.g., PHQ-9 / GAD-7 scoring, sleep efficiency)
- LangGraph agent orchestration loop with multi-tool chaining
- In-session conversation history
- Crisis resource injection on detected distress signals
- Visible disclaimer and tool-use indicators in the UI

### 3.2 Out of Scope
- Diagnosis, clinical assessment, or treatment recommendations
- User authentication / accounts
- Persistent chat history across sessions
- Mobile-native applications
- Containerization / cloud deployment
- Fine-tuning or training a custom model
- Tool result caching or rate-limit handling beyond basic error messages

---

## 4. User Stories

| ID | As a... | I want to... | So that... |
|----|---------|-------------|------------|
| US-01 | User | Ask about coping strategies for anxiety | The agent retrieves specific, sourced techniques from the knowledge base |
| US-02 | User | Ask about current research on a mental health topic | The agent searches the web and summarizes credible results |
| US-03 | User | Enter my PHQ-9 answers and get my score interpreted | The agent uses the calculator and explains what the score means |
| US-04 | User | See the agent's response appear word-by-word | The interaction feels fast and conversational |
| US-05 | User | See which tool the agent used (RAG, web search, calculator) | I can evaluate the trustworthiness of the answer |
| US-06 | User | Ask a follow-up question in the same chat window | Context is maintained within the session |
| US-07 | User | Send a message by pressing Enter or clicking Send | The interaction is intuitive |
| US-08 | User | Receive crisis resources immediately if I express distress | I am pointed to professional help without delay |

---

## 5. Functional Requirements

### 5.1 Chat UI
| ID | Requirement |
|----|------------|
| FR-01 | The UI shall display a scrollable message history with distinct styling for user and agent messages. |
| FR-02 | The UI shall provide a text input field and a Submit button (Enter key also submits). |
| FR-03 | The UI shall stream agent tokens into the message bubble as they arrive. |
| FR-04 | The UI shall display a visible loading indicator while the agent is processing. |
| FR-05 | The UI shall show a labeled tool badge when a tool is invoked (e.g., "Knowledge Base", "Web Search", "Calculator"). |
| FR-06 | The UI shall display a persistent disclaimer: "This tool is not a substitute for professional mental health care." |
| FR-07 | The UI shall auto-scroll to the newest message. |

### 5.2 RAG Tool
| ID | Requirement |
|----|------------|
| FR-08 | The tool shall accept a natural-language query and return the most semantically relevant chunks from the knowledge base. |
| FR-09 | The knowledge base shall be built from curated documents covering: CBT techniques, DBT skills, mindfulness/MBSR exercises, grounding techniques, sleep hygiene (CBT-I), and crisis resources. |
| FR-10 | The tool shall use LangChain's document pipeline: `TextLoader`/`PyPDFLoader` → `RecursiveCharacterTextSplitter` → `OpenAIEmbeddings` → `Chroma`. |
| FR-11 | The tool shall return the top-k (default: 4) relevant chunks along with their source document name. |
| FR-12 | The knowledge base shall be built once via an ingest script and persisted to disk; it shall not be rebuilt on every server start. |

### 5.3 Web Search Tool
| ID | Requirement |
|----|------------|
| FR-13 | The tool shall accept a natural-language search query string. |
| FR-14 | The tool shall call the Tavily Search API and return a structured list of results (title, URL, snippet). |
| FR-15 | The tool shall handle API errors gracefully and return a user-readable error message. |
| FR-16 | The tool shall return at most 5 results per query to keep context window usage reasonable. |

### 5.4 Calculator Tool
| ID | Requirement |
|----|------------|
| FR-17 | The tool shall accept a string representing a mathematical expression. |
| FR-18 | The tool shall safely evaluate the expression using a math-safe parser (no raw `eval`). |
| FR-19 | The tool shall support: basic arithmetic (`+`, `-`, `*`, `/`), exponentiation, parentheses, and common functions (`sqrt`, `abs`, `round`, `sum`). |
| FR-20 | The tool shall return the numeric result or a descriptive error message if the expression is invalid. |
| FR-21 | The agent's system prompt shall instruct it to use the calculator for standardized scoring (e.g., PHQ-9, GAD-7, sleep efficiency percentage). |

### 5.5 Agent / Backend
| ID | Requirement |
|----|------------|
| FR-22 | The backend shall expose a streaming HTTP endpoint (`POST /chat`) that accepts conversation history and returns an SSE stream. |
| FR-23 | The agent shall be implemented as a LangGraph `StateGraph` with `call_model` and `tools` nodes and conditional edges. |
| FR-24 | The agent shall use `gpt-4o-mini` (or equivalent) with LangChain tool-calling integration. |
| FR-25 | The agent shall autonomously decide whether to call one or more tools, chain tools sequentially, or respond directly. |
| FR-26 | The agent shall stream tokens using LangGraph's `.astream_events()` API, forwarding `on_chat_model_stream` and `on_tool_start` events to the SSE stream. |
| FR-27 | The backend shall maintain in-memory conversation history per `session_id` for the duration of the server process. |
| FR-28 | The agent's system prompt shall establish its role, ethical limits, and instruct it to always cite the source tool used. |

---

## 6. Non-Functional Requirements

| ID | Category | Requirement |
|----|----------|------------|
| NFR-01 | Performance | First token shall appear within 3 seconds of submission under normal network conditions. |
| NFR-02 | Reliability | Tool errors must not crash the agent; errors shall be returned as structured messages and explained to the user. |
| NFR-03 | Safety | Crisis keyword detection shall be evaluated server-side before the LLM responds; a hardcoded crisis resource message shall be injected immediately. |
| NFR-04 | Security | No raw `eval` in the calculator. All API keys stored in environment variables and excluded from version control via `.gitignore`. |
| NFR-05 | Usability | The UI must be usable on a modern desktop browser (Chrome, Firefox, Edge) without additional plugins or build steps. |
| NFR-06 | Maintainability | Code must be organized into clearly separated modules: `tools/`, `agent/`, `api/`, `knowledge_base/`, `frontend/`. |
| NFR-07 | Transparency | Every agent response that uses a tool must include the tool name in the SSE event stream so the UI can display it. |

---

## 7. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Browser (Chat UI)                   │
│   - Message history                                      │
│   - Streaming token rendering                            │
│   - Tool-use badges (Knowledge Base / Web Search / Calc) │
│   - Persistent disclaimer banner                         │
└───────────────────────┬─────────────────────────────────┘
                        │  POST /chat  (SSE stream)
┌───────────────────────▼─────────────────────────────────┐
│                    FastAPI Backend                       │
│                                                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │            LangGraph StateGraph Agent             │  │
│  │                                                   │  │
│  │  [START] → [call_model] ──tool_call?──► [tools]  │  │
│  │                 ▲                          │      │  │
│  │                 └──────────────────────────┘      │  │
│  │                        │ no tool call             │  │
│  │                      [END] → stream tokens        │  │
│  └────────────┬───────────┬──────────────┬───────────┘  │
│               │           │              │               │
│  ┌────────────▼──┐ ┌──────▼──────┐ ┌────▼───────────┐  │
│  │   RAG Tool    │ │  Web Search │ │  Calculator    │  │
│  │  (Retriever)  │ │  (Tavily)   │ │  (simpleeval)  │  │
│  └────────────┬──┘ └─────────────┘ └────────────────┘  │
│               │                                          │
│  ┌────────────▼──────────────────────────────────────┐  │
│  │         LangChain + Chroma Vector Store           │  │
│  │         (persisted to disk at ingest time)        │  │
│  │                                                   │  │
│  │  knowledge_base/                                  │  │
│  │  ├── cbt_techniques.md                            │  │
│  │  ├── dbt_skills.md                                │  │
│  │  ├── mindfulness_exercises.md                     │  │
│  │  ├── grounding_techniques.md                      │  │
│  │  ├── sleep_hygiene.md                             │  │
│  │  └── crisis_resources.md                          │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 8. API Contracts

### 8.1 `POST /chat`
**Request Body:**
```json
{
  "message": "What are some grounding techniques for panic attacks?",
  "session_id": "abc123"
}
```

**Response:** Server-Sent Events stream. Each event is a JSON object on a `data:` line:
```json
{ "type": "tool_use",  "tool": "rag_search",  "input": "grounding techniques panic attacks" }
{ "type": "token",     "content": "Here are " }
{ "type": "token",     "content": "several grounding techniques..." }
{ "type": "done" }
```

**Error / crisis injection:**
```json
{ "type": "crisis",    "content": "It sounds like you may be in distress. Please reach out to the 988 Suicide & Crisis Lifeline by calling or texting 988." }
{ "type": "done" }
```

### 8.2 `GET /health`
```json
{ "status": "ok", "vector_store": "loaded" }
```

### 8.3 RAG Tool Schema
```json
{
  "name": "rag_search",
  "description": "Searches the mental health knowledge base for evidence-based techniques, coping strategies, and therapeutic frameworks. Use this before answering any question about mental health skills or practices.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "A natural-language query describing the technique or topic to retrieve."
      }
    },
    "required": ["query"]
  }
}
```

### 8.4 Web Search Tool Schema
```json
{
  "name": "web_search",
  "description": "Searches the web using Tavily for current research, news, or resources not covered in the knowledge base.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "The web search query." }
    },
    "required": ["query"]
  }
}
```

### 8.5 Calculator Tool Schema
```json
{
  "name": "calculator",
  "description": "Safely evaluates a mathematical expression. Use this to compute standardized assessment scores (PHQ-9, GAD-7), sleep efficiency percentages, or any numeric calculation.",
  "parameters": {
    "type": "object",
    "properties": {
      "expression": { "type": "string", "description": "A valid mathematical expression, e.g. '2+3+1+2+0+1+2' or '(360/480)*100'" }
    },
    "required": ["expression"]
  }
}
```

---

## 9. Assumptions & Dependencies

| # | Assumption / Dependency |
|---|------------------------|
| 1 | A valid `OPENAI_API_KEY` is available via environment variable. |
| 2 | A valid `TAVILY_API_KEY` is available via environment variable. |
| 3 | `gpt-4o-mini` supports LangChain tool-calling integration. |
| 4 | The knowledge base documents are authored or curated by the developer prior to the ingest step. |
| 5 | The application runs locally; no cloud deployment or containerization is required for the MVP. |
| 6 | Internet access is available at runtime for Tavily calls. |
| 7 | LangGraph `>=0.2` and LangChain `>=0.3` are used; older APIs are not targeted. |

---

## 10. Open Questions

| # | Question | Owner | Status |
|---|----------|-------|--------|
| 1 | Should the crisis keyword list be static (hardcoded) or LLM-evaluated? | Developer | Open |
| 2 | How extensive should the initial knowledge base be — 5 documents or 20+? | Developer | Open |
| 3 | Should tool invocation details be visible by default or behind an expand toggle? | Developer | Open |
| 4 | Should the RAG tool always be called first, or only when the LLM decides to? | Developer | Open |

---

## 11. Success Criteria

- A user can ask at least 5 mental health technique questions and receive responses grounded in the knowledge base (RAG tool invoked, source shown).
- A user can ask at least 3 questions requiring live information and receive web-search-grounded responses.
- A user can enter PHQ-9 or GAD-7 responses and receive a correct calculated score with interpretation.
- The agent correctly selects the appropriate tool (or no tool) for at least 90% of a defined test set.
- Streamed responses begin appearing within 3 seconds on a local network.
- A crisis-signal message triggers the hardcoded crisis resource response every time.
- No API keys are exposed in the frontend or committed to version control.
