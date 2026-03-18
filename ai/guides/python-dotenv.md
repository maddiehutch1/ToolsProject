# python-dotenv Guide
## Usage in This Project

**Source:** [python-dotenv GitHub](https://github.com/theskumar/python-dotenv) — verified March 2026  
**Package:** `python-dotenv>=1.0.0`  
**Used in:** `backend/main.py`, `backend/ingest.py`, and any module that needs env vars at import time

---

## Why python-dotenv

All API keys (`OPENAI_API_KEY`, `TAVILY_API_KEY`) live in a `.env` file that is never committed to version control. `python-dotenv` loads that file into `os.environ` at runtime so every library that reads environment variables (LangChain, OpenAI SDK, Tavily) finds them automatically.

---

## Installation

```bash
pip install python-dotenv
```

---

## Usage

### Basic Pattern

Call `load_dotenv()` once, as early as possible in your entry point — before any import that triggers an API call:

```python
# backend/main.py  (top of file)
from dotenv import load_dotenv
load_dotenv()

# Now these work without passing the key explicitly:
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_tavily import TavilySearch
```

### In `ingest.py`

```python
# backend/ingest.py
from dotenv import load_dotenv
load_dotenv()

import os
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "faiss_index")
```

### Reading Variables

```python
import os

openai_key = os.getenv("OPENAI_API_KEY")           # None if not set
port = int(os.getenv("PORT", "8000"))              # with default
faiss_path = os.getenv("FAISS_INDEX_PATH", "faiss_index")
```

---

## The `.env` File

Create this file in the project root (never commit it):

```bash
# .env
OPENAI_API_KEY=sk-proj-...
TAVILY_API_KEY=tvly-...
PORT=8000
FAISS_INDEX_PATH=faiss_index
```

### `.env.example`

Commit a `.env.example` template (no real values) so collaborators know which variables to set:

```bash
# .env.example
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
PORT=8000
FAISS_INDEX_PATH=faiss_index
```

---

## `.gitignore` Entry

Ensure `.env` is never tracked:

```gitignore
.env
*.env
```

Verify with:
```bash
git status
# .env should NOT appear in untracked files
```

---

## `load_dotenv()` Behavior

| Scenario | Behavior |
|----------|---------|
| `.env` file exists | Variables loaded into `os.environ` |
| `.env` file missing | No error raised — silently does nothing |
| Variable already set in environment | **Not overwritten** (existing env takes precedence) |
| Duplicate key in `.env` | Last occurrence wins |

To force `.env` values to override existing environment variables:
```python
load_dotenv(override=True)
```

For this project, the default behavior (env takes precedence) is correct — it allows CI/CD or hosting platforms to inject real keys without a `.env` file.

---

## `dotenv_values` (read without setting env)

If you need the values as a dict without mutating `os.environ`:

```python
from dotenv import dotenv_values

config = dotenv_values(".env")
api_key = config.get("OPENAI_API_KEY")
```

This is useful in tests where you don't want to pollute the global environment.

---

## Testing with Environment Variables

For unit tests, set env vars directly rather than relying on a `.env` file:

```python
# tests/conftest.py
import os
import pytest

@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-not-real")
    monkeypatch.setenv("TAVILY_API_KEY", "test-key-not-real")
    monkeypatch.setenv("FAISS_INDEX_PATH", "tests/fixtures/faiss_index")
```

`pytest`'s `monkeypatch.setenv` is scoped to the test and automatically reverted after each test, so there are no side effects between tests.

---

## Common Pitfalls

| Pitfall | Fix |
|---------|-----|
| `AuthenticationError` despite `.env` existing | `load_dotenv()` called too late — move it to the top of the entry-point file, before LangChain imports |
| `.env` committed to git by accident | Add `.env` to `.gitignore` before the first commit; if already tracked, use `git rm --cached .env` |
| Variable is `None` at runtime | Check the `.env` file is in the project root (same directory as where you run `uvicorn`) |
| Works locally, fails in production | Production hosts (Render, Railway, etc.) inject env vars natively — no `.env` file needed there |
| `load_dotenv` in every file | Only call it once in the entry point (`main.py`, `ingest.py`); all submodules share the same `os.environ` |

---

## Key References

- [python-dotenv GitHub](https://github.com/theskumar/python-dotenv)
- [python-dotenv PyPI](https://pypi.org/project/python-dotenv/)
