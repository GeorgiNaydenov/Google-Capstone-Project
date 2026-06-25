---
name: testing-workflow
description: Add, update, or run pytest unit/behavioral/security tests, and manage evaluation runs using `adk eval` on the Google Capstone Project. Use when adding tests, modifying tools, changing security callbacks, or running evaluations.
---

# Testing Workflow

## When to Use

Use when testing tools, verifying callbacks, checking unicode sanitization/PII/secret filters, running test suites, or running the Agent Platform evaluations.

## Core Workflow

1. Read `.agents/rules/testing.md` (testing rules, LLM non-determinism constraint).
2. If modifying a tool, check input constraints in `capstone_agent/tools.py` or MCP tools in `mcp_server/server.py`.
3. Add/update tests in `tests/test_tools.py` or `tests/test_agent_eval.py` to cover system boundaries and constraints.
4. Run targeted tests first:
   ```bash
   pytest tests/test_security.py -v     # Pure regex/unicode checks
   pytest tests/test_callbacks.py -v    # Callback logic
   pytest tests/test_tools.py -v        # Custom tool inputs
   ```
5. Run the full pytest suite:
   ```bash
   pytest tests/ -v
   ```
6. Run evaluation to validate response quality and LLM behavior (requires `GOOGLE_API_KEY`):
   ```bash
   adk eval capstone_agent eval/capstone.evalset.json --config_file_path eval/test_config.json --print_detailed_results
   ```
7. Verify all runs pass and report back.

## Constraints

- Never assert on specific phrasing, persona, or tone in pytest (non-deterministic).
- Skip model-dependent tests in CI if `GOOGLE_API_KEY` is not set.
- Before committing, run `$root = git rev-parse --show-toplevel`, then
  `python (Join-Path $root 'scripts/check_harness.py')` so the audit works from
  any project subdirectory.
