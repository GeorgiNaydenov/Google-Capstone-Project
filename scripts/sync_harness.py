"""Safely mirror the Claude harness into the cross-agent ``.agents`` tree.

``.claude`` is the executable Claude Code source. ``.agents`` is the portable
mirror used by Codex and other coding agents. Synchronization is incremental:
only files previously managed by this script may be removed, so Codex-specific
skills and vendored assets under ``.agents`` are never deleted accidentally.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAUDE_DIR = ROOT / ".claude"
AGENTS_DIR = ROOT / ".agents"
MANIFEST = AGENTS_DIR / ".sync-manifest.json"
SKIPPED_NAMES = {"settings.local.json", "launch.json"}
SKIPPED_PARTS = {
    "state",
    "agent-memory-local",
    ".git",
    # Local vendored checkout/junction. The portable tracked drawio skill lives
    # directly in .agents and is intentionally destination-owned.
    "drawio-skill",
    "drawio",
}
DESTINATION_ONLY_PREFIXES = ("skills/drawio-skill/", "skills/drawio/")


def _read_manifest() -> set[str]:
    """Return relative paths managed by the previous successful sync."""
    try:
        payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    files = payload.get("files", []) if isinstance(payload, dict) else []
    return {str(path) for path in files if isinstance(path, str)}


def _atomic_write(path: Path, data: bytes) -> None:
    """Atomically write bytes to avoid partial harness files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "wb",
        delete=False,
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    ) as handle:
        handle.write(data)
        temporary = Path(handle.name)
    temporary.replace(path)


def _translate(data: bytes) -> bytes:
    """Translate Claude paths in UTF-8 text while preserving binary assets."""
    try:
        content = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return content.replace(".claude/", ".agents/").encode("utf-8")


def _source_files() -> list[Path]:
    """List syncable source files without following skill junctions."""
    files: list[Path] = []
    for directory, dirnames, filenames in os.walk(CLAUDE_DIR, followlinks=False):
        base = Path(directory)
        relative_dir = base.relative_to(CLAUDE_DIR)
        dirnames[:] = [
            name
            for name in dirnames
            if name not in SKIPPED_PARTS and not (base / name).is_symlink()
        ]
        if any(part in SKIPPED_PARTS for part in relative_dir.parts):
            continue
        for filename in filenames:
            if filename in SKIPPED_NAMES:
                continue
            source = base / filename
            if source.is_symlink():
                continue
            files.append(source)
    return sorted(files)


def _remove_stale(previous: set[str], current: set[str]) -> None:
    """Remove only files named by the previous generated manifest."""
    for relative in sorted(previous - current):
        if relative.startswith(DESTINATION_ONLY_PREFIXES):
            continue
        target = AGENTS_DIR / Path(relative)
        try:
            target.relative_to(AGENTS_DIR)
        except ValueError:
            continue
        if target.is_file():
            target.unlink()


def sync_harness() -> None:
    """Mirror managed harness files and regenerate ``AGENTS.md``."""
    if not CLAUDE_DIR.is_dir():
        raise FileNotFoundError("Required .claude directory not found.")

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    previous = _read_manifest()
    managed: set[str] = set()

    for source in _source_files():
        relative = source.relative_to(CLAUDE_DIR)
        relative_posix = relative.as_posix()
        destination = AGENTS_DIR / relative
        _atomic_write(destination, _translate(source.read_bytes()))
        managed.add(relative_posix)

    _remove_stale(previous, managed)
    manifest = {
        "schema_version": 1,
        "source": ".claude",
        "files": sorted(managed),
    }
    _atomic_write(
        MANIFEST,
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )

    claude_md = ROOT / "CLAUDE.md"
    if not claude_md.is_file():
        raise FileNotFoundError("Required CLAUDE.md not found.")
    translated = claude_md.read_text(encoding="utf-8").replace(".claude/", ".agents/")
    _atomic_write(ROOT / "AGENTS.md", translated.encode("utf-8"))
    print(
        f"Synced {len(managed)} managed files from .claude/ to .agents/ "
        "without deleting destination-only assets."
    )


if __name__ == "__main__":
    sync_harness()
