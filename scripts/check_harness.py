"""Deterministically validate executable repository harness configuration."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DIRECTORIES = (
    ".claude/agents",
    ".claude/agent-memory",
    ".claude/commands",
    ".claude/memory",
    ".claude/references",
    ".claude/rules",
    ".claude/skills",
    ".claude/state",
)
REQUIRED_FILES = (
    "CLAUDE.md",
    "AGENTS.md",
    ".claude/settings.json",
    ".claude/memory/project.md",
    ".claude/memory/handoff-protocol.md",
    "scripts/harness_runtime.py",
    "scripts/sync_harness.py",
)
REQUIRED_HOOKS = {
    "SessionStart": "harness_runtime.py",
    "PreToolUse": "check_harness.py",
    "PreCompact": "harness_runtime.py",
    "SubagentStart": "harness_runtime.py",
    "SubagentStop": "harness_runtime.py",
    "Stop": "harness_runtime.py",
    "SessionEnd": "harness_runtime.py",
}


def _read(relative: str) -> str:
    """Read one UTF-8 repository file."""
    return (ROOT / relative).read_text(encoding="utf-8")


def _frontmatter(text: str) -> dict[str, str]:
    """Parse scalar top-level YAML frontmatter without external dependencies."""
    match = re.match(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n", text)
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if line.startswith((" ", "\t", "-")) or ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip()
    return values


def _hook_commands(settings: dict[str, Any], event: str) -> list[str]:
    """Extract command hook strings for one lifecycle event."""
    commands: list[str] = []
    hooks = settings.get("hooks", {})
    groups = hooks.get(event, []) if isinstance(hooks, dict) else []
    if not isinstance(groups, list):
        return commands
    for group in groups:
        if not isinstance(group, dict):
            continue
        handlers = group.get("hooks", [])
        if not isinstance(handlers, list):
            continue
        for handler in handlers:
            if isinstance(handler, dict) and handler.get("type") == "command":
                command = handler.get("command")
                if isinstance(command, str):
                    commands.append(command)
    return commands


def _indexed_paths(prefix: str) -> list[str]:
    """Return portable harness paths that must appear in the root index."""
    root = ROOT / prefix
    paths: list[str] = []
    for section in ("rules", "commands", "references", "agents", "memory"):
        folder = root / section
        if folder.is_dir():
            for path in sorted(folder.glob("*.md")):
                paths.append(f"{prefix}/{section}/{path.name}")
    skills = root / "skills"
    if skills.is_dir():
        for directory in sorted(path for path in skills.iterdir() if path.is_dir()):
            skill = directory / "SKILL.md"
            if skill.is_file():
                paths.append(f"{prefix}/skills/{directory.name}/SKILL.md")
    return paths


def _validate_skills(errors: list[str]) -> None:
    """Validate portable skill frontmatter in the canonical harness."""
    skills = ROOT / ".claude" / "skills"
    for directory in sorted(path for path in skills.iterdir() if path.is_dir()):
        skill = directory / "SKILL.md"
        if not skill.is_file():
            errors.append(f"Missing .claude/skills/{directory.name}/SKILL.md")
            continue
        metadata = _frontmatter(skill.read_text(encoding="utf-8"))
        if metadata.get("name") != directory.name:
            errors.append(
                f"{skill.relative_to(ROOT).as_posix()} name must match folder"
            )
        description = metadata.get("description", "")
        if len(description) < 40:
            errors.append(
                f"{skill.relative_to(ROOT).as_posix()} description is too short"
            )
        unexpected = set(metadata) - {"name", "description"}
        if unexpected:
            errors.append(
                f"{skill.relative_to(ROOT).as_posix()} has non-portable "
                f"frontmatter keys: {', '.join(sorted(unexpected))}"
            )


def _validate_agents(errors: list[str]) -> None:
    """Validate executable subagent profiles and project-scoped memory."""
    profiles = sorted((ROOT / ".claude" / "agents").glob("*.md"))
    if not profiles:
        errors.append(".claude/agents contains no executable agent profiles")
        return
    for profile in profiles:
        metadata = _frontmatter(profile.read_text(encoding="utf-8"))
        expected_name = profile.stem
        if metadata.get("name") != expected_name:
            errors.append(
                f"{profile.relative_to(ROOT).as_posix()} name must be '{expected_name}'"
            )
        if len(metadata.get("description", "")) < 40:
            errors.append(
                f"{profile.relative_to(ROOT).as_posix()} description is too short"
            )
        if metadata.get("memory") != "project":
            errors.append(
                f"{profile.relative_to(ROOT).as_posix()} must use project memory"
            )
        memory = ROOT / ".claude" / "agent-memory" / expected_name / "MEMORY.md"
        if not memory.is_file():
            errors.append(f"Missing project agent memory for '{expected_name}'")


def _validate_settings(errors: list[str]) -> None:
    """Validate lifecycle hooks are wired to executable repository scripts."""
    try:
        settings = json.loads(_read(".claude/settings.json"))
    except json.JSONDecodeError as exc:
        errors.append(f".claude/settings.json is invalid JSON: {exc}")
        return
    for event, expected_script in REQUIRED_HOOKS.items():
        commands = _hook_commands(settings, event)
        if not commands:
            errors.append(f".claude/settings.json missing {event} command hook")
        elif not any(expected_script in command for command in commands):
            errors.append(f"{event} hook must invoke scripts/{expected_script}")
        elif not all(
            "uv run --no-project --python 3.11" in command for command in commands
        ):
            errors.append(f"{event} hook must use the dependency-free uv launcher")


def _validate_mirror(errors: list[str]) -> None:
    """Validate root indexes and all manifest-managed mirror files."""
    claude = _read("CLAUDE.md")
    agents = _read("AGENTS.md")
    marker = "## Default Style"
    if marker not in claude or marker not in agents:
        errors.append(f"Missing '{marker}' section in CLAUDE.md or AGENTS.md")
    else:
        claude_shared = claude[claude.index(marker) :]
        agents_shared = agents[agents.index(marker) :].replace(".agents/", ".claude/")
        if claude_shared != agents_shared:
            errors.append("CLAUDE.md and AGENTS.md drift after '## Default Style'")

    for prefix, index, name in (
        (".claude", claude, "CLAUDE.md"),
        (".agents", agents, "AGENTS.md"),
    ):
        for path in _indexed_paths(prefix):
            if path not in index:
                errors.append(f"{name} missing reference to {path}")

    manifest_path = ROOT / ".agents" / ".sync-manifest.json"
    if not manifest_path.is_file():
        errors.append("Missing .agents/.sync-manifest.json; run sync_harness.py")
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f".agents/.sync-manifest.json is invalid: {exc}")
        return
    for relative in manifest.get("files", []):
        source = ROOT / ".claude" / relative
        target = ROOT / ".agents" / relative
        if not source.is_file() or not target.is_file():
            errors.append(f"Managed mirror file missing: {relative}")
            continue
        try:
            source_text = source.read_text(encoding="utf-8")
            target_text = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            if source.read_bytes() != target.read_bytes():
                errors.append(f"Managed binary mirror drift: {relative}")
            continue
        expected = source_text.replace(".claude/", ".agents/")
        if target_text != expected:
            errors.append(f"Managed mirror drift: {relative}")


def check_harness() -> list[str]:
    """Return all harness integrity errors; an empty list means valid."""
    errors: list[str] = []
    for relative in REQUIRED_DIRECTORIES:
        if not (ROOT / relative).is_dir():
            errors.append(f"Missing {relative}")
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"Missing {relative}")
    if errors:
        return errors

    gitignore = _read(".gitignore")
    for pattern in (
        ".claude/settings.local.json",
        ".claude/state/",
        ".agents/state/",
        ".agents/settings.local.json",
        "/MEMORY.md",
    ):
        if pattern not in gitignore:
            errors.append(f".gitignore missing '{pattern}'")
    if any(line.strip() == "MEMORY.md" for line in gitignore.splitlines()):
        errors.append(
            ".gitignore must not hide project-scoped subagent MEMORY.md files"
        )

    _validate_settings(errors)
    _validate_skills(errors)
    _validate_agents(errors)
    _validate_mirror(errors)
    return errors


def main() -> int:
    """Print harness audit result and return a process exit code."""
    errors = check_harness()
    if errors:
        print("Harness check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Harness check passed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
