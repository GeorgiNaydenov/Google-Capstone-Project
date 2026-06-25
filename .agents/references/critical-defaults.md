# Critical Defaults

Always-on behaviors for the agent.

- **Apply brevity rules**: Always format conversations using Caveman-Micro style unless exceptions trigger.
- **Treat MEMORY.md as context**: Read Developer Agent Memory at the start of a session.
- **Run the Pre-Commit Gate**: Ensure all format, check, and test scripts pass successfully.
- **Redact secrets**: Ensure any variables, tokens, or environment outputs are redacted.
- **Maintain CLAUDE.md and AGENTS.md sync**: Always execute the sync script when editing rules, commands, or index files.
