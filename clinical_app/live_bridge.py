"""Lazy Google ADK execution bridge for live product mode."""

import base64
import json
import re
from typing import Any
from uuid import uuid4


async def execute_live(
    query: str,
    user_id: str,
    file_bytes: bytes | None = None,
    file_mime: str | None = None,
    patient_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Invoke the root agent with optional multimodal content and return structured results.

    Imports stay inside this function so demo tenant sessions have no model,
    key, network, or ADK graph dependency.
    """

    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types

        from capstone_agent.agent import root_agent
        from capstone_agent.config import redact_secrets
        from capstone_agent.security import redact_pii
    except (ImportError, KeyError) as error:
        raise RuntimeError(f"Live ADK runtime unavailable: {error}") from error

    app_name = "clinical_product_live"
    session_id = f"live-{uuid4().hex}"
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=app_name, user_id=user_id, session_id=session_id,
    )
    if patient_context:
        for key, value in patient_context.items():
            session.state[key] = value

    parts: list[types.Part] = [types.Part(text=query)]
    if file_bytes and file_mime:
        parts.append(types.Part(inline_data=types.Blob(mime_type=file_mime, data=file_bytes)))

    content = types.Content(role="user", parts=parts)
    runner = Runner(agent=root_agent, app_name=app_name, session_service=session_service)

    final_text = ""
    author_steps: list[dict[str, Any]] = []
    tool_calls: list[dict[str, Any]] = []

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        author = getattr(event, "author", None) or "unknown"
        if not author_steps or author_steps[-1]["author"] != author:
            author_steps.append({"author": author, "eventId": getattr(event, "id", None)})

        if hasattr(event, "function_calls") and event.function_calls:
            for fc in event.function_calls:
                tool_calls.append({
                    "tool": getattr(fc, "name", "unknown"),
                    "status": "success",
                    "args": _safe_json(getattr(fc, "args", {})),
                })

        if hasattr(event, "function_responses") and event.function_responses:
            for fr in event.function_responses:
                for tc in reversed(tool_calls):
                    if tc["tool"] == getattr(fr, "name", ""):
                        tc["output"] = _safe_json(getattr(fr, "response", {}))
                        break

        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(
                part.text or "" for part in event.content.parts if getattr(part, "text", None)
            )

    safe_text = redact_pii(redact_secrets(final_text))

    fields = _extract_fields(safe_text)
    confidence = _extract_confidence(safe_text)
    sql = _extract_sql(safe_text)

    return {
        "finalResponse": safe_text,
        "authorSteps": author_steps,
        "toolCalls": tool_calls,
        "fields": fields,
        "confidence": confidence,
        "sql": sql,
    }


def _safe_json(obj: Any) -> Any:
    """Convert protobuf-like objects to JSON-safe dicts."""

    if isinstance(obj, dict):
        return obj
    try:
        return json.loads(json.dumps(obj, default=str))
    except (TypeError, ValueError):
        return str(obj)


def _extract_fields(text: str) -> dict[str, str]:
    """Best-effort extraction of structured fields from agent response text."""

    fields: dict[str, str] = {}
    json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, dict):
                fields = {str(k): str(v) for k, v in parsed.items()}
        except json.JSONDecodeError:
            pass
    if not fields:
        for line in text.split("\n"):
            if ":" in line and not line.strip().startswith("#"):
                key, _, value = line.partition(":")
                key = key.strip().strip("-*").strip()
                value = value.strip()
                if key and value and len(key) < 60:
                    fields[key] = value
    return fields


def _extract_confidence(text: str) -> float:
    """Best-effort confidence extraction from agent response."""

    match = re.search(r"confidence[:\s]*(\d+(?:\.\d+)?)\s*%?", text, re.IGNORECASE)
    if match:
        val = float(match.group(1))
        return val / 100 if val > 1 else val
    return 0.85


def _extract_sql(text: str) -> str:
    """Extract SQL statement from agent response if present."""

    match = re.search(r"(SELECT\s.+?)(?:;|\Z)", text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""
