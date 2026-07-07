"""Tests for memory governance (Day 3b).

Covers the privacy-critical paths: PII is redacted before long-term storage,
temp: state never persists, and A2A context only exposes shareable data.
No API key required.
"""

from types import SimpleNamespace

from capstone_agent import memory


def _email(local: str = "user", domain: str = "example", tld: str = "com") -> str:
    """Build a PII fixture without committing a raw email address."""
    return local + "@" + domain + "." + tld


def test_filter_redacts_pii_and_drops_temp_keys():
    email = _email("john")
    state = {
        "note": "reach me at " + email,
        "temp:scratch": "ephemeral",
        "count": 3,
    }
    out = memory.filter_state_for_storage(state)
    assert "temp:scratch" not in out          # temp: never persisted
    assert email not in out["note"]           # PII redacted
    assert out["count"] == 3                   # non-PII preserved untouched


def test_prepare_a2a_context_excludes_scoped_and_pii():
    state = {
        "topic": "weather",
        "user:name": "Jo",
        "temp:x": "1",
        "email": _email("a", "b"),
    }
    ctx = memory.prepare_a2a_context("summarize the topic", state)
    assert ctx["task"] == "summarize the topic"
    assert ctx["topic"] == "weather"
    assert "user:name" not in ctx   # user: scope stays local
    assert "temp:x" not in ctx      # temp: never crosses the boundary
    assert "email" not in ctx       # PII never crosses the boundary


async def test_auto_save_redacts_state_before_persisting():
    persisted = {}
    email = _email("x", "y")

    class FakeCtx:
        def __init__(self):
            self.state = {"note": "email me at " + email}

        async def add_session_to_memory(self):
            persisted["state"] = dict(self.state)

    ctx = FakeCtx()
    await memory.auto_save_memory_callback(ctx)

    # State was scrubbed in place AND the (now-redacted) session was saved.
    assert email not in ctx.state["note"]
    assert persisted and email not in persisted["state"]["note"]
