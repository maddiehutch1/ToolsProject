from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import tool
import os

load_dotenv()

_vectorstore = None
retriever = None

try:
    _embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    _vectorstore = FAISS.load_local(
        os.getenv("FAISS_INDEX_PATH", "faiss_index"),
        _embeddings,
        allow_dangerous_deserialization=True,
    )
    retriever = _vectorstore.as_retriever(search_kwargs={"k": 4})
except Exception:
    pass  # retriever stays None; health check reports "not_loaded"


@tool
def rag_search(query: str) -> str:
    """Searches the mental health knowledge base for evidence-based techniques.
    Use for any question about CBT, DBT, mindfulness, grounding, sleep, or crisis resources."""
    if retriever is None:
        return "Knowledge base unavailable."
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant documents found."
    return "\n---\n".join(
        f"[{os.path.basename(doc.metadata.get('source', 'unknown'))}]\n{doc.page_content}"
        for doc in docs
    )
