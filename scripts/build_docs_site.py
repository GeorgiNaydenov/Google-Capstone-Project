#!/usr/bin/env python3
"""Build the standalone documentation hub served at /documentation.

Compiles the Karpathy LLM Wiki (``wiki/``) and the Obsidian Project Wiki
(``Project Wiki/``) into plain, readable HTML pages under ``docs_site/``,
plus a hub index that also links the interactive API documentation
(Swagger, ReDoc, OpenAPI JSON, and the in-app API console). The pages are
deliberately separate from the React application: they share the deployed
origin but load no app code, so a reviewer can simply read.

Deterministic and idempotent: same inputs produce byte-identical outputs.
Run manually after editing wiki content:

    python scripts/build_docs_site.py
"""

from __future__ import annotations

import html
import re
import shutil
from pathlib import Path

from markdown_it import MarkdownIt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LLM_WIKI_ROOT = PROJECT_ROOT / "wiki"
OBSIDIAN_ROOT = PROJECT_ROOT / "Project Wiki"
OUTPUT_ROOT = PROJECT_ROOT / "frontend" / "public" / "documentation"

SKIP_DIRS = {".obsidian", "diagrams"}

CSS = """
:root { --ink: #1e293b; --muted: #64748b; --line: #e2e8f0; --accent: #1d4ed8; --bg: #f8fafc; --panel: #ffffff; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink); font: 16px/1.65 Inter, system-ui, -apple-system, "Segoe UI", sans-serif; }
.doc-topbar { position: sticky; top: 0; z-index: 10; display: flex; align-items: center; gap: 14px; padding: 10px 22px; border-bottom: 1px solid var(--line); background: #ffffffee; backdrop-filter: blur(8px); }
.doc-topbar img { width: 26px; height: 26px; object-fit: contain; }
.doc-topbar .crumb { display: flex; align-items: center; gap: 8px; min-width: 0; color: var(--muted); font-size: 14px; }
.doc-topbar .crumb a { color: var(--accent); text-decoration: none; font-weight: 600; }
.doc-topbar .crumb a:hover { text-decoration: underline; }
.doc-topbar .spacer { flex: 1; }
.doc-topbar .actions { display: flex; gap: 8px; }
.doc-topbar .actions a { display: inline-flex; align-items: center; height: 34px; padding: 0 14px; border-radius: 6px; font-size: 13.5px; font-weight: 600; text-decoration: none; }
.doc-topbar .actions a.ghost { border: 1px solid var(--line); color: var(--ink); background: var(--panel); }
.doc-topbar .actions a.primary { background: var(--accent); color: #fff; }
main { max-width: 880px; margin: 0 auto; padding: 34px 22px 80px; }
main h1 { font-size: 30px; line-height: 1.25; margin: 0 0 6px; }
main h2 { margin-top: 2.1em; padding-bottom: 6px; border-bottom: 1px solid var(--line); font-size: 22px; }
main h3 { margin-top: 1.7em; font-size: 18px; }
main a { color: var(--accent); }
main img { max-width: 100%; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
main code { background: #eef2f7; border-radius: 4px; padding: 1px 5px; font: 13.5px/1.5 "JetBrains Mono", ui-monospace, monospace; }
main pre { overflow-x: auto; padding: 14px 16px; border: 1px solid var(--line); border-radius: 8px; background: #0f172a; color: #e2e8f0; }
main pre code { background: transparent; color: inherit; padding: 0; }
main table { width: 100%; border-collapse: collapse; margin: 1.2em 0; font-size: 14.5px; }
main th, main td { padding: 8px 10px; border: 1px solid var(--line); text-align: left; vertical-align: top; }
main th { background: #f1f5f9; }
main blockquote { margin: 1.2em 0; padding: 8px 16px; border-left: 3px solid var(--accent); background: #eff6ff; border-radius: 0 6px 6px 0; color: #334155; }
.hub-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin-top: 26px; }
.hub-card { display: block; padding: 20px; border: 1px solid var(--line); border-radius: 10px; background: var(--panel); text-decoration: none; color: var(--ink); box-shadow: 0 1px 2px rgba(15,23,42,.05); }
.hub-card:hover { border-color: var(--accent); box-shadow: 0 6px 18px rgba(29,78,216,.12); }
.hub-card h2 { margin: 0 0 8px; border: 0; padding: 0; font-size: 18px; color: var(--accent); }
.hub-card p { margin: 0; color: var(--muted); font-size: 14px; }
.hub-card small { display: block; margin-top: 12px; color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: .04em; }
.section-list { list-style: none; margin: 8px 0 0; padding: 0; }
.section-list li { border-bottom: 1px solid var(--line); }
.section-list a { display: flex; justify-content: space-between; gap: 14px; padding: 10px 4px; text-decoration: none; }
.section-list a:hover { background: #f1f5f9; }
.section-list span { color: var(--muted); font-size: 13.5px; }
.doc-footer { margin-top: 60px; padding-top: 18px; border-top: 1px solid var(--line); color: var(--muted); font-size: 13.5px; display: flex; gap: 14px; flex-wrap: wrap; }
.doc-footer a { color: var(--accent); text-decoration: none; }
@media (max-width: 640px) { .doc-topbar { flex-wrap: wrap; padding: 10px 14px; } main { padding: 24px 14px 60px; } main h1 { font-size: 24px; } }
"""


def md_renderer() -> MarkdownIt:
    """Create the markdown renderer with GFM-style tables and strikethrough."""

    return MarkdownIt("commonmark").enable(["table", "strikethrough"])


def page(title: str, body: str, depth: int) -> str:
    """Wrap rendered content in the shared standalone documentation shell."""

    root = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} · Nexus Documentation</title>
<link rel="icon" href="/favicon.png">
<link rel="stylesheet" href="{root}docs.css">
</head>
<body>
<header class="doc-topbar">
  <a href="/" title="Back to the Nexus Clinical AI Command Center"><img src="/favicon.png" alt="Nexus home"></a>
  <span class="crumb"><a href="{root}index.html">Documentation hub</a>&nbsp;/&nbsp;{html.escape(title)}</span>
  <span class="spacer"></span>
  <nav class="actions">
    <a class="ghost" href="/">Back to main page</a>
    <a class="primary" href="/roles">Enter the application</a>
  </nav>
</header>
<main>
{body}
<footer class="doc-footer">
  <a href="{root}index.html">Documentation hub</a>
  <a href="/">Product landing</a>
  <a href="/roles">Enter the application</a>
  <a href="/docs">Swagger API console</a>
  <a href="/redoc">ReDoc API reference</a>
</footer>
</main>
</body>
</html>
"""


def strip_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block if present."""

    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].lstrip("\n")
    return text


def first_heading(text: str, fallback: str) -> str:
    """Return the first H1 text or a fallback title."""

    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def build_tree(source: Path, destination: Path, renderer: MarkdownIt, link_index: dict[str, str], wikilinks: bool) -> list[tuple[str, str]]:
    """Convert one markdown tree to HTML pages; return (title, relative_href) rows."""

    pages: list[tuple[str, str]] = []
    for path in sorted(source.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        relative = path.relative_to(source)
        out_path = destination / relative.with_suffix(".html")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        text = strip_frontmatter(path.read_text(encoding="utf-8"))
        title = first_heading(text, relative.stem)
        depth = len(out_path.relative_to(OUTPUT_ROOT).parts) - 1

        if wikilinks:
            def replace_wikilink(match: re.Match[str]) -> str:
                target, _, label = match.group(1).partition("|")
                target = target.split("#")[0].strip()
                label = (label or target).strip()
                href = link_index.get(target.casefold())
                if href:
                    encoded = ("../" * depth + href).replace(" ", "%20")
                    return f"[{label}]({encoded})"
                return label
            text = re.sub(r"(?<!\!)\[\[([^\]]+)\]\]", replace_wikilink, text)
            # Embedded images and file transclusions render as plain references.
            text = re.sub(r"\!\[\[([^\]]+)\]\]", lambda match: f"`{match.group(1)}`", text)
            # Obsidian callouts render as titled blockquotes.
            text = re.sub(r"^>\s*\[!(\w+)\][-+]?\s*(.*)$", lambda match: f"> **{match.group(1).title()}:** {match.group(2)}", text, flags=re.MULTILINE)

        # Relative .md links become .html links inside the same tree.
        text = re.sub(r"\(([^)\s]+)\.md(#[^)\s]*)?\)", lambda match: f"({match.group(1)}.html{match.group(2) or ''})", text)
        # Image links into the wiki diagrams folder resolve to the app's
        # public diagram assets, which the same origin already serves.
        text = re.sub(r"\((?:\.\./)*(?:02 Architecture/)?diagrams/([^)\s]+)\)", lambda match: f"(/diagrams/{match.group(1)})", text)

        body = renderer.render(text)
        out_path.write_text(page(title, body, depth), encoding="utf-8", newline="\n")
        pages.append((title, str(out_path.relative_to(destination)).replace("\\", "/")))
    return pages


def obsidian_link_index(destination_prefix: str) -> dict[str, str]:
    """Map Obsidian note names to their generated page hrefs (hub-relative)."""

    index: dict[str, str] = {}
    for path in sorted(OBSIDIAN_ROOT.rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        relative = path.relative_to(OBSIDIAN_ROOT).with_suffix(".html")
        index[path.stem.casefold()] = f"{destination_prefix}/{str(relative).replace(chr(92), '/')}"
    return index


def section_list(rows: list[tuple[str, str]], prefix: str) -> str:
    """Render a linked page list for the hub index."""

    items = "\n".join(
        f'<li><a href="{prefix}/{href}"><strong>{html.escape(title)}</strong><span>{html.escape(href)}</span></a></li>'
        for title, href in rows
    )
    return f'<ul class="section-list">\n{items}\n</ul>'


def build_hub(llm_pages: list[tuple[str, str]], obsidian_pages: list[tuple[str, str]]) -> None:
    """Write the hub index tying the three documentation forms together."""

    llm_index = next((href for title, href in llm_pages if href.endswith("index.html")), "index.html")
    body = f"""
<h1>Nexus documentation</h1>
<p>Standalone, readable documentation for the Nexus Clinical AI Command Center.
These pages are intentionally separate from the application so you can study the
system without the product shell around you. Use the buttons above to jump back
to the main page or straight into the clinician/admin workspace.</p>
<div class="hub-grid">
  <a class="hub-card" href="llm-wiki/{llm_index}">
    <h2>Karpathy LLM Wiki</h2>
    <p>The compiled knowledge base: one distilled article per topic with summaries,
    stable categories, and an index built for fast reading.</p>
    <small>Compiled from the Obsidian vault</small>
  </a>
  <a class="hub-card" href="project-wiki/Home.html">
    <h2>Obsidian Project Wiki</h2>
    <p>The full engineering vault: architecture notes, process documentation,
    security and memory design, operations runbooks, and generated inventories.</p>
    <small>Source vault, rendered page by page</small>
  </a>
  <a class="hub-card" href="/docs">
    <h2>Interactive API docs (Swagger)</h2>
    <p>Try every V1 and V2 endpoint against the running backend with the themed
    Swagger console.</p>
    <small>Live OpenAPI console</small>
  </a>
  <a class="hub-card" href="/redoc">
    <h2>API reference (ReDoc)</h2>
    <p>The same OpenAPI contract as structured reference reading, organized by
    tag with schemas expanded.</p>
    <small>Live OpenAPI reference</small>
  </a>
  <a class="hub-card" href="/openapi.json">
    <h2>OpenAPI schema (JSON)</h2>
    <p>The machine-readable contract for generators, testing tools, and API
    clients.</p>
    <small>Raw specification</small>
  </a>
  <a class="hub-card" href="/docs-viewer?tab=api_runner">
    <h2>In-app API console</h2>
    <p>The developer console inside the product, with request presets for the
    clinical workflows.</p>
    <small>Opens the application</small>
  </a>
</div>
<h2>Karpathy LLM Wiki articles</h2>
{section_list(llm_pages, "llm-wiki")}
<h2>Obsidian Project Wiki pages</h2>
{section_list(obsidian_pages, "project-wiki")}
"""
    (OUTPUT_ROOT / "index.html").write_text(page("Overview", body, 0), encoding="utf-8", newline="\n")


def main() -> None:
    """Rebuild docs_site/ from the two wiki trees."""

    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)
    (OUTPUT_ROOT / "docs.css").write_text(CSS.strip() + "\n", encoding="utf-8", newline="\n")

    renderer = md_renderer()
    link_index = obsidian_link_index("project-wiki")
    llm_pages = build_tree(LLM_WIKI_ROOT, OUTPUT_ROOT / "llm-wiki", renderer, {}, wikilinks=False) if LLM_WIKI_ROOT.is_dir() else []
    obsidian_pages = build_tree(OBSIDIAN_ROOT, OUTPUT_ROOT / "project-wiki", renderer, link_index, wikilinks=True)
    build_hub(llm_pages, obsidian_pages)
    print(f"docs_site built: {len(llm_pages)} LLM wiki pages, {len(obsidian_pages)} project wiki pages")


if __name__ == "__main__":
    main()
