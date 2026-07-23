# Harness Status

Show current local lifecycle state and recent sanitized handoffs.

```powershell
uv run --no-project --python 3.11 python scripts/harness_runtime.py status
```

Then run
`uv run --no-project --python 3.11 python scripts/check_harness.py`
when structural drift is suspected.
