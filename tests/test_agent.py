import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage, HumanMessage


def make_tool_call_message(tool_name: str):
    args = {"expression": "2+3"} if tool_name == "calculator" else {"query": "test"}
    return AIMessage(
        content="",
        tool_calls=[{"name": tool_name, "args": args, "id": "call_1"}],
    )


def make_direct_message(content: str):
    return AIMessage(content=content)


@pytest.fixture(autouse=True)
def mock_llm():
    with patch("backend.agent._llm_with_tools") as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_tool_internals():
    """Prevent tool functions from making real API calls during integration tests."""
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = []
    mock_tavily = MagicMock()
    mock_tavily.invoke.return_value = []
    with patch("backend.tools.rag_search.retriever", mock_retriever), \
         patch("backend.tools.web_search._tavily", mock_tavily):
        yield


@pytest.mark.integration
def test_routes_to_rag_search_for_mental_health_query(mock_llm):
    mock_llm.invoke.side_effect = [
        make_tool_call_message("rag_search"),
        make_direct_message("CBT stands for Cognitive Behavioral Therapy."),
    ]
    from backend.agent import graph
    result = graph.invoke({"messages": [HumanMessage(content="What is CBT?")]})
    tool_names = [
        tc["name"]
        for msg in result["messages"]
        if hasattr(msg, "tool_calls")
        for tc in (msg.tool_calls or [])
    ]
    assert "rag_search" in tool_names


@pytest.mark.integration
def test_routes_to_calculator_for_math(mock_llm):
    mock_llm.invoke.side_effect = [
        make_tool_call_message("calculator"),
        make_direct_message("Your PHQ-9 score is 15."),
    ]
    from backend.agent import graph
    result = graph.invoke({"messages": [HumanMessage(content="Score my PHQ-9: 2+3+1+0+2+1+3+2+1")]})
    tool_names = [
        tc["name"]
        for msg in result["messages"]
        if hasattr(msg, "tool_calls")
        for tc in (msg.tool_calls or [])
    ]
    assert "calculator" in tool_names


@pytest.mark.integration
def test_routes_to_web_search_for_current_events(mock_llm):
    mock_llm.invoke.side_effect = [
        make_tool_call_message("web_search"),
        make_direct_message("Recent research shows mindfulness reduces anxiety."),
    ]
    from backend.agent import graph
    result = graph.invoke({"messages": [HumanMessage(content="What is the latest research on CBT?")]})
    tool_names = [
        tc["name"]
        for msg in result["messages"]
        if hasattr(msg, "tool_calls")
        for tc in (msg.tool_calls or [])
    ]
    assert "web_search" in tool_names


@pytest.mark.integration
def test_direct_answer_when_no_tool_needed(mock_llm):
    mock_llm.invoke.return_value = make_direct_message("I'm here to help.")
    from backend.agent import graph
    result = graph.invoke({"messages": [HumanMessage(content="Hello")]})
    last = result["messages"][-1]
    assert last.content == "I'm here to help."


@pytest.mark.integration
async def test_run_agent_stream_yields_token_and_done(mock_llm):
    from backend.agent import run_agent_stream

    async def fake_astream_events(state, version):
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="Hello")}, "name": ""}
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content=" there")}, "name": ""}

    with patch("backend.agent.graph.astream_events", fake_astream_events):
        events = [e async for e in run_agent_stream([HumanMessage(content="hi")])]

    types = [e["type"] for e in events]
    assert "token" in types
    assert types[-1] == "done"


@pytest.mark.integration
async def test_run_agent_stream_yields_tool_events(mock_llm):
    from backend.agent import run_agent_stream

    async def fake_astream_events(state, version):
        yield {"event": "on_tool_start", "name": "rag_search", "data": {}}
        yield {"event": "on_tool_end", "name": "rag_search", "data": {}}
        yield {"event": "on_chat_model_stream", "data": {"chunk": MagicMock(content="Here is info.")}, "name": ""}

    with patch("backend.agent.graph.astream_events", fake_astream_events):
        events = [e async for e in run_agent_stream([HumanMessage(content="What is CBT?")])]

    types = [e["type"] for e in events]
    assert "tool_use" in types
    assert "tool_done" in types
