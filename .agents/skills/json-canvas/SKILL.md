---
name: json-canvas
description: Create and edit JSON Canvas files (.canvas) with nodes, edges, groups, and connections. Use when working with .canvas files, creating visual canvases, mind maps, flowcharts, or when the user mentions Canvas files in Obsidian.
---

# JSON Canvas Skill

## File Structure

A canvas file (`.canvas`) contains two top-level arrays:
```json
{
  "nodes": [],
  "edges": []
}
```

## Common Workflows

1. **Create a New Canvas**: Base layout `{"nodes": [], "edges": []}`.
2. **Add a Node**: Generate unique 16-character hex IDs (e.g. `"6f0ad84f44ce9c17"`). Position them using `x`, `y`, `width`, `height`.
3. **Connect Two Nodes**: Reference node IDs via `fromNode` and `toNode` on edges.

## Node Types

- **text**: Contains markdown text.
- **file**: Reference vault files.
- **link**: External link nodes.
- **group**: Container group organize nodes.
