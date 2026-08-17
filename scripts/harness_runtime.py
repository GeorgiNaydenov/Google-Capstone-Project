"""Lifecycle state and handoff runtime for the repository agent harness.

Claude Code invokes this module from project hooks. It keeps ephemeral session
state under ``.claude/state/`` (gitignored), injects compact project context at
session and subagent boundaries, records sanitized subagent handoffs, and runs
the deterministic wiki/harness sync when a turn stops.

The module uses only the Python standard library so hooks still work before the
project virtual environment has been installed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".claude" / "state"
HANDOFF_DIR = STATE_DIR / "handoffs"
SESSION_STATE = STATE_DIR / "session.json"
SCHEMA_VERSION = 1
MAX_CONTEXT_CHARS = 6_000
MAX_HANDOFF_CHARS = 2_000

_SENSITIVE_PATTERNS = (
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b"),
    re.compile(
        r"(?:api[_-]?key|secret|password|token|credential)"
        r"\s*[:=]\s*['\"]?\S+",
        re.IGNORECASE,
    ),
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
)


def utc_now() -> str:
    """Return a stable UTC timestamp suitable for JSON state."""
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sanitize_text(value: str, limit: int = MAX_HANDOFF_CHARS) -> str:
    """Redact common sensitive values and bound persisted hook text."""
    redacted = value
    for pattern in _SENSITIVE_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted[:limit]


def read_hook_input(stream: Any = None) -> dict[str, Any]:
    """Read one Claude Code hook payload from stdin.

    Empty or malformed input returns an empty mapping. Hooks must remain
    non-blocking when launched manually or by older clients.
    """
    source = stream if stream is not None else sys.stdin
    raw = source.read()
    if not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def read_json(path: Path) -> dict[str, Any]:
    """Read a JSON object, returning an empty mapping for missing/corrupt state."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomically write JSON state so interrupted hooks cannot corrupt it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        newline="\n",
        delete=False,
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as handle:
        handle.write(serialized)
        temporary = Path(handle.name)
    temporary.replace(path)


def _session_base(event: dict[str, Any]) -> dict[str, Any]:
    """Return existing session state upgraded with current hook metadata."""
    state = read_json(SESSION_STATE)
    session_id = str(event.get("session_id", state.get("session_id", "unknown")))
    if state.get("session_id") != session_id:
        state = {
            "schema_version": SCHEMA_VERSION,
            "session_id": session_id,
            "started_at": utc_now(),
            "active_agents": {},
            "completed_agents": [],
            "turn_count": 0,
        }
    state.update(
        {
            "schema_version": SCHEMA_VERSION,
            "session_id": session_id,
            "updated_at": utc_now(),
        }
    )
    return state


def _pending_handoffs(recipient: str) -> list[dict[str, Any]]:
    """Return sanitized handoffs addressed to a recipient or the root agent."""
    if not HANDOFF_DIR.is_dir():
        return []
    records: list[dict[str, Any]] = []
    for path in sorted(HANDOFF_DIR.glob("*.json"), reverse=True):
        record = read_json(path)
        target = str(record.get("to", "root"))
        if target in {"root", recipient}:
            records.append(record)
        if len(records) == 3:
            break
    return records


def _project_context(recipient: str) -> str:
    """Assemble compact durable memory and pending handoffs for hook injection."""
    parts = [
        "Harness runtime active. Follow .claude/memory/handoff-protocol.md. "
        "Runtime state is ephemeral under .claude/state/; durable facts belong "
        "in project or subagent MEMORY.md files.",
    ]
    project_memory = ROOT / ".claude" / "memory" / "project.md"
    if project_memory.is_file():
        parts.append(project_memory.read_text(encoding="utf-8"))
    handoffs = _pending_handoffs(recipient)
    if handoffs:
        rendered = ["Pending handoffs:"]
        for record in handoffs:
            rendered.append(
                f"- {record.get('from', 'unknown')} -> {record.get('to', 'root')}: "
                f"{record.get('summary', '(no summary)')}"
            )
        parts.append("\n".join(rendered))
    return sanitize_text("\n\n".join(parts), MAX_CONTEXT_CHARS)


def _print_additional_context(event_name: str, context: str) -> None:
    """Emit Claude Code's structured additional-context hook response."""
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": event_name,
                    "additionalContext": context,
                }
            }
        )
    )


def session_start(event: dict[str, Any]) -> int:
    """Initialize or resume ephemeral session state and inject durable context."""
    state = _session_base(event)
    state.update(
        {
            "status": "active",
            "source": str(event.get("source", "startup")),
            "model": str(event.get("model", "unknown")),
        }
    )
    write_json(SESSION_STATE, state)
    _print_additional_context("SessionStart", _project_context("root"))
    return 0


def subagent_start(event: dict[str, Any]) -> int:
    """Register an active subagent and inject its memory/handoff context."""
    state = _session_base(event)
    agent_id = str(event.get("agent_id", "unknown"))
    agent_type = str(event.get("agent_type", "unknown"))
    active = dict(state.get("active_agents", {}))
    active[agent_id] = {"type": agent_type, "started_at": utc_now()}
    state["active_agents"] = active
    state["status"] = "active"
    write_json(SESSION_STATE, state)
    _print_additional_context("SubagentStart", _project_context(agent_type))
    return 0


def _write_handoff(
    sender: str,
    recipient: str,
    summary: str,
    files: list[str] | None = None,
    agent_id: str | None = None,
) -> Path:
    """Write a sanitized, versioned handoff record and return its path."""
    timestamp = utc_now()
    safe_agent_id = re.sub(r"[^A-Za-z0-9_.-]", "_", agent_id or sender)
    filename = timestamp.replace(":", "").replace("+", "_") + f"-{safe_agent_id}.json"
    record = {
        "schema_version": SCHEMA_VERSION,
        "created_at": timestamp,
        "from": sanitize_text(sender, 100),
        "to": sanitize_text(recipient, 100),
        "summary": sanitize_text(summary),
        "files": [sanitize_text(item, 500) for item in (files or [])],
    }
    path = HANDOFF_DIR / filename
    write_json(path, record)
    return path


def subagent_stop(event: dict[str, Any]) -> int:
    """Record subagent completion and create a sanitized parent handoff."""
    state = _session_base(event)
    agent_id = str(event.get("agent_id", "unknown"))
    agent_type = str(event.get("agent_type", "unknown"))
    active = dict(state.get("active_agents", {}))
    active.pop(agent_id, None)
    completed = list(state.get("completed_agents", []))
    completed.append(
        {
            "id": agent_id,
            "type": agent_type,
            "completed_at": utc_now(),
        }
    )
    state["active_agents"] = active
    state["completed_agents"] = completed[-20:]
    state["updated_at"] = utc_now()
    write_json(SESSION_STATE, state)
    _write_handoff(
        sender=agent_type,
        recipient="root",
        summary=str(event.get("last_assistant_message", "Subagent completed.")),
        agent_id=agent_id,
    )
    return 0


def snapshot(event: dict[str, Any]) -> int:
    """Snapshot session metadata immediately before context compaction."""
    state = _session_base(event)
    state["last_compaction_at"] = utc_now()
    state["status"] = "compacting"
    write_json(SESSION_STATE, state)
    return 0


def stop(event: dict[str, Any]) -> int:
    """Mark a completed turn and run deterministic wiki/harness synchronization."""
    state = _session_base(event)
    state["turn_count"] = int(state.get("turn_count", 0)) + 1
    state["last_turn_completed_at"] = utc_now()
    state["status"] = "waiting"
    write_json(SESSION_STATE, state)
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "sync_wiki.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    if result.stderr.strip():
        print(result.stderr.strip(), file=sys.stderr)
    return result.returncode


def session_end(event: dict[str, Any]) -> int:
    """Mark the local session ended without deleting recoverable state."""
    state = _session_base(event)
    state["status"] = "ended"
    state["ended_at"] = utc_now()
    state["active_agents"] = {}
    write_json(SESSION_STATE, state)
    return 0


def manual_handoff(args: argparse.Namespace) -> int:
    """Create an explicit cross-agent handoff from command-line arguments."""
    path = _write_handoff(args.sender, args.recipient, args.summary, args.files)
    print(path.relative_to(ROOT).as_posix())
    return 0


def show_status() -> int:
    """Print current ephemeral state and recent handoffs as JSON."""
    payload = {
        "session": read_json(SESSION_STATE),
        "handoffs": _pending_handoffs("root"),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the lifecycle and manual handoff command parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in (
        "session-start",
        "subagent-start",
        "subagent-stop",
        "snapshot",
        "stop",
        "session-end",
        "status",
    ):
        subparsers.add_parser(command)
    handoff = subparsers.add_parser("handoff")
    handoff.add_argument("--from", dest="sender", required=True)
    handoff.add_argument("--to", dest="recipient", required=True)
    handoff.add_argument("--summary", required=True)
    handoff.add_argument("--file", dest="files", action="append", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    """Dispatch a hook event or manual harness command."""
    args = build_parser().parse_args(argv)
    if args.command == "handoff":
        return manual_handoff(args)
    if args.command == "status":
        return show_status()
    event = read_hook_input()
    handlers = {
        "session-start": session_start,
        "subagent-start": subagent_start,
        "subagent-stop": subagent_stop,
        "snapshot": snapshot,
        "stop": stop,
        "session-end": session_end,
    }
    return handlers[args.command](event)


if __name__ == "__main__":
    raise SystemExit(main())
