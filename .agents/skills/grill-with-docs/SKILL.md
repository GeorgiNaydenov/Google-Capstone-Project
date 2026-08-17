---
name: grill-with-docs
description: Stress-test a plan against the Google Capstone Project domain language, architecture docs, memory, and code behavior. Use when the user asks to grill a plan with docs, challenge terminology, or align agent design with documented decisions.
---

# Grill With Docs

Challenge the plan against Capstone project design decisions and documented structures.

## Workflow

1. **Explore first**:
   - Read `MEMORY.md` (Developer Agent Context Memory).
   - Read `docs/architecture.md`.
   - Read the existing module configurations (`capstone_agent/config.py`, `capstone_agent/llm.py`).
   - Read existing instructions in `capstone_agent/prompts.py`.
2. **Identify Conflicts**: Call out contradictions between user language, architecture specs, and existing codebase module rules.
3. **Align Callbacks & Security**: Ensure changes follow the 3-layer security callback system in `callbacks.py` and structured logger formats.
4. **Select Right Model Tier**: Ensure agent tier alignment (e.g. flash-lite for simple orchestration, pro for heavy custom tool calling).
5. **Log Decisions**: Record resolved items as they stabilize.
6. **Formulate ADR**: If a choice represents an architectural trade-off, document it in `docs/architecture.md`.

## Constraints

- Use project-specific terminology (e.g. Working Memory, session.state, MemoryService, callbacks, tiers) instead of generic terms.
- Do not propose modifications that violate structural boundaries in the module dependency graph.
- Ask one question per turn.
- Include `Recommended answer:` for every question.
