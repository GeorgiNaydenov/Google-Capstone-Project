"""Tests for context engineering utilities (Day 1 working memory).

Covers the rule-based helpers in context.py: token estimation, structured
assembly, boundary injection, and the manual compaction fallback (the
dependency-free alternative to ADK's EventsCompactionConfig).
"""

from capstone_agent import context


def test_estimate_tokens_is_roughly_quarter_length():
    assert context.estimate_tokens("a" * 40) == 10
    assert context.estimate_tokens("") == 1  # never returns 0


def test_structured_context_has_delimited_sections():
    out = context.build_structured_context(
        role="tester",
        environment={"k": "v"},
        active_task="do it",
        constraints=["be safe"],
    )
    assert "<role>tester</role>" in out
    assert "<environment>" in out
    assert "<active_task>do it</active_task>" in out
    assert "be safe" in out


def test_inject_at_boundaries_repeats_critical_info():
    out = context.inject_at_boundaries("BODY", "RULE")
    assert out.startswith("RULE")
    assert out.endswith("RULE")
    assert out.count("RULE") == 2


def test_compact_history_preserves_recent_and_summarizes_old():
    turns = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
    compacted = context.compact_history(turns, keep_recent=5)
    # First entry is a summary; the last 5 turns are preserved verbatim.
    assert compacted[0]["role"] == "system"
    assert "summary" in compacted[0]["content"].lower()
    assert compacted[-5:] == turns[-5:]
    # Input list is never mutated (append-only contract).
    assert len(turns) == 20


def test_compact_history_noop_when_short():
    turns = [{"role": "user", "content": "hi"}]
    assert context.compact_history(turns, keep_recent=10) == turns
