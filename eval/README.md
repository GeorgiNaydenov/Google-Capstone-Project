# eval — ADK Evaluation Suite

Evaluation cases and scoring criteria for the Clinical AI Command Center using Google ADK's built-in `AgentEvaluator`.

---

## Files

| File | Purpose |
|------|---------|
| `capstone.evalset.json` | Evaluation set with conversation cases covering routing, clinical workflows, security, MCP tool usage, and memory |
| `test_config.json` | Scoring criteria and pass thresholds |

---

## Evaluation Cases

The eval set (`capstone.evalset.json`) covers:

- **Greeting / no-tools** — Agent responds without calling tools
- **Image extraction routing** — Correct pipeline delegation with expected tool trajectory
- **Patient Q&A routing** — Evidence-cited answers with correct tool calls
- **Database intelligence routing** — SQL generation, safety validation, execution
- **Injection blocking** — Prompt injection attempts are blocked by security layer
- **Multi-turn state** — Session state persists across conversation turns
- **MCP tool usage** — MCP tools are called correctly via the protocol

---

## Scoring Criteria

From `test_config.json`:

```json
{
  "criteria": {
    "tool_trajectory_avg_score": 1.0,
    "response_match_score": 0.3
  }
}
```

- **`tool_trajectory_avg_score`** (threshold: 1.0) — Did the agent call the right tools in the right order?
- **`response_match_score`** (threshold: 0.3) — Does the response semantically match the expected output? (Low threshold accounts for LLM non-determinism)

---

## Running

Requires `GOOGLE_API_KEY` to be set.

```powershell
adk eval capstone_agent eval/capstone.evalset.json \
  --config_file_path eval/test_config.json \
  --print_detailed_results
```

The evaluation runs each conversation case through the agent, compares tool trajectories and response quality, and reports pass/fail per case.
