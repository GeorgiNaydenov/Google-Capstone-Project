# Harness Audit

Runs the deterministic validation script to check files, folders, and settings formatting.

## Run

```powershell
$root = git rev-parse --show-toplevel
python (Join-Path $root 'scripts/check_harness.py')
```
