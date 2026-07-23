# Sync Agents MD

Incrementally mirror managed files under `.agents/` to `.agents/` and generate
`AGENTS.md` from `CLAUDE.md`. Destination-only `.agents` assets are preserved.

## Run

```powershell
python scripts/sync_harness.py
python scripts/check_harness.py
```
