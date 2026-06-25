---
name: defuddle
description: Extract clean markdown content from web pages using Defuddle CLI, removing clutter and navigation to save tokens. Use when the user or agent needs to fetch and parse external URLs, documentation, or online articles. Do NOT use for URLs ending in .md.
---

# Defuddle

Use Defuddle CLI to parse web page links into clean markdown content. This saves tokens and removes unwanted ads, headers, and footer blocks.

Install globally: `npm install -g defuddle`

## Usage

Extract markdown:
```bash
defuddle parse <url> --md
```

Write to a file:
```bash
defuddle parse <url> --md -o content.md
```

Extract properties:
```bash
defuddle parse <url> -p title
defuddle parse <url> -p description
```
