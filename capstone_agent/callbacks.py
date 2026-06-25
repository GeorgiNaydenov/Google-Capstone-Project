"""Security callbacks — defense in depth for agent safety.

Implements the 3-layer security architecture required by the capstone rubric:

Layer 1 (before_model_callback): Inspect user input BEFORE the LLM sees it.
    - Blocks prompt injection via security.is_blocked_input()
    - Sanitizes input via security.sanitize_input()

Layer 2 (before_tool_callback): Validate tool calls BEFORE execution.
    - Checks for empty/missing arguments
    - Enforces per-tool rate limits via temp: state
    - Scans tool args for injected secrets

Layer 3 (after_model_callback): Inspect LLM output BEFORE the user sees it.
    - Detects PII in model responses via security.detect_pii()
    - Catches leaked secrets via security.scan_for_secrets()

All blocked events are logged via observability.log_security_event()
for audit trail. Detection logic lives in security.py (pure functions,
independently testable); this module handles the ADK callback wiring.
"""

from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

from .observability import log_security_event
from .security import (
    detect_pii,
    is_blocked_input,
    sanitize_input,
    scan_for_secrets,
)

# Max tool calls per tool per invocation (rate limiting).
TOOL_RATE_LIMIT = 20


def _make_block_response(message: str) -> LlmResponse:
    """Create a blocking LlmResponse that short-circuits the request."""
    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(text=message)],
        )
    )


def _extract_last_user_text(llm_request: LlmRequest) -> str:
    """Extract the text of the most recent user message."""
    if not llm_request.contents:
        return ""
    for content in reversed(llm_request.contents):
        if content.role == "user" and content.parts:
            for part in content.parts:
                if part.text:
                    return part.text
    return ""


# --- Layer 1: Input Safety (before_model_callback) ---

def content_safety_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    """Block prompt injection and sanitize input before the LLM sees it.

    Uses security.is_blocked_input() for pattern matching (15+ patterns)
    and security.sanitize_input() for unicode/control-char cleaning.
    """
    last_user_text = _extract_last_user_text(llm_request)
    if not last_user_text:
        return None

    # Sanitize: normalize unicode, strip control characters
    sanitized = sanitize_input(last_user_text)

    # Check for injection patterns
    blocked, reason = is_blocked_input(sanitized)
    if blocked:
        log_security_event("input_blocked", {
            "reason": reason,
            "input_length": len(sanitized),
        })
        return _make_block_response(
            "I'm unable to process that request. Please rephrase your question."
        )

    return None


# --- Layer 2: Tool Authorization (before_tool_callback) ---

def tool_authorization_callback(
    callback_context: CallbackContext,
    tool_name: str,
    tool_args: dict,
) -> Optional[dict]:
    """Validate tool calls before execution.

    Enforces:
    - Non-empty arguments for tools that require them
    - Per-tool rate limiting via temp: session state
    - Secret scanning on tool arguments
    """
    # Check for empty arguments
    if not tool_args:
        log_security_event("tool_blocked", {
            "tool": tool_name,
            "reason": "empty_arguments",
        })
        return {"status": "error", "message": f"Tool '{tool_name}' requires arguments."}

    # Rate limiting: track call count in temp: state
    rate_key = f"temp:tool_calls_{tool_name}"
    call_count = callback_context.state.get(rate_key, 0)
    if call_count >= TOOL_RATE_LIMIT:
        log_security_event("tool_rate_limited", {
            "tool": tool_name,
            "count": call_count,
        })
        return {
            "status": "error",
            "message": f"Tool '{tool_name}' rate limit exceeded ({TOOL_RATE_LIMIT} calls).",
        }
    callback_context.state[rate_key] = call_count + 1

    # Scan tool args for injected secrets
    args_text = " ".join(str(v) for v in tool_args.values())
    secrets = scan_for_secrets(args_text)
    if secrets:
        log_security_event("secrets_in_tool_args", {
            "tool": tool_name,
            "secret_types": [s["type"] for s in secrets],
        })
        return {
            "status": "error",
            "message": "Tool arguments contain sensitive data. Please remove secrets.",
        }

    return None


# --- Layer 3: Output Safety (after_model_callback) ---

def output_safety_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    """Check LLM output for PII and secrets before returning to user.

    If sensitive data is detected, the response is replaced with
    a safe message. This is the last line of defense.
    """
    if not llm_response.content or not llm_response.content.parts:
        return None

    for part in llm_response.content.parts:
        if not part.text:
            continue

        # Check for PII
        pii_findings = detect_pii(part.text)
        if pii_findings:
            log_security_event("pii_in_output", {
                "pii_types": [p["type"] for p in pii_findings],
            })

        # Check for leaked secrets
        secret_findings = scan_for_secrets(part.text)
        if secret_findings:
            log_security_event("secrets_in_output", {
                "secret_types": [s["type"] for s in secret_findings],
            })
            return _make_block_response(
                "I detected sensitive information in my response and removed it "
                "for your security. Please rephrase your request."
            )

    return None
