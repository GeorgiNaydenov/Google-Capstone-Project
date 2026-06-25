# Testing Rules

Immutable. Every behavioral change to code or tools carries test validation.

## pytest Runner & Layout

- **Runner**: Use `uv run pytest` or `pytest`.
- **Layout**: Tests reside in the `tests/` directory:
  - `tests/conftest.py` contains shared fixtures (`runner`, `session_service`, `memory_service`).
  - `tests/test_security.py` asserts unicode sanitization, PII, and secret detection patterns (pure functions, no model/API key required).
  - `tests/test_callbacks.py` asserts ADK callback integrations.
  - `tests/test_tools.py` asserts tool input/output validations.
  - `tests/test_agent_eval.py` tests agent flows (basic conversation, injection blocks, multi-turn state).

## LLM Non-Determinism Constraint

- **NEVER** write pytest tests that assert on the exact semantic output or tone of the LLM (e.g. checking if the response matches a pirate persona or includes a particular phrase).
- LLM outputs are non-deterministic; pytest tests asserting on output content will flake.
- Pytest tests should assert:
  - System contracts (functions return correct types or raise correct errors).
  - Security gates block queries when expected (returning blocked response status).
  - Session state persists correct keys across turns.
- Content, response quality, and reasoning evaluations must be handled via Agent Platform eval metrics (`adk eval`), not pytest.

## Env Configuration
- All pytest tests that invoke the Gemini model must be marked with `@requires_model` (checks `GOOGLE_API_KEY`).
- Tests must pass cleanly when `GOOGLE_API_KEY` is not present, skipping model-dependent cases so CI remains green.
