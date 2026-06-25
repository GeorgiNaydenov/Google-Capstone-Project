"""Memory management — Layer 2 (Session State), Layer 3 (Long-Term), Layer 4 (A2A Context).

Encapsulates ADK's SessionService and MemoryService with governance
rules (PII filtering, temporal metadata, A2A context preparation).

Memory architecture:
- Layer 1 (Working Memory): managed by context.py
- Layer 2 (Session State): ADK session.state dict, helpers here
- Layer 3 (Long-Term Memory): MemoryService, lifecycle here
- Layer 4 (A2A Context): prepare_a2a_context() extracts shareable state

Key behaviors:
- auto_save_memory_callback: wired as after_agent_callback to persist
  completed sessions into long-term memory automatically.
- filter_pii_before_storage: strips PII from session content before
  memory ingestion (memory governance from Day 3b).
- prepare_a2a_context: extracts only task-relevant, non-sensitive
  state for A2A delegation (no PII, no secrets, no temp: keys).
- search_past_conversations: custom tool for agent-initiated memory
  retrieval via ToolContext.search_memory().
"""

from typing import Any

from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService

from .config import get_config
from .observability import log_security_event
from .security import detect_phi, redact_phi


def create_session_service():
    """Factory for the session service (Day 3a), selected by SESSION_BACKEND.

    - 'memory'   (default): InMemorySessionService — fast, ephemeral, dev.
    - 'database': DatabaseSessionService — persists sessions across restarts
      (SQLite/Postgres via SESSION_DB_URL). Requires google-adk[db] (sqlalchemy);
      imported lazily so the default path has no extra dependency.

    >>> CUSTOMIZE: set SESSION_BACKEND=database + SESSION_DB_URL for persistence.
    """
    config = get_config()
    if config["session_backend"] == "database":
        from google.adk.sessions import DatabaseSessionService  # lazy: needs sqlalchemy

        db_url = config["session_db_url"]
        # ADK 2.x uses SQLAlchemy's async engine for persistent sessions.
        # Keep older sqlite:/// configuration values working safely.
        if db_url.startswith("sqlite:///"):
            db_url = db_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
        return DatabaseSessionService(db_url=db_url)
    return InMemorySessionService()


def create_memory_service():
    """Factory for the long-term memory service (Day 3b), by MEMORY_BACKEND.

    - 'memory' (default): InMemoryMemoryService — keyword search, no persistence.
    - 'vertex': VertexAiMemoryBankService — LLM-extracted, semantic, persistent
      cloud memory. Requires Vertex AI + an Agent Engine id; imported lazily.

    >>> CUSTOMIZE: set MEMORY_BACKEND=vertex + AGENT_ENGINE_ID for production.
    """
    config = get_config()
    if config["memory_backend"] == "vertex" and config["agent_engine_id"]:
        from google.adk.memory import VertexAiMemoryBankService  # lazy: needs Vertex

        return VertexAiMemoryBankService(
            project=config["gcp_project"],
            location=config["gcp_location"],
            agent_engine_id=config["agent_engine_id"],
        )
    return InMemoryMemoryService()


async def auto_save_memory_callback(callback_context) -> None:
    """After-agent callback: save completed session to long-term memory.

    Wired as after_agent_callback on agents that should persist their
    conversations. Implements the write path of Layer 3 (Long-Term Memory)
    with memory governance: PII in session state is redacted *before* the
    session is committed to long-term memory (Day 3b), and temp: keys are
    never persisted. This closes the privacy gap where raw PII could leak
    across sessions.
    """
    try:
        # Redact PII in state values in-place so nothing sensitive is persisted.
        state = callback_context.state
        filtered = filter_state_for_storage(dict(state))
        for key, value in filtered.items():
            if state.get(key) != value:
                state[key] = value  # write back the redacted value
        await callback_context.add_session_to_memory()
    except Exception as e:
        log_security_event("memory_save_error", {"error": str(e)})


def filter_state_for_storage(state: dict) -> dict:
    """Strip PII and secrets from session state before memory ingestion.

    Memory governance rule: personal information and protected health
    information (PHI) should not persist in long-term memory unless
    explicitly authorized. Uses detect_phi/redact_phi which covers
    both generic PII and clinical identifiers (MRN, ICD-10, NPI, etc.).
    """
    filtered = {}
    for key, value in state.items():
        if key.startswith("temp:"):
            continue
        if isinstance(value, str):
            phi_found = detect_phi(value)
            if phi_found:
                log_security_event("phi_filtered_from_memory", {
                    "key": key,
                    "phi_types": [p["type"] for p in phi_found],
                })
                filtered[key] = redact_phi(value)
            else:
                filtered[key] = value
        else:
            filtered[key] = value
    return filtered


def prepare_a2a_context(task_description: str, state: dict) -> dict:
    """Extract only shareable state for A2A delegation.

    Layer 4 (A2A Context) rule: remote agents get isolated memory
    scopes. Only task-relevant, non-sensitive data crosses the
    boundary. No PII, no secrets, no temp: keys, no user: keys.

    Args:
        task_description: What the remote agent should do.
        state: Current session state dict.

    Returns:
        A dict safe to include in A2A messages.
    """
    shareable = {"task": task_description}

    for key, value in state.items():
        # Skip scoped keys that shouldn't cross agent boundaries
        if key.startswith(("temp:", "user:", "app:")):
            continue
        # Skip anything with PII or PHI
        if isinstance(value, str) and detect_phi(value):
            continue
        shareable[key] = value

    return shareable


async def search_past_conversations(
    query: str,
    tool_context: Any,
) -> dict[str, Any]:
    """Search long-term memory for relevant past conversations.

    This is a custom tool function wired to the root agent.
    It wraps ADK's ToolContext.search_memory() with structured
    result formatting.

    Use this tool when the user references something from a
    previous session or when context from past interactions
    would help answer the current question.

    Args:
        query: What to search for in past conversations.
        tool_context: ADK ToolContext (injected automatically).

    Returns:
        Dict with 'status' and 'results' keys.
    """
    try:
        response = await tool_context.search_memory(query)
        results = []
        for entry in response.memories:
            if entry.content and entry.content.parts:
                text_parts = [
                    part.text for part in entry.content.parts if part.text
                ]
                if text_parts:
                    results.append(" ".join(text_parts))

        return {
            "status": "success",
            "results": results if results else ["No relevant past conversations found."],
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Memory search failed: {e}",
            "results": [],
        }
