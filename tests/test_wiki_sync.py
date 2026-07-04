"""Unit tests for the deterministic wiki sync script (scripts/sync_wiki.py).

Pure-function tests only — no model, no API key, no network. The sync script
is harness tooling, so these tests import it directly from scripts/ and
exercise the marker replacement, docstring extraction, and change-detection
helpers that the Stop hook relies on.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import sync_wiki


def test_replace_between_preserves_surrounding_text():
    """Only the region inside the markers changes; prose around it stays."""
    text = "before\n<!-- B -->\nold body\n<!-- E -->\nafter"
    out = sync_wiki.replace_between(text, "<!-- B -->", "<!-- E -->", "new body")
    assert out.startswith("before\n")
    assert out.endswith("\nafter")
    assert "new body" in out
    assert "old body" not in out


def test_replace_between_missing_markers_raises():
    """A page without markers must raise so the caller can log drift."""
    try:
        sync_wiki.replace_between("no markers here", "<!-- B -->", "<!-- E -->", "x")
    except ValueError as exc:
        assert "markers not found" in str(exc)
    else:
        raise AssertionError("expected ValueError for missing markers")


def test_first_docstring_line_extracts_summary(tmp_path):
    """The first docstring line becomes the module purpose."""
    mod = tmp_path / "sample.py"
    mod.write_text('"""One line summary.\n\nDetails."""\nX = 1\n', encoding="utf-8")
    assert sync_wiki.first_docstring_line(mod) == "One line summary."


def test_first_docstring_line_handles_missing_docstring(tmp_path):
    """Modules without a docstring get a stable placeholder, not an error."""
    mod = tmp_path / "bare.py"
    mod.write_text("X = 1\n", encoding="utf-8")
    assert sync_wiki.first_docstring_line(mod) == "(no docstring)"


def test_write_if_changed_is_idempotent(tmp_path):
    """Rewriting identical content (modulo volatile lines) is a no-op."""
    page = tmp_path / "note.md"
    first = "updated: 2026-01-01\nbody line\n"
    assert sync_wiki.write_if_changed(page, first) is True
    # Same body, different timestamp: must NOT rewrite (keeps diffs clean).
    second = "updated: 2026-12-31\nbody line\n"
    assert sync_wiki.write_if_changed(page, second) is False
    assert "2026-01-01" in page.read_text(encoding="utf-8")
    # Changed body: must rewrite.
    third = "updated: 2026-12-31\ndifferent body\n"
    assert sync_wiki.write_if_changed(page, third) is True


def test_build_depgraph_mermaid_is_deterministic():
    """Two builds over the same tree emit byte-identical Mermaid."""
    assert sync_wiki.build_depgraph_mermaid() == sync_wiki.build_depgraph_mermaid()


def test_parse_model_tiers_finds_registry():
    """MODEL_TIERS keys in llm.py are discovered for the MEMORY.md registers."""
    tiers = sync_wiki.parse_model_tiers()
    assert "flash-lite" in tiers
