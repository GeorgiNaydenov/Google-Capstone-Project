# mcp_server — Model Context Protocol Server

A **FastMCP** server providing clinical data tools over the [Model Context Protocol](https://modelcontextprotocol.io/) (JSON-RPC 2.0). Any MCP-compatible client — ADK, Claude Desktop, or other frameworks — can discover and use these tools.

---

## Architecture

The MCP server connects to the clinical SQLite database and exposes patient data, document management, database queries, and audit logging through standardized MCP tool interfaces.

```
MCP Client (ADK agent, Claude Desktop, etc.)
     │ stdio (JSON-RPC 2.0)
     ▼
┌──────────────────────────────────┐
│  FastMCP Server (server.py)      │
│  ├── Patient data tools          │
│  ├── Document tools              │
│  ├── Database query tools        │
│  └── Audit logging tools         │
│           │                      │
│           ▼                      │
│  SQLite clinical database        │
└──────────────────────────────────┘
```

---

## Available Tools

| Tool | Description |
|------|-------------|
| `get_patient_status` | Get current clinical status and risk level for a patient |
| `list_patients` | List all patients with optional filtering |
| `get_patient_record` | Get full patient record with sessions and history |
| `list_extraction_sessions` | List extraction sessions for a patient |
| `store_extraction_result` | Store structured extraction results from a pipeline |
| `query_clinical_database` | Execute validated SQL queries against clinical data |
| `log_clinical_audit` | Write audit events to the persistent audit log |
| `upload_document` | Upload and process a clinical document |
| `search_all_documents` | Search across all uploaded documents |
| `list_documents` | List all documents with metadata |

---

## Running

```powershell
# Standalone (stdio mode)
python -m mcp_server.server

# Via ADK (automatic — configured in agent.py)
# ADK connects via StdioConnectionParams at agent initialization
```

The server is automatically started by the ADK agent via `StdioConnectionParams` in `capstone_agent/agent.py`. No manual startup is needed when using the agent.

---

## Integration with ADK

In `agent.py`, the MCP server is connected via:

```python
mcp_tools = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=["-m", "mcp_server.server"],
        ),
        timeout=30,
    ),
    tool_filter=["get_patient_status", "list_patients", ...],
)
```

The `tool_filter` restricts which MCP tools are exposed to the agent, following the principle of least privilege.

---

## SQL Safety

All database queries go through `clinical_schemas.validate_sql()` before execution, which blocks destructive operations (DROP, DELETE, ALTER) and restricts queries to allowed tables.
