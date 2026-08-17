# Memory Layers

> Sources: Antigravity, 2026-07-05
> Raw: [Memory Layers Source](../../raw/security-memory/2026-07-04-memory-layers.md)

# Memory Layers

Four-layer memory system with automatic PII/PHI redaction before anything persists.

| Layer | Module | Scope | Persistence |
|-------|--------|-------|-------------|
| 1. Working Memory | `context.py` | Per LLM call | Never |
| 2. Session State | ADK `session.state` | Per conversation | With DB-backed service |
| 3. Long-Term Memory | `memory.py` → MemoryService | Cross-session | With Vertex AI Memory Bank |
| 4. A2A Context | `prepare_a2a_context` → RemoteA2aAgent | Per delegation | Never |

## Layer 1 — Working Memory (context engineering)

`context.py` assembles the per-call context window. It never calls the LLM — compaction is rule-based (truncation + metadata preservation).

| Function | Purpose |
|----------|---------|
| `estimate_tokens(text)` | chars/4 heuristic for budget decisions (no tokenizer) |
| `build_structured_context(role, environment, task, constraints)` | XML-delimited sections so the model separates instructions from data |
| `compact_history(turns, keep_recent=10, max_total_tokens=8000)` | Summarizes old turns to metadata, preserves recent verbatim; append-only (returns new list) |
| `inject_at_boundaries(context, critical_info)` | Places critical info at start AND end ("lost in the middle" mitigation) |

Token pipeline: Collect → Rank → Compress → Budget → Assemble. `config.deterministic_json()` (sorted keys, compact separators) improves KV-cache hits.

## Layer 2 — Session State

- `output_key` plumbing carries data between pipeline stages — see [[Agent Architecture]].
- State prefixes: no prefix (session), `user:` (cross-session), `app:` (global), `temp:` (invocation-only, never persisted). Layer 2 rate limiting uses `temp:` state ([[Security Layers]]).

## Layer 3 — Long-Term Memory

- `InMemoryMemoryService` (dev) / `VertexAiMemoryBankService` (prod), selected by environment in `memory.py`.
- Auto-saved via `after_agent_callback` when sessions complete.
- **PHI filtered before storage** (`detect_phi` + `redact_phi`).
- Written by pipeline audit stages: `save_qa_to_memory`, `save_query_to_memory`; recalled by the orchestrator via `search_past_conversations`.

## Layer 4 — A2A Context

Only task-relevant, non-sensitive data crosses agent boundaries: no PII/PHI, no secrets, no `temp:`/`user:` keys. Used by `RemoteA2aAgent` delegations — see [[MCP and A2A]].

Related: [[Security Layers]] · [[Testing and Eval]] (test_memory.py, test_context.py)
