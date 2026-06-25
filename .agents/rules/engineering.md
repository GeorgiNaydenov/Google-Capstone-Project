# Engineering Rules

Immutable. Every coding action obeys these.

## Language & Style

- Python 3.11+. Strict typing with type hints where applicable. No unused imports.
- Match existing code style exactly — do not refactor surroundings.
- Use structured JSON logging via `observability.py`. No `print()` statements in agent codebase.
- No emojis in code or logs.
- Python docstrings are required for all public classes, functions, and tools to satisfy the capstone rubric. Keep docstrings clear and descriptive.

## Scope Discipline

- A bug fix changes the bug. No surrounding cleanup, no helper extraction, no abstraction for hypothetical future use.
- Three similar lines beats a premature abstraction.
- No new files unless the task requires a new module. Prefer extending an existing file under `capstone_agent/`.
- No validation for scenarios that cannot happen. Trust internal code and framework guarantees. Validate only at system boundaries using Pydantic.

## Model Selection

- Never pass a bare model-id string to ADK LlmAgent. Always use `llm.build_model(tier)` which wraps standard Gemini models with exponential backoff and HTTP retry options.
- The standard model tiers are defined in `capstone_agent/llm.py` (`MODEL_TIERS`). Refer to that mapping; never invent model identifiers.

## Windows / Python commands
- Run commands with `uv` (e.g., `uv run pytest`).
- Use `python` to invoke Python, as `python3` may not be mapped on Windows.
- Stage files specifically by name (e.g., `git add capstone_agent/agent.py`); never run `git add .` or `git add -A` to avoid unstaging env files or committing logs.
- Never commit `.env` values or private keys anywhere.
