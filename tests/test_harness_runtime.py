"""Tests for lifecycle state, handoff, and safe mirror harness tooling."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import harness_runtime  # noqa: E402
import sync_harness  # noqa: E402


def _configure_runtime(monkeypatch, tmp_path: Path) -> None:
    """Point harness runtime constants at an isolated fake repository."""
    state = tmp_path / ".claude" / "state"
    monkeypatch.setattr(harness_runtime, "ROOT", tmp_path)
    monkeypatch.setattr(harness_runtime, "STATE_DIR", state)
    monkeypatch.setattr(harness_runtime, "HANDOFF_DIR", state / "handoffs")
    monkeypatch.setattr(harness_runtime, "SESSION_STATE", state / "session.json")
    memory = tmp_path / ".claude" / "memory"
    memory.mkdir(parents=True)
    (memory / "project.md").write_text("# Stable context\n", encoding="utf-8")


def test_session_start_persists_state_and_injects_context(
    monkeypatch,
    tmp_path,
    capsys,
):
    """SessionStart creates recoverable state and emits hook context JSON."""
    _configure_runtime(monkeypatch, tmp_path)
    event = {
        "session_id": "session-1",
        "source": "startup",
        "model": "test-model",
    }
    assert harness_runtime.session_start(event) == 0
    state = harness_runtime.read_json(harness_runtime.SESSION_STATE)
    assert state["status"] == "active"
    assert state["session_id"] == "session-1"
    output = json.loads(capsys.readouterr().out)
    hook_output = output["hookSpecificOutput"]
    assert hook_output["hookEventName"] == "SessionStart"
    assert "Stable context" in hook_output["additionalContext"]


def test_subagent_stop_creates_sanitized_handoff(monkeypatch, tmp_path):
    """Fallback subagent handoff excludes sensitive completion text."""
    _configure_runtime(monkeypatch, tmp_path)
    secret = "password = " + "x" * 24
    event = {
        "session_id": "session-1",
        "agent_id": "agent-1",
        "agent_type": "security-reviewer",
        "last_assistant_message": "done; " + secret,
    }
    assert harness_runtime.subagent_stop(event) == 0
    handoffs = list(harness_runtime.HANDOFF_DIR.glob("*.json"))
    assert len(handoffs) == 1
    rendered = handoffs[0].read_text(encoding="utf-8")
    assert secret not in rendered
    assert "[REDACTED]" in rendered


def test_sync_preserves_destination_only_assets(monkeypatch, tmp_path):
    """Incremental sync never removes Codex-only files from .agents."""
    claude = tmp_path / ".claude"
    agents = tmp_path / ".agents"
    (claude / "rules").mkdir(parents=True)
    (claude / "rules" / "test.md").write_text(
        "Read .claude/memory/project.md\n",
        encoding="utf-8",
    )
    (tmp_path / "CLAUDE.md").write_text(
        "## Default Style\nUse .claude/rules/test.md\n",
        encoding="utf-8",
    )
    (agents / "skills" / "codex-only").mkdir(parents=True)
    destination_only = agents / "skills" / "codex-only" / "SKILL.md"
    destination_only.write_text("keep\n", encoding="utf-8")

    monkeypatch.setattr(sync_harness, "ROOT", tmp_path)
    monkeypatch.setattr(sync_harness, "CLAUDE_DIR", claude)
    monkeypatch.setattr(sync_harness, "AGENTS_DIR", agents)
    monkeypatch.setattr(
        sync_harness,
        "MANIFEST",
        agents / ".sync-manifest.json",
    )
    sync_harness.sync_harness()

    assert destination_only.read_text(encoding="utf-8") == "keep\n"
    mirrored = agents / "rules" / "test.md"
    assert ".agents/memory/project.md" in mirrored.read_text(encoding="utf-8")
