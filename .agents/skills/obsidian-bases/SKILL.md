---
name: obsidian-bases
description: Create and edit Obsidian Bases (.base files) with views, filters, formulas, and summaries. Use when working with .base files, creating database-like views of notes, or when the user mentions Bases, table views, card views, filters, or formulas in Obsidian.
---

# Obsidian Bases Skill

Create and edit `.base` files using YAML formatting.

## Schema Layout

```yaml
filters:
  and:
    - 'status == "active"'
formulas:
  formula_name: 'expression'
properties:
  property_name:
    displayName: "Display Name"
views:
  - type: table
    name: "View Name"
    order:
      - file.name
      - property_name
```
