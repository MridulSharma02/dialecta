import re
import bleach
from config import get_settings
from core.errors import ValidationError, InjectionDetectedError

settings = get_settings()

_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous|above|prior)\s+instructions?",
    r"system\s*prompt",
    r"you\s+are\s+now\s+(?:a\s+)?(?:different|new|another)",
    r"disregard\s+(?:all\s+)?(?:previous|above)",
    r"act\s+as\s+(?:if\s+you\s+(?:are|were)\s+)?(?:an?\s+)?(?:AI|assistant|gpt|claude)",
    r"jailbreak",
    r"DAN\s+mode",
    r"pretend\s+(?:you\s+(?:are|have\s+no))",
    r"\{\{.*?\}\}",
    r"<\|.*?\|>",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

PASSWORD_MIN_LENGTH = 8
TOPIC_MAX_LENGTH = settings.MAX_TOPIC_CHARS

VALID_PERSONAS = {"Policymaker", "Student", "Journalist", "Scientist", "General"}


def validate_email(email: str) -> str:
    email = email.strip().lower()
    if not _EMAIL_RE.match(email):
        raise ValidationError("Invalid email address")
    if len(email) > 254:
        raise ValidationError("Email address too long")
    return email


def validate_password(password: str) -> str:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValidationError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
    if len(password) > 128:
        raise ValidationError("Password too long")
    if not re.search(r"[A-Za-z]", password):
        raise ValidationError("Password must contain at least one letter")
    if not re.search(r"\d", password):
        raise ValidationError("Password must contain at least one digit")
    return password


def validate_debate_topic(topic: str) -> str:
    topic = bleach.clean(topic, tags=[], strip=True).strip()

    if not topic:
        raise ValidationError("Topic cannot be empty")

    if len(topic) > TOPIC_MAX_LENGTH:
        raise ValidationError(f"Topic must be {TOPIC_MAX_LENGTH} characters or fewer")

    if _INJECTION_RE.search(topic):
        raise InjectionDetectedError()

    return topic


def validate_persona(persona: str) -> str:
    if persona not in VALID_PERSONAS:
        raise ValidationError(f"Persona must be one of: {', '.join(sorted(VALID_PERSONAS))}")
    return persona