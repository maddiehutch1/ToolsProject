# LangChain + OpenAI Guide
## Usage in This Project

**Source:** [LangChain Docs](https://python.langchain.com) — verified March 2026  
**Packages:** `langchain-openai>=0.2.0`, `langchain-core>=0.3.0`, `langchain-community>=0.3.0`, `langchain>=0.3.0`  
**Used in:** `backend/agent.py`, `backend/ingest.py`, `backend/tools/rag_search.py`

---

## Why langchain-openai

- `ChatOpenAI` provides the LLM interface for LangGraph nodes — supports tool calling and streaming out of the box
- `OpenAIEmbeddings` generates the vectors stored in FAISS — text-embedding-3-small is fast and cheap
- Both classes read `OPENAI_API_KEY` from environment automatically via `python-dotenv`

---

## Installation

```bash
pip install langchain-openai langchain-core langchain-community langchain
```

---

## Environment Setup

`langchain-openai` reads `OPENAI_API_KEY` automatically from the environment. Load it with `python-dotenv` at application startup:

```python
# backend/main.py (top of file, before any langchain imports that trigger API calls)
from dotenv import load_dotenv
load_dotenv()
```

Your `.env` file:
```
OPENAI_API_KEY=sk-...
```

---

## ChatOpenAI — LLM for the Agent

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gpt-4o-mini",
    streaming=True,       # required for token-by-token SSE output
    temperature=0.2,      # lower temperature = more consistent, evidence-based answers
)
```

### Binding Tools

Before wiring into LangGraph, bind the tools so the LLM knows their schemas:

```python
from backend.tools.rag_search import rag_search
from backend.tools.web_search import web_search
from backend.tools.calculator import calculator

llm_with_tools = llm.bind_tools([rag_search, web_search, calculator])
```

The LLM will then produce `AIMessage` objects with `.tool_calls` populated when it decides to use a tool. `ToolNode` handles dispatching those calls.

### Using in a LangGraph Node

```python
def call_model(state: AgentState) -> dict:
    messages = [SYSTEM_PROMPT] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}
```

### Key Parameters

| Parameter | Value Used | Notes |
|-----------|-----------|-------|
| `model` | `"gpt-4o-mini"` | Low cost, fast, strong tool-calling |
| `streaming` | `True` | Enables `on_chat_model_stream` events in LangGraph |
| `temperature` | `0.2` | More deterministic for factual / evidence-based responses |
| `max_tokens` | *(default)* | Override if responses are getting cut off |
| `api_key` | *(from env)* | Set explicitly only if managing multiple keys |

---

## OpenAIEmbeddings — Vectors for FAISS

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
```

`text-embedding-3-small` produces 1536-dimensional vectors. It is cost-effective and sufficient for the 6-document knowledge base.

### Usage in `ingest.py`

```python
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# Load all markdown files in knowledge_base/
loader = DirectoryLoader("knowledge_base/", glob="*.md", loader_cls=TextLoader)
documents = loader.load()

# Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)

# Embed and store
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = FAISS.from_documents(chunks, embeddings)
vectorstore.save_local("faiss_index")

print(f"Ingested {len(chunks)} chunks from {len(documents)} documents.")
```

### Usage in `rag_search.py` (loading at server startup)

```python
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True,  # required for loading .pkl files
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
```

---

## Document Loading and Splitting

### TextLoader + DirectoryLoader

```python
from langchain_community.document_loaders import TextLoader, DirectoryLoader

# Load a single file
doc = TextLoader("knowledge_base/cbt_techniques.md").load()

# Load all .md files in a folder
docs = DirectoryLoader(
    "knowledge_base/",
    glob="*.md",
    loader_cls=TextLoader,
    show_progress=True,
).load()
```

Each loaded document has:
- `page_content` — the text
- `metadata["source"]` — the file path (used for source attribution)

### RecursiveCharacterTextSplitter

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,     # ~125 words per chunk
    chunk_overlap=50,   # overlap reduces context loss at chunk boundaries
    separators=["\n\n", "\n", " ", ""],  # default priority
)
chunks = splitter.split_documents(docs)
```

`chunk_size=500, chunk_overlap=50` is the spec from `aiDocs/mvp.md`. Test retrieval quality early — if chunks are too small, important context will be split.

---

## @tool Decorator (langchain-core)

All three tools in this project use the `@tool` decorator from `langchain_core.tools`:

```python
from langchain_core.tools import tool

@tool
def rag_search(query: str) -> str:
    """Searches the mental health knowledge base for evidence-based techniques and guidance."""
    docs = retriever.invoke(query)
    results = [f"[{doc.metadata.get('source', 'unknown')}]\n{doc.page_content}" for doc in docs]
    return "\n\n---\n\n".join(results)
```

Rules for `@tool` functions:
- The **docstring** becomes the tool description shown to the LLM — be specific about when to call it
- The **function name** is the tool's `name` field — keep it short, snake_case
- The **type hints** define the tool's input schema — always annotate parameters
- Return a `str` — the LLM reads this as plain text

---

## Message Types

LangGraph passes `BaseMessage` subclasses through the graph. Know these:

```python
from langchain_core.messages import (
    SystemMessage,   # agent system prompt — prepended in call_model
    HumanMessage,    # user's input
    AIMessage,       # LLM response (may contain .tool_calls)
    ToolMessage,     # tool execution result (produced by ToolNode)
)
```

Constructing messages:
```python
history = [
    HumanMessage(content="What is CBT?"),
    AIMessage(content="CBT, or Cognitive Behavioral Therapy..."),
    HumanMessage(content="Can you give me an exercise?"),
]
```

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| `AuthenticationError` on startup | `load_dotenv()` must be called before any LangChain import that uses the API |
| `allow_dangerous_deserialization` warning | Pass `allow_dangerous_deserialization=True` to `FAISS.load_local` — required for `.pkl` files |
| Tool not being called | Check the `@tool` docstring — make it specific about when the tool is appropriate |
| Chunks too small / poor retrieval | Increase `chunk_size` or adjust `chunk_overlap`; test with direct `retriever.invoke()` calls |
| `text-embedding-3-small` dimension mismatch | If you change embedding models, delete and rebuild the FAISS index |
| `streaming=True` has no effect | Streaming requires `.astream_events()` on the LangGraph graph, not on the LLM directly |

---

## Key References

- [langchain-openai — ChatOpenAI](https://python.langchain.com/docs/integrations/chat/openai/)
- [langchain-openai — OpenAIEmbeddings](https://docs.langchain.com/oss/python/integrations/text_embedding/openai)
- [LangChain — Document Loaders](https://python.langchain.com/docs/how_to/#document-loaders)
- [LangChain — Text Splitters](https://python.langchain.com/docs/how_to/recursive_text_splitter/)
- [LangChain Core — @tool decorator](https://python.langchain.com/docs/how_to/custom_tools/)
