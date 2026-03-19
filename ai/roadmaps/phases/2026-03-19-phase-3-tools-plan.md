# 2026-03-19 Phase 3 Plan — Web Search & Calculator Tools

---

> **Build only what the checklist requires. No abstractions until you need them twice.**
> If a file, class, or function isn't referenced by something else in this phase, it shouldn't exist yet.
> Do not add compatibility shims, base classes, config flags, or "just in case" error paths not listed here.

---

## `backend/tools/web_search.py`
Wraps `TavilySearch` in a `@tool`. Requires `TAVILY_API_KEY` in `.env`.

```python
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langchain_core.tools import tool

load_dotenv()

_search = TavilySearch(max_results=5)

@tool
def web_search(query: str) -> str:
    """Searches the web for current information not in the knowledge base."""
    try:
        results = _search.invoke(query)
        if not results:
            return "No results found."
        lines = []
        for r in results:
            lines.append(f"Title: {r.get('title', 'N/A')}\nURL: {r.get('url', 'N/A')}\n{r.get('content', '')}")
        return "\n\n".join(lines)
    except Exception as e:
        return f"Web search failed: {e}"
```

---

## `tests/test_web_search.py`

```python
import pytest
from unittest.mock import MagicMock, patch

MOCK_RESULTS = [
    {"title": "What is CBT?", "url": "https://example.com/cbt", "content": "CBT is a form of therapy..."},
    {"title": "Mindfulness research", "url": "https://example.com/mindfulness", "content": "Recent studies show..."},
]

@pytest.fixture(autouse=True)
def mock_tavily(monkeypatch):
    with patch("backend.tools.web_search._search") as mock:
        mock.invoke.return_value = MOCK_RESULTS
        yield mock

@pytest.mark.unit
def test_output_contains_title_and_url(mock_tavily):
    from backend.tools.web_search import web_search
    result = web_search.invoke("cognitive behavioral therapy")
    assert "What is CBT?" in result
    assert "https://example.com/cbt" in result

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
```

---

## `backend/tools/calculator.py`
Uses `simpleeval` for safe expression evaluation — no raw `eval`.

```python
from langchain_core.tools import tool
from simpleeval import simple_eval, EvalWithCompoundTypes
import math

_FUNCTIONS = {
    "sqrt": math.sqrt,
    "abs": abs,
    "round": round,
    "pow": pow,
    "floor": math.floor,
    "ceil": math.ceil,
}

@tool
def calculator(expression: str) -> str:
    """Evaluates a math expression safely.
    Use for PHQ-9, GAD-7, sleep efficiency, or any arithmetic."""
    try:
        result = simple_eval(expression, functions=_FUNCTIONS)
        return str(result)
    except ZeroDivisionError:
        return "Error: division by zero."
    except Exception as e:
        return f"Error: {e}"
```

---

## `tests/test_calculator.py`

```python
import pytest
from backend.tools.calculator import calculator

@pytest.mark.unit
def test_basic_addition():
    assert calculator.invoke("2 + 3") == "5"

@pytest.mark.unit
def test_basic_multiplication():
    assert calculator.invoke("6 * 7") == "42"

@pytest.mark.unit
def test_phq9_sum():
    # PHQ-9 example: sum of 9 item scores
    assert calculator.invoke("2+3+1+0+2+1+3+2+1") == "15"

@pytest.mark.unit
def test_gad7_sum():
    # GAD-7 example: sum of 7 item scores
    assert calculator.invoke("1+2+3+1+2+1+2") == "12"

@pytest.mark.unit
def test_sqrt():
    assert calculator.invoke("sqrt(144)") == "12.0"

@pytest.mark.unit
def test_zero_division():
    result = calculator.invoke("1 / 0")
    assert "division by zero" in result.lower()

@pytest.mark.unit
def test_invalid_syntax():
    result = calculator.invoke("not a number !!!")
    assert "Error" in result

@pytest.mark.unit
def test_import_attempt_blocked():
    result = calculator.invoke("__import__('os').system('ls')")
    assert "Error" in result
```

---

## Verify
```bash
# Run all unit tests — no API keys needed
pytest -m unit -v

# Expected output:
# tests/test_calculator.py::test_basic_addition PASSED
# tests/test_calculator.py::test_phq9_sum PASSED
# ... (8 total)
# tests/test_web_search.py::test_output_contains_title_and_url PASSED
# ... (3 total)
# tests/test_rag_search.py::* PASSED  (no regressions)
```
