import pytest
from unittest.mock import patch

MOCK_RESULTS = [
    {"title": "What is CBT?", "url": "https://example.com/cbt", "content": "CBT is a form of therapy..."},
    {"title": "Mindfulness research", "url": "https://example.com/mindfulness", "content": "Recent studies show..."},
]


@pytest.fixture(autouse=True)
def mock_tavily(monkeypatch):
    with patch("backend.tools.web_search._tavily") as mock:
        mock.invoke.return_value = MOCK_RESULTS
        yield mock


@pytest.mark.unit
def test_output_contains_title_and_url(mock_tavily):
    from backend.tools.web_search import web_search
    result = web_search.invoke("cognitive behavioral therapy")
    assert "What is CBT?" in result
    assert "https://example.com/cbt" in result


@pytest.mark.unit
def test_all_results_present_in_output(mock_tavily):
    from backend.tools.web_search import web_search
    result = web_search.invoke("mindfulness")
    assert "Mindfulness research" in result
    assert "https://example.com/mindfulness" in result


@pytest.mark.unit
def test_empty_results_returns_fallback(mock_tavily):
    mock_tavily.invoke.return_value = []
    from backend.tools.web_search import web_search
    result = web_search.invoke("obscure query")
    assert "No results found." in result


@pytest.mark.unit
def test_api_error_returns_graceful_string(mock_tavily):
    mock_tavily.invoke.side_effect = Exception("API timeout")
    from backend.tools.web_search import web_search
    result = web_search.invoke("anything")
    assert "Web search failed" in result
