# DB Intelligence Pipeline

> Sources: Antigravity, 2026-07-05
> Raw: [DB Intelligence Pipeline Source](../../raw/processes/2026-07-04-db-intelligence-pipeline.md)

# DB Intelligence Pipeline

SequentialAgent (6 agents) translating natural language into safe SQL with validation before execution and chart-spec generation after. Lanes: Agents, Safety Gate.

```mermaid
flowchart TD
    subgraph LANE_AG["Lane: Pipeline agents"]
        SD["schema_discovery_agent (flash-lite)<br/>get_database_schema"]
        NL["nl_to_sql_agent (pro)<br/>generate_sql"]
        EX["query_executor_agent (pro-customtools)"]
        IC["insight_chart_agent (flash-lite)<br/>generate_chart_spec, save_query_to_memory"]
    end

    subgraph LANE_GATE["Lane: Safety gate"]
        SV{sql_validator_agent (flash-lite)<br/>validate_sql_safety}
        APPR{Approval boundary<br/>approve_sql_preview}
    end

    START([Natural-language question]) --> SD --> NL --> SV
    SV -->|unsafe| REJ([Rejected + logged])
    SV -->|safe| APPR
    APPR -->|direct| RUN["execute_clinical_query"]
    APPR -->|preview approved| RUN2["execute_approved_clinical_query"]
    RUN --> IC
    RUN2 --> IC
    IC --> DONE([Table / chart / CSV export + history + audit])
```

Key facts:

- SQL never executes without passing `validate_sql_safety`; the product exposes a **read-only SQL preview with an explicit execution boundary** ([[Problem & Solution]]).
- The executor is `pro-customtools` tier; generation is `pro` tier ([[Model Registry]]).
- Results feed `generate_chart_spec` for visual output, and the query is persisted to memory (`save_query_to_memory`) for later recall.
- Schema and query engine live in `clinical_schemas.py` and `database.py` ([[Module Reference]]).

Related: [[Agent Architecture]] · [[End-to-End Request Flow]]
