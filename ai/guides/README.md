# Package Guides
## Mental Health Companion — Implementation References

All guides are sourced from official documentation, verified March 2026.  
Each guide covers only the patterns and APIs used in this specific project.

---

## Index

| Guide | Package | Used In | Purpose |
|-------|---------|---------|---------|
| [fastapi.md](./fastapi.md) | `fastapi`, `uvicorn` | `backend/main.py` | SSE streaming, static file mount, Pydantic models, session store |
| [langgraph.md](./langgraph.md) | `langgraph` | `backend/agent.py` | `StateGraph`, `ToolNode`, `.astream_events()`, conditional edges |
| [langchain-openai.md](./langchain-openai.md) | `langchain-openai`, `langchain-core`, `langchain-community` | `backend/agent.py`, `backend/ingest.py`, `backend/tools/rag_search.py` | `ChatOpenAI`, `OpenAIEmbeddings`, `@tool`, document loaders, text splitter |
| [faiss.md](./faiss.md) | `faiss-cpu`, `langchain-community` | `backend/ingest.py`, `backend/tools/rag_search.py` | Build/load FAISS index, retriever, source attribution |
| [tavily.md](./tavily.md) | `langchain-tavily` | `backend/tools/web_search.py` | `TavilySearch` tool, response format, mocking for tests |
| [simpleeval.md](./simpleeval.md) | `simpleeval` | `backend/tools/calculator.py` | Safe expression evaluation, PHQ-9/GAD-7 scoring, error handling |
| [python-dotenv.md](./python-dotenv.md) | `python-dotenv` | `backend/main.py`, `backend/ingest.py` | `.env` loading, env var access, test fixtures |

---

## Build Order

Read guides in this order when implementing the project:

1. **python-dotenv** — set up env vars first, everything else needs API keys
2. **fastapi** — scaffold the server before building logic
3. **langchain-openai** — understand `@tool`, `ChatOpenAI`, and document loading
4. **faiss** — build the ingest script and RAG tool
5. **tavily** — implement web search tool
6. **simpleeval** — implement calculator tool
7. **langgraph** — wire all tools into the agent graph

This matches the phase order in [`../roadmaps/mvp-roadmap.md`](../roadmaps/mvp-roadmap.md).
