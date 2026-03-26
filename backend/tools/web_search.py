from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langchain_core.tools import tool

load_dotenv()

_tavily = TavilySearch(max_results=5)


@tool
def web_search(query: str) -> str:
    """Searches the web for current information not in the knowledge base.
    Use for recent research, news, or anything requiring up-to-date information."""
    try:
        raw = _tavily.invoke(query)
        # v0.2.x returns a dict {"results": [...], ...}; v0.1.x returned a list
        items = raw.get("results", raw) if isinstance(raw, dict) else raw
        if not items:
            return "No results found."
        lines = []
        for r in items:
            lines.append(
                f"Title: {r.get('title', 'N/A')}\nURL: {r.get('url', 'N/A')}\n{r.get('content', '')}"
            )
        return "\n\n".join(lines)
    except Exception as e:
        return f"Web search failed: {e}"
