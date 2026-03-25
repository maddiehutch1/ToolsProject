import json
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


async def mock_agent_stream_normal(messages):
    yield {"type": "token", "content": "Here is some help."}
    yield {"type": "done"}


async def mock_agent_stream_with_tool(messages):
    yield {"type": "tool_use", "tool": "rag_search"}
    yield {"type": "tool_done", "tool": "rag_search"}
    yield {"type": "token", "content": "CBT involves cognitive restructuring."}
    yield {"type": "done"}


async def mock_agent_stream_error(messages):
    raise RuntimeError("LLM unavailable")
    yield  # makes it an async generator


def parse_sse(response_text: str) -> list[dict]:
    events = []
    for line in response_text.splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


# --- Health ---

@pytest.mark.integration
def test_health_returns_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.integration
def test_health_has_vector_store_key():
    r = client.get("/health")
    assert "vector_store" in r.json()


# --- Normal chat ---

@pytest.mark.integration
def test_chat_normal_contains_token_and_done():
    with patch("backend.main.run_agent_stream", mock_agent_stream_normal):
        r = client.post("/chat", json={"message": "What is CBT?", "session_id": "s1"})
    events = parse_sse(r.text)
    types = [e["type"] for e in events]
    assert "token" in types
    assert types[-1] == "done"


# --- Tool event in stream ---

@pytest.mark.integration
def test_chat_stream_contains_tool_use_event():
    with patch("backend.main.run_agent_stream", mock_agent_stream_with_tool):
        r = client.post("/chat", json={"message": "What is CBT?", "session_id": "s6"})
    events = parse_sse(r.text)
    types = [e["type"] for e in events]
    assert "tool_use" in types
    assert "tool_done" in types


# --- Crisis ---

@pytest.mark.integration
def test_chat_crisis_contains_crisis_event_not_token():
    r = client.post("/chat", json={"message": "I want to kill myself", "session_id": "s2"})
    events = parse_sse(r.text)
    types = [e["type"] for e in events]
    assert "crisis" in types
    assert "token" not in types


# --- Session memory ---

@pytest.mark.integration
def test_session_memory_persists_across_turns():
    with patch("backend.main.run_agent_stream", mock_agent_stream_normal):
        client.post("/chat", json={"message": "Hello", "session_id": "s3"})
        from backend.main import session_store
        assert len(session_store["s3"]) >= 2  # HumanMessage + AIMessage


# --- Error handling ---

@pytest.mark.integration
def test_chat_agent_exception_returns_error_event():
    with patch("backend.main.run_agent_stream", mock_agent_stream_error):
        r = client.post("/chat", json={"message": "Hello", "session_id": "s4"})
    events = parse_sse(r.text)
    types = [e["type"] for e in events]
    assert "error" in types


# --- Validation ---

@pytest.mark.integration
def test_chat_missing_message_returns_422():
    r = client.post("/chat", json={"session_id": "s5"})
    assert r.status_code == 422
