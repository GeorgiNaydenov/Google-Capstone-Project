# Security Rules

Immutable. All agent interfaces, callbacks, and data ingestion steps must obey these.

## Callbacks Pipeline (3 Layers)

The safety callback order in `capstone_agent/callbacks.py` is fixed and must be preserved:

1. **Input (before_model_callback)**:
   - `content_safety_callback` sanitizes unicode inputs and runs pattern matching to block 15+ injection and extraction patterns.
   
2. **Tool (before_tool_callback)**:
   - `tool_authorization_callback` rates limits tool usage, performs Pydantic validation on arguments, and scans arguments for secrets before execution.
   
3. **Output (after_model_callback)**:
   - `output_safety_callback` checks model response output for leaked secrets (bearer tokens, API keys) and personal PII, redacting or blocking if found.

## Secrets & PII Scan

- All secret scanning uses pure regular expressions in `capstone_agent/security.py` (`scan_for_secrets`).
- PII detection checks for emails, phone numbers, SSNs, and credit card numbers (`detect_pii`).
- All loggers must route strings through `config.redact_secrets()` before calling debug/info/error.
- Never write API keys or GCP credentials to long-term memory or session storage. Run `redact_pii` before persisting memory layers.
