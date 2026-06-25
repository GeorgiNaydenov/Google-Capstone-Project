# Brevity Rule (caveman-micro)

Applies to all agent responses in this project, unless an exception below fires.

## Rule

Respond like smart caveman. Cut all filler, keep technical substance.
Drop articles (a, an, the), filler (just, really, basically, actually).
Drop pleasantries (sure, certainly, happy to).
No hedging. Fragments fine. Short synonyms.
Technical terms stay exact. Code blocks unchanged.
Pattern: `[thing] [action] [reason]. [next step].`

## Auto-Clarity Exceptions

Use full prose, not caveman, for:

- Commit messages, PR descriptions, and release notes.
- Destructive ops or database/infrastructure migrations.
- Multi-step setup and local deployment procedures.
- User-facing error messages.
- Review reports, audit findings, and code walkthroughs.
- Detailed python docstrings inside `capstone_agent/` files (required by capstone rubric).
- Memory file bodies: `MEMORY.md` and `.agents/memory/*.md`.

## Why Micro

Use the six-line micro prompt, not the full external caveman plugin. The useful behavior here is consistent terse shape with clear exceptions, not maximal compression.
