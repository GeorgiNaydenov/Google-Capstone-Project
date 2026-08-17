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
  # Keep uv cache project-local in restricted runners. Reuse the healthy
  # execution environment when this workspace has quarantined a stale .venv.
  $env:UV_CACHE_DIR = Join-Path $root '.uv-cache'
  $env:UV_PROJECT_ENVIRONMENT = if (Test-Path (Join-Path $root '.run-venv')) {
    '.run-venv'
  } else {
    '.venv'
  }
  # Tests import the agent and observability stack. Never export local gate
  # spans to Cloud Trace, even when the developer .env enables production tracing.
  $env:ENABLE_TRACING = 'FALSE'
  uv sync --frozen

  # 1. Run harness audit to ensure indexes and folders are synced and valid
  uv run --no-project --python 3.11 python scripts/check_harness.py

  # 2. Block committed secret-shaped fixtures and unsafe co-author trailers
  uv run --no-project --python 3.11 python scripts/check_source_safety.py

  # 3. Run formatting and linting
  uv run ruff check .
  uv run ruff format --check .

  # 4. Run deterministic tests. Live model behavior is the separate ADK eval
  # gate and must never become an accidental, billable pre-commit side effect.
  uv run pytest tests/ -v -m 'not requires_model'
} finally {
  Pop-Location
}
```

## Troubleshooting Failures

- **Harness check fail**: Set `$root = git rev-parse --show-toplevel`, then run `python (Join-Path $root 'scripts/sync_harness.py')` to rebuild `AGENTS.md` and `.agents/`.
- **Ruff check fail**: Run `ruff check --fix .` and `ruff format .` to fix common style issues.
- **Pytest fail**: Read the error message, identify if it's a security pattern mismatch or callback error, and fix the root cause.
