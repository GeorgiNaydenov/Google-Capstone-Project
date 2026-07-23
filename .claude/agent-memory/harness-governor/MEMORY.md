# Harness Governor Memory

- `.claude` is canonical; `.agents` is incremental portable mirror.
- Destination-only `.agents` skills and assets must survive synchronization.
- Hook scripts use only standard library so session startup works before env setup.
