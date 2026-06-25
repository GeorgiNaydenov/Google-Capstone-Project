"""Centralized configuration and secret management.

All runtime configuration loads from environment variables via .env.
No secrets are ever hardcoded. This module provides typed access,
validation, and utility functions used across the harness.

Design decisions:
- get_config() is cached so repeated calls don't re-read the environment.
- redact_secrets() is applied to all log output to prevent accidental leaks.
- deterministic_json() produces cache-friendly serialization (sorted keys,
  compact separators) improving KV-cache hit rates in repeated contexts.
"""

import json
import os
import re
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

# Patterns that indicate a secret value in text (key=value or key: value).
# Used by redact_secrets() to sanitize log output and error messages.
REDACT_PATTERNS = re.compile(
    r"(api[_-]?key|secret|password|token|auth[_-]?token|credential|private[_-]?key"
    r"|access[_-]?key|client[_-]?secret)"
    r"\s*[:=]\s*\S+",
    re.IGNORECASE,
)


@lru_cache(maxsize=1)
def get_config() -> dict:
    """Load and validate all configuration from environment.

    Returns a typed dict of all config values. Cached after first call;
    use get_config.cache_clear() if env changes at runtime.
    """
    config = {
        "google_api_key": os.getenv("GOOGLE_API_KEY", ""),
        "use_vertex_ai": os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE",
        "gcp_project": os.getenv("GOOGLE_CLOUD_PROJECT", ""),
        "gcp_location": os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        "app_name": os.getenv("APP_NAME", "capstone_agent"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        # --- Model selection (see llm.py for the registry of tiers) ---
        "model_id": os.getenv("MODEL_ID", "gemini-3.1-flash-lite"),
        "model_tier": os.getenv("MODEL_TIER", "flash-lite"),
        "max_tool_count": int(os.getenv("MAX_TOOL_COUNT", "15")),
        "session_compact_after": int(os.getenv("SESSION_COMPACT_AFTER", "40")),
        # --- Observability ---
        "enable_tracing": os.getenv("ENABLE_TRACING", "FALSE").upper() == "TRUE",
        "trace_exporter": os.getenv("TRACE_EXPORTER", "otlp").lower(),  # otlp | gcp
        "log_format": os.getenv("LOG_FORMAT", "json"),
        # --- Memory backends (see memory.py factories) ---
        "session_backend": os.getenv("SESSION_BACKEND", "memory").lower(),  # memory | database
        "session_db_url": os.getenv("SESSION_DB_URL", "sqlite:///./capstone_sessions.db"),
        "memory_backend": os.getenv("MEMORY_BACKEND", "memory").lower(),  # memory | vertex
        "agent_engine_id": os.getenv("AGENT_ENGINE_ID", ""),
        # --- Resumability (human-in-the-loop, long-running ops) ---
        "enable_resumability": os.getenv("ENABLE_RESUMABILITY", "TRUE").upper() == "TRUE",
        # --- A2A serving (Day 5a) ---
        "a2a_port": int(os.getenv("A2A_PORT", "8001")),
        # --- Clinical governance ---
        "hipaa_compliance_mode": os.getenv("HIPAA_MODE", "TRUE").upper() == "TRUE",
        "phi_redaction_enabled": os.getenv("PHI_REDACTION", "TRUE").upper() == "TRUE",
        "audit_retention_days": int(os.getenv("AUDIT_RETENTION_DAYS", "2190")),
        "extraction_confidence_threshold": float(
            os.getenv("EXTRACTION_CONFIDENCE_THRESHOLD", "0.80")
        ),
        "sensitive_action_requires_approval": (
            os.getenv("SENSITIVE_APPROVAL", "TRUE").upper() == "TRUE"
        ),
    }

    # Invariant: HIPAA mode forces PHI redaction on — a misconfigured
    # deploy must not silently disable redaction while claiming compliance.
    if config["hipaa_compliance_mode"] and not config["phi_redaction_enabled"]:
        config["phi_redaction_enabled"] = True

    return config


def redact_secrets(text: str) -> str:
    """Replace secret-like patterns in text with [REDACTED].

    Applied to all log output and error messages to prevent
    accidental secret leakage in logs, traces, and responses.
    """
    return REDACT_PATTERNS.sub("[REDACTED]", text)


def deterministic_json(data: object) -> str:
    """Serialize to JSON with sorted keys and compact separators.

    Deterministic output improves KV-cache hit rates when the
    same data appears across context windows. Used by context.py
    and memory.py for consistent serialization.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)
