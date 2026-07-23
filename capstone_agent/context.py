"""Context engineering — token budgeting, compaction, structured assembly.

Manages Layer 1 (Working Memory) of the 4-layer memory architecture.
The working memory is the active context window assembled per LLM call.

Key patterns applied:
- Token Pipeline: Collect → Rank → Compress → Budget → Assemble
- Append-only context: never mutate or reorder turns
- "Lost in the middle" mitigation: critical info at start and end
- Compaction: summarize old turns, preserve recent verbatim

This module produces structured context strings consumed by agent.py
and callbacks.py. It does NOT call the LLM — compaction here is
rule-based (truncation + metadata preservation).
"""

from .config import deterministic_json


def estimate_tokens(text: str) -> int:
    """Rough token estimate using chars/4 heuristic.

    Good enough for budget decisions without calling a tokenizer.
    Gemini averages ~4 chars per token for English text.
    """
    return max(1, len(text) // 4)


def build_structured_context(
    role: str,
    environment: dict,
    active_task: str = "",
    constraints: list[str] | None = None,
) -> str:
    """Assemble a structured context string with clear section delimiters.

    Follows the "make input parsing explicit" pattern — delimiters
    separate instructions from data so the model can distinguish them.

    Args:
        role: Agent role description (1-2 sentences).
        environment: Dict of environment info (tools available, config).
        active_task: Current task description, if any.
        constraints: List of constraint strings.
    """
    sections = []

    sections.append(f"<role>{role}</role>")

    env_str = deterministic_json(environment)
    sections.append(f"<environment>{env_str}</environment>")

    if active_task:
        sections.append(f"<active_task>{active_task}</active_task>")

    if constraints:
        constraints_str = "\n".join(f"- {c}" for c in constraints)
        sections.append(f"<constraints>\n{constraints_str}\n</constraints>")

    return "\n\n".join(sections)


def compact_history(
    turns: list[dict],
    keep_recent: int = 10,
    max_total_tokens: int = 8000,
) -> list[dict]:
    """Compact conversation history by summarizing older turns.

    Preserves the most recent `keep_recent` turns verbatim.
    Older turns are compressed to metadata summaries (role + length).
    This is rule-based compaction — no LLM call required.

    Args:
        turns: List of turn dicts with 'role' and 'content' keys.
        keep_recent: Number of recent turns to preserve verbatim.
        max_total_tokens: Token budget for the compacted history.

    Returns:
        New list of turns (never mutates the input list).
    """
    if len(turns) <= keep_recent:
        return list(turns)

    old_turns = turns[:-keep_recent]
    recent_turns = turns[-keep_recent:]

    # Summarize old turns as compact metadata
    summary_parts = []
    for turn in old_turns:
        role = turn.get("role", "unknown")
        content = turn.get("content", "")
        preview = content[:80] + "..." if len(content) > 80 else content
        summary_parts.append(f"[{role}: {preview}]")

    summary_text = " | ".join(summary_parts)

    # Truncate summary if it exceeds budget
    recent_tokens = sum(estimate_tokens(t.get("content", "")) for t in recent_turns)
    available_for_summary = max(100, max_total_tokens - recent_tokens)
    if estimate_tokens(summary_text) > available_for_summary:
        char_limit = available_for_summary * 4
        summary_text = summary_text[:char_limit] + "...[truncated]"

    compacted = [
        {"role": "system", "content": f"[Earlier conversation summary: {summary_text}]"}
    ]
    compacted.extend(recent_turns)

    return compacted


def inject_at_boundaries(context: str, critical_info: str) -> str:
    """Place critical information at both start and end of context.

    Mitigates the "lost in the middle" problem — models attend
    more strongly to content at the beginning and end of the
    context window. Critical constraints or safety instructions
    should appear in both positions.
    """
    return f"{critical_info}\n\n{context}\n\n{critical_info}"
