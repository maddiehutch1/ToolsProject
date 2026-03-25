CRISIS_KEYWORDS = [
    "want to die",
    "end my life",
    "kill myself",
    "self-harm",
    "suicidal",
    "hurt myself",
    "hurting myself",
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
