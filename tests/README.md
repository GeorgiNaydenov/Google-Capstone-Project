# tests — Test Suite

pytest test suite for the Nexus Clinical AI Command Center. Tests are organized by concern and designed to pass without a `GOOGLE_API_KEY` — model-dependent tests are skipped automatically when credentials are unavailable.

---

## Test Modules

| Module | Requires API Key | Description |
|--------|:---:|-------------|
| `test_security.py` | No | PII detection, secret scanning, unicode sanitization, injection pattern matching — all pure functions |
| `test_callbacks.py` | No | ADK security callback wiring — verifies callbacks block/allow correctly |
| `test_tools.py` | No | Tool input/output validation with Pydantic contracts |
| `test_context.py` | No | Context engineering — token estimation, history compaction, boundary injection |
| `test_memory.py` | No | Memory governance, PII redaction before persistence, session service creation |
| `test_orchestration.py` | No | Pipeline construction — verifies all 16 agents are wired correctly |
| `test_clinical_tools.py` | No | Clinical-specific tool validation and database operations |
| `test_clinical_api.py` | No | FastAPI endpoint integration tests |
| `test_document_parsing.py` | No | Document upload validation and parsing |
| `test_product_integration.py` | No | End-to-end product workflow tests |
| `test_product_orchestration.py` | No | Orchestration plan generation tests |
| `test_agent_eval.py` | Yes | Agent behavior tests — conversation flow, injection blocking, multi-turn state |
| `test_eval.py` | Yes | ADK `AgentEvaluator` integration — runs the eval set from `eval/` |

---

## Configuration

### conftest.py

Shared fixtures for all test modules:

- `session_service` — Fresh in-memory session service per test
- `memory_service` — Fresh in-memory memory service per test
- `runner` — ADK Runner wired to root agent, session, and memory
- `session_id` — Unique session ID per test
- `get_agent_response()` — Helper to send a query and collect the final response

### pytest.ini

```ini
[pytest]
asyncio_mode = auto          # All async tests run under asyncio
testpaths = tests            # Test discovery directory
filterwarnings = ignore::UserWarning
```

---

## Running

```powershell
# Full suite (model tests skip without API key)
pytest tests/ -v

# Individual modules
pytest tests/test_security.py -v
pytest tests/test_callbacks.py -v
pytest tests/test_tools.py -v

# With coverage
pytest tests/ -v --cov=capstone_agent --cov-report=html
```

---

## Testing Philosophy

- **System contracts over output content** — Assert types, status codes, and state changes, not LLM text
- **LLM non-determinism** — Never assert on exact LLM output. Content quality evaluation uses `adk eval`, not pytest
- **Model-gated tests** — Use `@requires_model` marker for tests needing `GOOGLE_API_KEY`
- **Pure function testing** — Security, context, and validation modules are tested with pure functions (no mocking needed)
