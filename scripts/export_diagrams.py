"""Export Project Wiki draw.io diagrams into frontend public assets.

This script is intentionally unhooked: run it when the wiki diagrams change.
It uses only the standard library plus the local draw.io desktop CLI.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Project Wiki" / "02 Architecture" / "diagrams"
PUBLIC = ROOT / "frontend" / "public" / "diagrams"
SVG_OUT = PUBLIC / "svg"

C4_PAGES = {
    "02-c4-p1": 1,
    "02-c4-p2": 2,
    "02-c4-p3": 3,
}


def resolve_drawio() -> str:
    configured = os.environ.get("DRAWIO_CLI")
    candidates = [
        configured,
        shutil.which("drawio"),
        shutil.which("draw.io"),
        r"C:\Program Files\draw.io\draw.io.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise SystemExit(
        "draw.io CLI not found. Set DRAWIO_CLI or install draw.io desktop."
    )


def copy_static_assets() -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    SVG_OUT.mkdir(parents=True, exist_ok=True)
    for pattern in ("*.png", "*.drawio"):
        for source in SOURCE.glob(pattern):
            shutil.copy2(source, PUBLIC / source.name)
    animated = SOURCE / "29-animated-chat-flow.svg"
    if animated.exists():
        shutil.copy2(animated, SVG_OUT / animated.name)


def run(command: list[str], dry_run: bool) -> None:
    print(" ".join(f'"{part}"' if " " in part else part for part in command))
    if not dry_run:
        subprocess.run(command, check=True)


def export_svgs(drawio: str, dry_run: bool) -> None:
    for source in sorted(SOURCE.glob("*.drawio")):
        if source.name == "02-c4-model.drawio":
            for output_stem, page_index in C4_PAGES.items():
                run(
                    [
                        drawio,
                        "-x",
                        "-f",
                        "svg",
                        "-e",
                        "--page-index",
                        str(page_index),
                        "-o",
                        str(SVG_OUT / f"{output_stem}.svg"),
                        str(source),
                    ],
                    dry_run,
                )
            continue
        run(
            [
                drawio,
                "-x",
                "-f",
                "svg",
                "-e",
                "-o",
                str(SVG_OUT / f"{source.stem}.svg"),
                str(source),
            ],
            dry_run,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print commands without executing draw.io",
    )
    args = parser.parse_args()
    drawio = resolve_drawio()
    copy_static_assets()
    export_svgs(drawio, args.dry_run)


if __name__ == "__main__":
    main()
