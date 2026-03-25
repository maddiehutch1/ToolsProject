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


@pytest.mark.unit
def test_detects_hurt_myself():
    assert detect_crisis("I've been thinking about hurting myself") is True


@pytest.mark.unit
def test_detects_dont_want_to_be_here():
    assert detect_crisis("I don't want to be here anymore") is True


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


@pytest.mark.unit
def test_no_crisis_for_depression_mention():
    assert detect_crisis("I've been feeling really depressed lately") is False


@pytest.mark.unit
def test_no_crisis_for_stress():
    assert detect_crisis("work has been really stressful") is False


# --- CRISIS_RESPONSE content ---

@pytest.mark.unit
def test_crisis_response_contains_988():
    assert "988" in CRISIS_RESPONSE


@pytest.mark.unit
def test_crisis_response_contains_crisis_text_line():
    assert "741741" in CRISIS_RESPONSE
