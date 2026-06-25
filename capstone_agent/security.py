"""Security module — PII detection, secret scanning, input sanitization.

This module contains all security detection logic as pure functions
(no side effects) so they can be tested independently of the agent
framework. Callbacks in callbacks.py call these functions and handle
the blocking/logging.

Security layers implemented (defense in depth from Day 2b):
1. Input filtering: block prompt injection before the LLM sees it
2. Output filtering: catch PII/secrets in LLM responses before the user sees them
3. Tool authorization: validate tool args before execution
4. Memory governance: strip PII before storing in long-term memory

All detection functions return structured results, not booleans,
so the caller can log exactly what was detected and why.
"""

import re
import unicodedata

from .config import redact_secrets

# --- Prompt injection patterns ---
# Expanded from 4 to 15+ patterns covering known attack categories.

INJECTION_PATTERNS: list[tuple[str, str]] = [
    (r"ignore\s+(all\s+)?(previous|prior|above|earlier)\s+instructions", "instruction_override"),
    (r"ignore\s+your\s+instructions", "instruction_override"),
    (r"disregard\s+(all\s+)?(previous|prior|your)\s+", "instruction_override"),
    (r"forget\s+(all\s+)?(previous|prior|your)\s+instructions", "instruction_override"),
    (r"(reveal|show|display|output|print)\s+(me\s+)?(your\s+)?(system\s+)?prompt", "prompt_extraction"),
    (r"what\s+(is|are)\s+your\s+(system\s+)?(instructions|prompt|rules)", "prompt_extraction"),
    (r"pretend\s+(you\s+are|to\s+be|you're)", "role_hijack"),
    (r"act\s+as\s+(if\s+you\s+are|a|an)", "role_hijack"),
    (r"you\s+are\s+now\s+(a|an|in)", "role_hijack"),
    (r"(enter|switch\s+to|enable)\s+(developer|debug|admin|root|god)\s+mode", "privilege_escalation"),
    (r"bypass\s+(your\s+)?(safety|security|filter|restriction|guardrail)", "bypass_attempt"),
    (r"override\s+(your\s+)?(safety|security|rules|instructions)", "bypass_attempt"),
    (r"\bDAN\b.*\bdo\s+anything\s+now\b", "jailbreak"),
    (r"jailbreak", "jailbreak"),
    (r"(do\s+not|don't)\s+(follow|obey|listen\s+to)\s+(your\s+)?(rules|instructions)", "bypass_attempt"),
    # Clinical / HIPAA bypass attempts
    (r"(ignore|disregard|bypass|disable)\s+(hipaa|privacy|audit|compliance|phi)\s+(requirement|restriction|check|protocol|rule)", "hipaa_bypass"),
    (r"(list|show|dump|export)\s+(all\s+)?patient\s+(names|records|data|identifiers)", "phi_extraction"),
    (r"(disable|turn\s+off|skip)\s+(pii|phi|redact|audit)\s+(filter|detection|logging|trail)", "safety_disable"),
]

_COMPILED_PATTERNS = [(re.compile(p, re.IGNORECASE), label) for p, label in INJECTION_PATTERNS]


# --- PII detection patterns ---

PII_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    ("email", "email address", re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")),
    ("phone", "phone number", re.compile(r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("ssn", "social security number", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("credit_card", "credit card number", re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")),
]

# --- Protected Health Information (PHI) detection patterns ---
# HIPAA identifiers beyond standard PII: medical record numbers,
# diagnosis codes, drug dosages, and provider identifiers.

PHI_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    ("medical_record_number", "medical record number",
     re.compile(r"\bMRN\s*[#:]?\s*\d{6,10}\b", re.IGNORECASE)),
    ("icd10_code", "ICD-10 diagnosis code",
     re.compile(r"\b[A-Z]\d{2}\.\d{1,4}\b")),
    ("npi_number", "provider NPI number",
     re.compile(r"\bNPI\s*[#:]?\s*\d{10}\b", re.IGNORECASE)),
    ("drug_dosage", "drug dosage",
     re.compile(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|mL|units|IU)\b", re.IGNORECASE)),
    ("dea_number", "DEA registration number",
     re.compile(r"\bDEA\s*[#:]?\s*[A-Z]{2}\d{7}\b", re.IGNORECASE)),
]

# --- Secret detection patterns ---

SECRET_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("api_key", re.compile(r"(?:api[_-]?key|apikey)\s*[:=]\s*['\"]?[\w\-]{20,}['\"]?", re.IGNORECASE)),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE)),
    ("password", re.compile(r"(?:password|passwd|pwd)\s*[:=]\s*['\"]?\S{6,}['\"]?", re.IGNORECASE)),
    ("private_key", re.compile(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----")),
    ("gcp_key", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("aws_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("generic_secret", re.compile(r"(?:secret|token|credential)\s*[:=]\s*['\"]?[\w\-]{16,}['\"]?", re.IGNORECASE)),
]


def is_blocked_input(text: str) -> tuple[bool, str]:
    """Check if text contains prompt injection patterns.

    Returns (is_blocked, reason). The reason string identifies
    the attack category for audit logging.
    """
    normalized = text.lower().strip()
    for pattern, label in _COMPILED_PATTERNS:
        if pattern.search(normalized):
            return True, label
    return False, ""


def detect_pii(text: str) -> list[dict[str, str]]:
    """Scan text for personally identifiable information.

    Returns a list of dicts with 'type', 'label', and 'match' keys.
    Empty list means no PII found.
    """
    findings = []
    for pii_type, label, pattern in PII_PATTERNS:
        for match in pattern.finditer(text):
            findings.append({
                "type": pii_type,
                "label": label,
                "match": match.group(),
            })
    return findings


def scan_for_secrets(text: str) -> list[dict[str, str]]:
    """Scan text for leaked secrets (API keys, tokens, passwords).

    Returns a list of dicts with 'type' and 'match' keys.
    The match value is redacted for safe logging.
    """
    findings = []
    for secret_type, pattern in SECRET_PATTERNS:
        for match in pattern.finditer(text):
            findings.append({
                "type": secret_type,
                "match": redact_secrets(match.group()),
            })
    return findings


def sanitize_input(text: str) -> str:
    """Clean user input: strip control characters, normalize unicode.

    Prevents homoglyph attacks (e.g., Cyrillic 'а' vs Latin 'a')
    and removes invisible/control characters that could confuse parsing.
    """
    # Normalize unicode to NFKC (compatibility decomposition + canonical composition)
    text = unicodedata.normalize("NFKC", text)

    # Remove control characters except newline and tab
    cleaned = []
    for char in text:
        category = unicodedata.category(char)
        if category.startswith("C") and char not in ("\n", "\t", "\r"):
            continue
        cleaned.append(char)

    return "".join(cleaned).strip()


def redact_pii(text: str) -> str:
    """Replace detected PII in text with [PII_REDACTED].

    Used by memory.py to strip PII before storing in long-term memory.
    """
    result = text
    for _, _, pattern in PII_PATTERNS:
        result = pattern.sub("[PII_REDACTED]", result)
    return result


def detect_phi(text: str) -> list[dict[str, str]]:
    """Scan text for Protected Health Information (HIPAA identifiers).

    Checks for both standard PII and clinical-specific PHI patterns
    including medical record numbers, diagnosis codes, drug dosages,
    and provider identifiers. Returns combined findings from both
    detect_pii() and PHI-specific patterns.
    """
    findings = detect_pii(text)
    for phi_type, label, pattern in PHI_PATTERNS:
        for match in pattern.finditer(text):
            findings.append({
                "type": phi_type,
                "label": label,
                "match": match.group(),
            })
    return findings


def redact_phi(text: str) -> str:
    """Replace detected PII and PHI in text with redaction markers.

    Applies both generic PII redaction and clinical PHI redaction.
    Used by memory governance to strip all protected identifiers
    before persisting to long-term memory or crossing A2A boundaries.
    """
    result = redact_pii(text)
    for _, _, pattern in PHI_PATTERNS:
        result = pattern.sub("[PHI_REDACTED]", result)
    return result
