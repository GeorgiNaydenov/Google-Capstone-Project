---
name: obsidian-cli
description: Interact with Obsidian vaults using the Obsidian CLI to read, create, search, and manage notes, tasks, properties, and more. Also supports plugin and theme development. Use when the user asks to interact with their Obsidian vault, manage notes, search vault content, perform vault operations from the command line, or develop and debug Obsidian plugins and themes.
---

# Obsidian CLI Skill

Use `obsidian` CLI command options.

## Syntax

Parameters accept values with `=`. Flags are boolean.

```bash
obsidian create name="My Note" content="Hello world" silent overwrite
obsidian read file="My Note"
obsidian append file="My Note" content="New line"
obsidian search query="search term" limit=10
```
