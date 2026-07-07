"""Lazy Google ADK execution bridge for live product mode."""

import asyncio
import json
import re
from typing import Any, Callable
from uuid import uuid4

# Shared across requests so a caller-supplied session_key can resume prior
# turns (Q&A follow-ups) and saved memories survive between requests. Created
# lazily inside execute_live so demo tenant sessions never import ADK.
_session_service: Any = None
_memory_service: Any = None

# Lean single-purpose agents built once and reused across requests, keyed by
# execute_live's target parameter. Kept separate from the root agent so the
# fast preview path never pays the orchestrator routing call or the MCP
# subprocess startup.
_target_agents: dict[str, Any] = {}

# Extraction-pipeline tools (assess_image_quality, extract_clinical_text,
# analyze_clinical_image) take a filesystem path or GCS URI, not inline bytes.
# A freshly uploaded file has neither until we write it to disk here, so
# without this mapping the sub-agents can only hallucinate a URI and every
# tool call 404s against the database.
_MIME_EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

# Pipeline output_key values surfaced to the product API (see
# capstone_agent/orchestration.py). SequentialAgent final responses come from
# the last stage (audit narration), so structured results must be read from
# session state, not the final text.
_STATE_OUTPUT_KEYS = (
    "structured_output",
    "refined_output",
    "review_decision",
    "qa_answer",
    "cited_sources",
    "generated_sql",
    "validated_sql",
    "query_results",
    "insight_summary",
)


# Stream-level failure signatures worth one retry. HTTP-level retries are
# already handled by llm.build_model's HttpRetryOptions; this catches aborts
# surfaced mid-stream after the connection succeeded.
# gRPC status codes are matched case-sensitively: a lowercase "unavailable"
# usually describes a missing local runtime, not a retryable server error.
_TRANSIENT_PATTERN = re.compile(r"429|RESOURCE_EXHAUSTED|UNAVAILABLE|503|DEADLINE|[Oo]verloaded")


def _is_transient(text: str) -> bool:
    """Return True when an error message indicates a retryable model failure.

    Credential, import, and validation errors never match, so a misconfigured
    runtime fails immediately instead of burning retry attempts.
    """

    return bool(_TRANSIENT_PATTERN.search(text))


async def execute_live(
    query: str,
    user_id: str,
    file_bytes: bytes | None = None,
    file_mime: str | None = None,
    patient_context: dict[str, Any] | None = None,
    session_key: str | None = None,
    max_attempts: int = 2,
    on_step: Callable[[list[dict[str, Any]]], None] | None = None,
    target: str | None = None,
) -> dict[str, Any]:
    """Invoke the root agent with a bounded retry on transient model errors.

    Only stream-level failures matching _TRANSIENT_PATTERN are retried; any
    other exception (missing ADK, bad credentials, agent bugs) is raised
    immediately so the caller can surface an honest error. on_step, if given,
    is called synchronously with the author-steps-so-far every time a new
    agent starts, so a caller can surface real incremental progress instead
    of waiting for the whole (often 30s-several-minute) run to finish.

    target selects a lean single-purpose agent instead of the root
    orchestrator: "sql_draft" runs one schema-grounded NL-to-SQL model call
    for the database preview (validation and execution stay deterministic
    and server-side). None keeps the full multi-agent root pipeline.
    """

    for attempt in range(1, max_attempts + 1):
        try:
            return await _execute_once(
                query, user_id,
                file_bytes=file_bytes, file_mime=file_mime,
                patient_context=patient_context, session_key=session_key,
                on_step=on_step, target=target,
            )
        except Exception as exc:
            if attempt >= max_attempts or not _is_transient(str(exc)):
                raise
            await asyncio.sleep(1.5 * attempt)
    raise RuntimeError("unreachable")  # loop always returns or raises


async def _execute_once(
    query: str,
    user_id: str,
    file_bytes: bytes | None = None,
    file_mime: str | None = None,
    patient_context: dict[str, Any] | None = None,
    session_key: str | None = None,
    on_step: Callable[[list[dict[str, Any]]], None] | None = None,
    target: str | None = None,
) -> dict[str, Any]:
    """Invoke the root agent (or a lean target agent) and return structured results.

    Imports stay inside this function so demo tenant sessions have no model,
    key, network, or ADK graph dependency. When session_key is provided, the
    same ADK session is reused across requests so follow-up questions keep
    conversational context.
    """

    global _session_service, _memory_service

    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types

        from capstone_agent.config import redact_secrets
        from capstone_agent.document_processor import UPLOAD_DIR, generate_document_id
        from capstone_agent.memory import create_memory_service
        from capstone_agent.security import redact_pii

        if target is None:
            # Importing capstone_agent.agent wires the full orchestrator,
            # including the MCP stdio subprocess — only pay that for runs
            # that actually need the multi-agent graph.
            from capstone_agent.agent import root_agent as live_agent
        elif target == "sql_draft":
            if "sql_draft" not in _target_agents:
                from capstone_agent.orchestration import build_sql_draft_agent

                _target_agents["sql_draft"] = build_sql_draft_agent()
            live_agent = _target_agents["sql_draft"]
        else:
            raise ValueError(f"Unknown live execution target: {target}")
    except (ImportError, KeyError) as error:
        raise RuntimeError(f"Live ADK runtime unavailable: {error}") from error

    app_name = "clinical_product_live"
    if _session_service is None:
        _session_service = InMemorySessionService()
    if _memory_service is None:
        # The Q&A pipeline carries load_memory/search_past_conversations and
        # the root agent auto-saves sessions; a Runner without a memory
        # service makes any of those calls fail the whole run.
        _memory_service = create_memory_service()
    session_service = _session_service
    session_id = f"live-{session_key}" if session_key else f"live-{uuid4().hex}"
    session = await session_service.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id,
    )
    if session is None:
        # State must be passed at creation: create_session returns a copy, so
        # post-hoc session.state mutations never reach the stored session.
        session = await session_service.create_session(
            app_name=app_name, user_id=user_id, session_id=session_id,
            state=dict(patient_context or {}),
        )
    # Snapshot so only keys written by THIS run surface as outputs. Resumed
    # sessions keep prior pipeline state (e.g. qa_answer), and returning it
    # again would mask a fresh answer produced outside that pipeline.
    baseline_state = dict(session.state or {})

    effective_query = query
    if file_bytes and file_mime:
        extension = _MIME_EXTENSIONS.get(file_mime, "")
        saved_path = UPLOAD_DIR / f"{generate_document_id('live-upload' + extension, file_bytes)}{extension}"
        if not saved_path.exists():
            saved_path.write_bytes(file_bytes)
        # Pipeline tools (assess_image_quality, extract_clinical_text,
        # analyze_clinical_image) require this exact local path as their
        # image_uri argument; the inline Part below only lets the top-level
        # model see the content, it does not give tool calls access to it.
        effective_query = (
            f"{query}\n\nThe uploaded file is saved locally at this exact path "
            f"(use it verbatim as image_uri/file_path in tool calls): {saved_path}"
        )

    parts: list[types.Part] = [types.Part(text=effective_query)]
    if file_bytes and file_mime:
        parts.append(types.Part(inline_data=types.Blob(mime_type=file_mime, data=file_bytes)))

    content = types.Content(role="user", parts=parts)
    runner = Runner(
        agent=live_agent,
        app_name=app_name,
        session_service=session_service,
        memory_service=_memory_service,
    )

    final_text = ""
    author_steps: list[dict[str, Any]] = []
    tool_calls: list[dict[str, Any]] = []

    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        author = getattr(event, "author", None) or "unknown"
        if not author_steps or author_steps[-1]["author"] != author:
            author_steps.append({"author": author, "eventId": getattr(event, "id", None)})
            if on_step:
                # A copy: author_steps keeps growing after this call, and the
                # caller may hold onto what it was given across an await.
                on_step(list(author_steps))

        for fc in event.get_function_calls():
            tool_calls.append({
                "tool": getattr(fc, "name", "unknown"),
                "status": "success",
                "args": _safe_json(getattr(fc, "args", {})),
            })

        for fr in event.get_function_responses():
            for tc in reversed(tool_calls):
                if tc["tool"] == getattr(fr, "name", ""):
                    tc["output"] = _safe_json(getattr(fr, "response", {}))
                    break

        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(
                part.text or "" for part in event.content.parts if getattr(part, "text", None)
            )

    final_session = await session_service.get_session(
        app_name=app_name, user_id=user_id, session_id=session_id,
    )
    state = dict(final_session.state) if final_session else {}
    state_outputs: dict[str, Any] = {}
    for key in _STATE_OUTPUT_KEYS:
        if key in state and state[key] != baseline_state.get(key):
            value = state[key]
            state_outputs[key] = redact_pii(redact_secrets(value)) if isinstance(value, str) else value

    safe_text = redact_pii(redact_secrets(final_text))

    fields_source = _string_source(state_outputs, ("structured_output", "refined_output")) or safe_text
    # generated_sql is the nl_to_sql stage's own SQL text; validated_sql is the
    # sql_validator's pass/fail verdict on it ("do not rewrite the SQL
    # yourself" per its prompt) and normally contains no SELECT statement at
    # all, so it must never be preferred over the actual SQL source.
    sql_source = _string_source(state_outputs, ("generated_sql", "validated_sql")) or safe_text

    return {
        "finalResponse": safe_text,
        "authorSteps": author_steps,
        "toolCalls": tool_calls,
        "stateOutputs": state_outputs,
        "fields": _extract_fields(fields_source),
        "confidence": _extract_confidence(safe_text),
        "sql": _extract_sql(sql_source),
    }


def _string_source(state_outputs: dict[str, Any], keys: tuple[str, ...]) -> str:
    """Return the first non-empty state output as text, preferring earlier keys."""

    for key in keys:
        value = state_outputs.get(key)
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, (dict, list)) and value:
            return json.dumps(value)
    return ""


def _safe_json(obj: Any) -> Any:
    """Convert protobuf-like objects to JSON-safe dicts."""

    if isinstance(obj, dict):
        return obj
    try:
        return json.loads(json.dumps(obj, default=str))
    except (TypeError, ValueError):
        return str(obj)


def _parse_json_object(text: str) -> Any:
    """Parse the first JSON object found in text, tolerating nesting and code fences."""

    stripped = text.strip()
    candidates = [stripped]
    fence = re.search(r"```(?:json)?\s*(.*?)```", stripped, re.DOTALL)
    if fence:
        candidates.insert(0, fence.group(1).strip())
    decoder = json.JSONDecoder()
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            start = candidate.find("{")
            if start < 0:
                continue
            try:
                value, _ = decoder.raw_decode(candidate[start:])
                return value
            except json.JSONDecodeError:
                continue
    return None


def _extract_fields(text: str) -> dict[str, str]:
    """Best-effort extraction of structured fields from agent output text."""

    fields: dict[str, str] = {}
    parsed = _parse_json_object(text)
    if isinstance(parsed, dict):
        fields = {str(k): v if isinstance(v, str) else json.dumps(v) for k, v in parsed.items()}
    if not fields:
        for line in text.split("\n"):
            # Markdown table rows and separators produce garbage keys — the
            # line fallback only understands "key: value" prose lines.
            if ":" in line and not line.strip().startswith(("#", "|", "-|", ":")):
                key, _, value = line.partition(":")
                key = key.strip().strip("-*").strip()
                value = value.strip()
                if key and value and len(key) < 60 and "|" not in key:
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
    """Extract the SQL statement (SELECT or WITH...SELECT CTE) from agent output.

    A fenced ```sql block is preferred when present — matching bare SELECT
    against the whole response used to slice a CTE apart by capturing from
    the first SELECT inside `WITH x AS (SELECT ...)`, which produced
    unexecutable SQL.
    """

    fence = re.search(r"```(?:sql)?\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    candidates = ([fence.group(1)] if fence else []) + [text]
    for candidate in candidates:
        match = re.search(
            r"((?:WITH\s+(?:RECURSIVE\s+)?[\w\"]+\s+AS\s*\(|SELECT\s).*?)(?:;|```|\Z)",
            candidate,
            re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(1).strip()
    return ""
