"""Repository safety gate for public source and commit metadata.

The scanner is intentionally conservative: fixture values used to test security
detectors must be built from fragments at runtime, not committed as raw
secret-shaped strings that GitHub may flag or CI may print.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAFE_ROOT = str(ROOT).replace("\\", "/")
MAX_BYTES = 2_000_000

SOURCE_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key_header", re.compile(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----")),
    ("openai_style_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{20,}")),
    ("password_assignment", re.compile(r"password\s*[:=]\s*['\"]?\S{6,}", re.IGNORECASE)),
    ("generic_secret_assignment", re.compile(r"secret\s*=\s*['\"]?\S{16,}", re.IGNORECASE)),
]

TEST_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("email_fixture", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("ssn_fixture", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("card_fixture", re.compile(r"\b(?:\d{4}[ -]){3}\d{4}\b")),
    ("phone_fixture", re.compile(r"\b\d{3}-\d{3}-\d{4}\b")),
]

COAUTHOR_PATTERN = re.compile(
    r"Co-Authored-By:.*(?:Claude|Anthropic|noreply@anthropic\.com)",
    re.IGNORECASE,
)

ALLOWLISTED_TEXT = (
    "PROJECT_NUMBER-compute@developer.gserviceaccount.com",
    "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com",
    "github-actions@github.com",
)


def git_lines(args: list[str]) -> list[str]:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={SAFE_ROOT}", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.splitlines()


def tracked_files() -> list[Path]:
    return [ROOT / line for line in git_lines(["ls-files"]) if line.strip()]


def is_text_file(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if len(data) > MAX_BYTES or b"\0" in data:
        return False
    return True


def scan_files() -> list[str]:
    findings: list[str] = []
    for path in tracked_files():
        if not path.exists() or not is_text_file(path):
            continue
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for allowed in ALLOWLISTED_TEXT:
            text = text.replace(allowed, "")
        for label, pattern in SOURCE_SECRET_PATTERNS:
            for match in pattern.finditer(text):
                line = text.count("\n", 0, match.start()) + 1
                findings.append(f"{rel}:{line}: raw {label}")
        if rel.startswith("tests/"):
            for label, pattern in TEST_PII_PATTERNS:
                for match in pattern.finditer(text):
                    line = text.count("\n", 0, match.start()) + 1
                    findings.append(f"{rel}:{line}: raw {label}")
    return findings


def scan_history() -> list[str]:
    findings: list[str] = []
    messages = "\n".join(git_lines(["log", "--all", "--format=%H%x00%B%x00END_COMMIT"]))
    for block in messages.split("\x00END_COMMIT"):
        if not block.strip():
            continue
        commit, _, body = block.partition("\x00")
        if COAUTHOR_PATTERN.search(body):
            findings.append(f"{commit[:12]}: Claude/Anthropic co-author trailer")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan source and history for public leak risks.")
    parser.add_argument("--skip-history", action="store_true", help="Only scan tracked file contents.")
    args = parser.parse_args()

    findings = scan_files()
    if not args.skip_history:
        findings.extend(scan_history())

    if findings:
        print("Source safety check failed:", file=sys.stderr)
        for finding in findings:
            print(f"- {finding}", file=sys.stderr)
        return 1
    print("Source safety check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
