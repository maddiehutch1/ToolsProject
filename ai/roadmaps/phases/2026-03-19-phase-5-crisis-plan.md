# 2026-03-19 Phase 5 Plan — Crisis Detection & System Prompt

---

> **Build only what the checklist requires. No abstractions until you need them twice.**
> If a file, class, or function isn't referenced by something else in this phase, it shouldn't exist yet.
> Do not add compatibility shims, base classes, config flags, or "just in case" error paths not listed here.

---

## `backend/crisis.py`
Pure Python — no imports beyond the standard library. The gate must never call the LLM.

```python
CRISIS_KEYWORDS = [
    "want to die",
    "end my life",
    "kill myself",
    "self-harm",
    "suicidal",
    "hurt myself",
    "don't want to be here",
]

CRISIS_RESPONSE = (
    "It sounds like you may be going through something very difficult. "
    "Please reach out to one of these free, confidential resources:\n\n"
    "• 988 Suicide & Crisis Lifeline — call or text 988\n"
    "• Crisis Text Line — text HOME to 741741\n"
    "• NAMI Helpline — 1-800-950-6264\n"
    "• SAMHSA National Helpline — 1-800-662-4357\n\n"
    "You are not alone, and help is available right now."
)

def detect_crisis(message: str) -> bool:
    lowered = message.lower()
    return any(keyword in lowered for keyword in CRISIS_KEYWORDS)
```

---

## `backend/agent.py` — system prompt addition
Add `SYSTEM_PROMPT` and prepend it inside `run_agent_stream`. No other changes to the graph.

```python
# Add near the top of backend/agent.py, after imports

SYSTEM_PROMPT = (
    "You are a psychoeducational mental health companion. "
    "You are NOT a therapist and do not provide diagnosis or treatment.\n\n"
    "Guidelines:\n"
    "- For questions about mental health techniques (CBT, DBT, mindfulness, grounding, sleep), "
    "always use the rag_search tool and cite the source document by name.\n"
    "- For current research or information not in the knowledge base, use web_search.\n"
    "- For PHQ-9, GAD-7, or any arithmetic, use the calculator tool.\n"
    "- Always state which tool you used and cite your source.\n"
    "- Maintain a warm, non-judgmental, evidence-based tone at all times."
)
```

Update `run_agent_stream` to prepend the system message:

```python
async def run_agent_stream(messages: list[BaseMessage]):
    state = {"messages": [SystemMessage(content=SYSTEM_PROMPT)] + messages}
    async for event in graph.astream_events(state, version="v2"):
        ...  # unchanged
```

---

## `tests/test_crisis.py`

```python
import pytest
from backend.crisis import detect_crisis, CRISIS_RESPONSE

# --- True cases ---

@pytest.mark.unit
def test_detects_want_to_die():
    assert detect_crisis("I want to die") is True

@pytest.mark.unit
def test_detects_kill_myself():
    assert detect_crisis("I want to kill myself") is True

@pytest.mark.unit
def test_detects_suicidal():
    assert detect_crisis("I've been feeling suicidal lately") is True

@pytest.mark.unit
def test_detects_self_harm():
    assert detect_crisis("I've been doing self-harm") is True

@pytest.mark.unit
def test_detects_mixed_case():
    assert detect_crisis("I WANT TO DIE") is True

@pytest.mark.unit
def test_detects_keyword_mid_sentence():
    assert detect_crisis("Sometimes I feel like I want to end my life") is True

# --- False cases ---

@pytest.mark.unit
def test_no_crisis_for_anxiety():
    assert detect_crisis("I've been feeling really anxious") is False

@pytest.mark.unit
def test_no_crisis_for_sleep_question():
    assert detect_crisis("help me sleep better") is False

@pytest.mark.unit
def test_no_crisis_for_cbt_question():
    assert detect_crisis("what is CBT?") is False

@pytest.mark.unit
def test_no_crisis_for_greeting():
    assert detect_crisis("hello, I need some help") is False

# --- CRISIS_RESPONSE content ---

@pytest.mark.unit
def test_crisis_response_contains_988():
    assert "988" in CRISIS_RESPONSE

@pytest.mark.unit
def test_crisis_response_contains_crisis_text_line():
    assert "741741" in CRISIS_RESPONSE
```

---

## Verify
```bash
pytest -m unit -v
# Expected: 12 tests in test_crisis.py pass
# All prior unit tests still green

# Quick manual check — confirm gate fires correctly
python -c "
from backend.crisis import detect_crisis, CRISIS_RESPONSE
print(detect_crisis('I want to die'))       # True
print(detect_crisis('I feel anxious'))      # False
print(CRISIS_RESPONSE[:80])
"
```
