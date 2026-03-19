# 2026-03-19 Phase 2 Plan — Knowledge Base & RAG Tool

---

> **Build only what the checklist requires. No abstractions until you need them twice.**
> If a file, class, or function isn't referenced by something else in this phase, it shouldn't exist yet.
> Do not add compatibility shims, base classes, config flags, or "just in case" error paths not listed here.

---

## `backend/ingest.py`
Run once to build the FAISS index. Requires `OPENAI_API_KEY` in `.env`.

```python
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os, glob

load_dotenv()

def ingest():
    paths = glob.glob("knowledge_base/*.md")
    docs = []
    for path in paths:
        docs.extend(TextLoader(path).load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local("faiss_index")
    print(f"Ingested {len(chunks)} chunks from {len(paths)} files.")

if __name__ == "__main__":
    ingest()
```

---

## `backend/tools/rag_search.py`
Loads the pre-built FAISS index and exposes a `@tool` for the agent.

```python
from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import tool
import os

load_dotenv()

_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
_vectorstore = FAISS.load_local(
    os.getenv("FAISS_INDEX_PATH", "faiss_index"),
    _embeddings,
    allow_dangerous_deserialization=True,
)
_retriever = _vectorstore.as_retriever(search_kwargs={"k": 4})

@tool
def rag_search(query: str) -> str:
    """Searches the mental health knowledge base for evidence-based techniques.
    Use for any question about CBT, DBT, mindfulness, grounding, sleep, or crisis resources."""
    docs = _retriever.invoke(query)
    if not docs:
        return "No relevant documents found."
    return "\n---\n".join(
        f"[{os.path.basename(doc.metadata.get('source', 'unknown'))}]\n{doc.page_content}"
        for doc in docs
    )
```

> If `faiss_index/` is missing, this module will raise on import. `GET /health` should catch this and report `"vector_store": "not_loaded"` — handled in Phase 6.

---

## `tests/test_rag_search.py`

```python
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

MOCK_DOCS = [
    Document(page_content="Cognitive restructuring helps reframe negative thoughts.", metadata={"source": "knowledge_base/cbt_techniques.md"}),
    Document(page_content="The 5-4-3-2-1 technique grounds you in the present.", metadata={"source": "knowledge_base/grounding_techniques.md"}),
]

@pytest.fixture(autouse=True)
def mock_faiss_load(monkeypatch):
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = MOCK_DOCS
    with patch("backend.tools.rag_search._retriever", mock_retriever):
        yield mock_retriever

@pytest.mark.unit
def test_returns_source_prefixed_chunks(mock_faiss_load):
    from backend.tools.rag_search import rag_search
    result = rag_search.invoke("coping strategies")
    assert "[cbt_techniques.md]" in result
    assert "Cognitive restructuring" in result

@pytest.mark.unit
def test_multiple_sources_in_output(mock_faiss_load):
    from backend.tools.rag_search import rag_search
    result = rag_search.invoke("grounding")
    assert "[grounding_techniques.md]" in result

@pytest.mark.unit
def test_empty_results_returns_fallback(mock_faiss_load):
    mock_faiss_load.invoke.return_value = []
    from backend.tools.rag_search import rag_search
    result = rag_search.invoke("unrelated topic")
    assert "No relevant documents found." in result
```

---

## Knowledge Base Documents
Each file must be substantive — no placeholder text. Minimum ~200 words per file covering real techniques. The agent cites these by filename, so names must exactly match those listed in `aiDocs/architecture.md §RAG Pipeline`.

| File | Core content to include |
|------|------------------------|
| `cbt_techniques.md` | Thought records, cognitive distortions, behavioral activation |
| `dbt_skills.md` | TIPP, ACCEPTS, DEAR MAN, PLEASE skills |
| `mindfulness_exercises.md` | Body scan, breath awareness, STOP technique |
| `grounding_techniques.md` | 5-4-3-2-1 senses, box breathing, cold water |
| `sleep_hygiene.md` | CBT-I, sleep restriction, sleep efficiency = time asleep / time in bed × 100 |
| `crisis_resources.md` | 988 Suicide & Crisis Lifeline, text HOME to 741741, NAMI, SAMHSA |

---

## Verify
```bash
# Build the index (requires OPENAI_API_KEY)
python backend/ingest.py

# Confirm index files exist
ls faiss_index/
# Expected: index.faiss  index.pkl

# Run unit tests (no API keys needed — retriever is mocked)
pytest -m unit -v
```
