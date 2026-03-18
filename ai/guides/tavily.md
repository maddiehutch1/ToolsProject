# Tavily Guide
## Usage in This Project

**Source:** [Tavily Docs](https://docs.tavily.com/integrations/langchain) — verified March 2026  
**Package:** `langchain-tavily>=0.1.0`  
**Used in:** `backend/tools/web_search.py`

---

## Why Tavily

Tavily is LangChain's recommended search partner:
- `langchain-tavily` is the official, actively maintained integration package
- The older `langchain_community.tools.tavily_search.tool` is **deprecated** — use `langchain-tavily` instead
- Returns structured results (title, URL, snippet, relevance score) — easy to format for the LLM
- `TavilySearch` is directly usable as a LangChain `@tool`-compatible tool

---

## Installation

```bash
pip install langchain-tavily
```

---

## Environment Setup

Get an API key from [app.tavily.com](https://app.tavily.com/sign-in).

Add to `.env`:
```
TAVILY_API_KEY=tvly-...
```

`langchain-tavily` reads `TAVILY_API_KEY` from the environment automatically.

---

## Implementation: `web_search.py`

```python
# backend/tools/web_search.py
import os
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langchain_core.tools import tool

load_dotenv()

_tavily = TavilySearch(
    max_results=5,
    topic="general",
    search_depth="basic",
)

@tool
def web_search(query: str) -> str:
    """Searches the web for current, factual information not available in the local \
knowledge base. Use for news, recent research, specific statistics, or any information \
that may have changed recently."""
    try:
        result = _tavily.invoke({"query": query})
        if not result or "results" not in result:
            return "No web results found."
        lines = []
        for item in result["results"]:
            lines.append(f"**{item['title']}**")
            lines.append(f"URL: {item['url']}")
            lines.append(item.get("content", ""))
            lines.append("")
        return "\n".join(lines)
    except Exception as e:
        return f"Web search failed: {str(e)}"
```

---

## TavilySearch Parameters

```python
from langchain_tavily import TavilySearch

tool = TavilySearch(
    max_results=5,              # number of results to return (default: 5)
    topic="general",            # "general" | "news" | "finance"
    search_depth="basic",       # "basic" (fast) | "advanced" (slower, more thorough)
    include_answer=False,       # include a direct answer (cannot change at invocation)
    include_raw_content=False,  # include full HTML (cannot change at invocation)
    include_images=False,       # include image URLs
    time_range=None,            # "day" | "week" | "month" | "year"
    include_domains=None,       # list of domains to restrict to
    exclude_domains=None,       # list of domains to exclude
)
```

> **Note:** `include_answer` and `include_raw_content` are fixed at instantiation and cannot be changed per-invocation (to prevent context window overflows).

---

## Response Format

`TavilySearch.invoke({"query": "..."})` returns a dict:

```python
{
    "query": "what is CBT therapy",
    "follow_up_questions": None,
    "answer": None,
    "images": [],
    "results": [
        {
            "url": "https://www.apa.org/ptsd-guideline/patients-and-families/cognitive-behavioral",
            "title": "What is Cognitive Behavioral Therapy?",
            "content": "Cognitive behavioral therapy (CBT) is a form of psychological...",
            "score": 0.87,
            "raw_content": None,
        },
        # ... up to max_results
    ],
    "response_time": 1.4
}
```

Access results with `result["results"]`, each item having `title`, `url`, `content`, and `score`.

---

## Direct Invocation (without @tool wrapper)

If you need to call Tavily outside the agent loop:

```python
from langchain_tavily import TavilySearch

search = TavilySearch(max_results=3)
result = search.invoke({"query": "mindfulness research 2025"})
for r in result["results"]:
    print(r["title"], r["url"])
```

---

## Using with LangGraph (as a standalone tool)

`TavilySearch` itself is already a LangChain tool. You can pass it directly to `ToolNode` without a `@tool` wrapper if you prefer:

```python
from langchain_tavily import TavilySearch

tavily_tool = TavilySearch(max_results=5)
tool_node = ToolNode([rag_search, tavily_tool, calculator])
```

However, wrapping it in a custom `@tool` function (as shown in the implementation above) gives you control over the output format and error handling.

---

## Testing with Mocked Responses

For unit tests, mock the Tavily API to avoid real network calls and quota consumption:

```python
# tests/test_web_search.py
from unittest.mock import patch, MagicMock
from backend.tools.web_search import web_search

MOCK_RESULT = {
    "results": [
        {
            "title": "What is CBT?",
            "url": "https://example.com/cbt",
            "content": "Cognitive Behavioral Therapy is a structured therapy...",
            "score": 0.9,
        }
    ]
}

def test_web_search_returns_formatted_result():
    with patch("backend.tools.web_search._tavily") as mock_tavily:
        mock_tavily.invoke.return_value = MOCK_RESULT
        result = web_search.invoke({"query": "what is CBT"})
    assert "What is CBT?" in result
    assert "https://example.com/cbt" in result

def test_web_search_handles_api_error():
    with patch("backend.tools.web_search._tavily") as mock_tavily:
        mock_tavily.invoke.side_effect = Exception("API quota exceeded")
        result = web_search.invoke({"query": "test query"})
    assert "Web search failed" in result
```

---

## Rate Limits and Quotas

- Free tier: 1,000 API credits/month
- Each `TavilySearch` invocation costs approximately 1 credit
- For this MVP, credits are consumed only during live E2E tests — unit tests should always be mocked
- If quota is exceeded, the `except Exception` block in the tool returns a graceful error string rather than crashing the agent

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| `TAVILY_API_KEY` not found | Ensure `load_dotenv()` is called before the tool module is imported |
| Using deprecated `langchain_community.tools.tavily_search` | Migrate to `from langchain_tavily import TavilySearch` |
| Result is empty dict / missing `"results"` key | Add a guard: `if not result or "results" not in result` |
| Unit tests hit the real API | Always patch `_tavily` or `TavilySearch.invoke` in tests |
| `include_answer` causes context overflow | Leave it `False` at instantiation — the agent synthesizes its own answer |

---

## Key References

- [langchain-tavily — LangChain Integration Docs](https://docs.tavily.com/integrations/langchain)
- [Tavily Python SDK Reference](https://docs.tavily.com/sdk/python/reference)
- [PyPI — langchain-tavily](https://pypi.org/project/langchain-tavily/)
- [GitHub — tavily-ai/langchain-tavily](https://github.com/tavily-ai/langchain-tavily)
