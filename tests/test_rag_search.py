import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

MOCK_DOCS = [
    Document(
        page_content="Cognitive restructuring helps reframe negative thoughts.",
        metadata={"source": "knowledge_base/cbt_techniques.md"},
    ),
    Document(
        page_content="The 5-4-3-2-1 technique grounds you in the present.",
        metadata={"source": "knowledge_base/grounding_techniques.md"},
    ),
]


@pytest.fixture(autouse=True)
def mock_faiss_load(monkeypatch):
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = MOCK_DOCS
    with patch("backend.tools.rag_search.retriever", mock_retriever):
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


@pytest.mark.unit
def test_chunks_separated_by_divider(mock_faiss_load):
    from backend.tools.rag_search import rag_search
    result = rag_search.invoke("coping strategies")
    assert "---" in result
