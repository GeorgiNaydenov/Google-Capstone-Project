# Testing and Eval

> Sources: Antigravity, 2026-07-05
> Raw: [Testing and Eval Source](../../raw/operations/2026-07-04-testing-eval.md)

# Testing and Eval

pytest + pytest-asyncio for system contracts; ADK `AgentEvaluator` for content quality. The live, machine-generated test-count table is [[Test Inventory]].

## Test suite (tests/)

| File | Covers |
|------|--------|
| `conftest.py` | Shared fixtures — runner, session_service, memory_service |
| `test_security.py` | All detection and sanitization functions (pure, no API key) |
| `test_callbacks.py` | 3-layer security callback wiring ([[Security Layers]]) |
| `test_tools.py` | Clinical tool validation — consistent I/O contracts |
| `test_clinical_tools.py` | Clinical tool integration — mock data consistency and HITL |
| `test_clinical_api.py` | Frontend contract tests for the deterministic product API |
| `test_product_integration.py` | End-to-end contracts joining the clinical UI API to product state |
| `test_product_orchestration.py` | Clinician-facing production workflow boundaries |
| `test_document_parsing.py` | Document upload policy and extraction contracts |
| `test_live_bridge.py` | Live-mode ADK bridge parsing helpers |
| `test_context.py` | Context engineering utilities ([[Memory Layers]] Layer 1) |
| `test_memory.py` | Memory governance / PII redaction (Day 3b) |
| `test_orchestration.py` | Workflow primitive construction (Day 1b / 2a) |
| `test_agent_eval.py` | Agent behavior end-to-end (model tests skip without key) |
| `test_eval.py` | ADK evaluation harness (Day 4b, skips without key) |
| `test_wiki_sync.py` | Deterministic wiki sync script ([[Development Workflow]]) |
| `test_showcase_generators.py` | Smoke tests for showcase data generators |
| `test_versioned_api.py` | Unit tests for versioned V1 and V2 API endpoints and Swagger/ReDoc customization |

## Rules

> [!warning] LLM non-determinism constraint
> Never assert on exact semantic output or tone of the LLM in pytest — outputs are non-deterministic and such tests flake. pytest asserts system contracts, security gates, and state persistence. Content quality goes through `adk eval`.

- Runner: `uv run pytest` or `pytest`.
- Model-dependent tests carry `@requires_model` (checks `GOOGLE_API_KEY`) and skip cleanly so CI stays green without credentials.

## Commands

```powershell
pytest tests/ -v                      # full suite
pytest tests/test_security.py -v      # pure functions, no key needed
cd frontend; npm run typecheck; npm test; npm run build
```

## ADK evaluation (Day 4b, requires key)

`eval/capstone.evalset.json` (cases: user_content, final_response, tool_uses) scored by `eval/test_config.json` criteria: `tool_trajectory_avg_score`, `response_match_score`.

```powershell
adk eval capstone_agent eval/capstone.evalset.json --config_file_path eval/test_config.json --print_detailed_results
```

Related: [[Course Concepts Map]] · [[Development Workflow]]
