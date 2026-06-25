# Pre-Commit Gate

Verification commands before making a commit to the Google Capstone Project repository.

## Commands

All commands must run and pass in the exact order. The gate anchors itself to
the repository root, so it is safe to invoke from `frontend/` or any other
project subdirectory.

```powershell
$root = git rev-parse --show-toplevel
Push-Location $root
try {
  # 1. Run harness audit to ensure indexes and folders are synced and valid
  python scripts/check_harness.py

  # 2. Run formatting and linting
  ruff check .
  ruff format --check .

  # 3. Run testing suite (model tests skip without GOOGLE_API_KEY)
  pytest tests/ -v
} finally {
  Pop-Location
}
```

## Troubleshooting Failures

- **Harness check fail**: Set `$root = git rev-parse --show-toplevel`, then run `python (Join-Path $root 'scripts/sync_harness.py')` to rebuild `AGENTS.md` and `.agents/`.
- **Ruff check fail**: Run `ruff check --fix .` and `ruff format .` to fix common style issues.
- **Pytest fail**: Read the error message, identify if it's a security pattern mismatch or callback error, and fix the root cause.
