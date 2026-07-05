import React, { useState, useEffect } from "react";
import { api } from "../api";
import { Card, DenseTable, ErrorState, JsonViewer, LoadingState, StatusBadge } from "../components";

interface Endpoint {
  method: "GET" | "POST" | "PUT";
  path: string;
  description: string;
  defaultParams?: Record<string, string>;
  defaultBody?: string;
}

const PRESET_ENDPOINTS: Endpoint[] = [
  { method: "GET", path: "/api/v1/patients", description: "List all patients with risk level and condition info" },
  { method: "GET", path: "/api/v1/patients/PT-8829", description: "Get a specific patient profile by ID" },
  { method: "GET", path: "/api/v1/sessions", description: "List all clinical sessions, optionally filtered by patient_id", defaultParams: { patient_id: "PT-8829" } },
  { method: "GET", path: "/api/v1/dashboard", description: "Retrieve metrics, patients, sessions, and activity logs", defaultParams: { role: "clinician" } },
  { method: "POST", path: "/api/v1/orchestrate", description: "Classify user natural language request and output a workflow plan", defaultBody: JSON.stringify({ query: "show me all patients with high risk of lung cancer", patientId: "PT-8829" }, null, 2) },
  { method: "POST", path: "/api/v1/runs/qa", description: "Execute patient-scoped grounded Q&A", defaultBody: JSON.stringify({ patientId: "PT-8829", question: "What is the primary tumor size?", source_types: ["text", "image"], filters: { dateRange: "30d" } }, null, 2) },
  { method: "POST", path: "/api/v1/runs/database/preview", description: "Generate safe read-only SQL query for population questions", defaultBody: JSON.stringify({ question: "How many patients are active?" }, null, 2) },
  { method: "GET", path: "/api/v2/health", description: "Fetch advanced system health checking database and storage connectivity" },
  { method: "GET", path: "/api/v2/mcp/tools", description: "List all dynamic tools registered on the FastMCP clinical server" },
  { method: "GET", path: "/api/v2/a2a/card", description: "Retrieve Agent Card metadata for Agent-to-Agent discovery" },
];

export function DeveloperConsole() {
  const [activeTab, setActiveTab] = useState<"api_runner" | "mcp_tools" | "a2a_card" | "openapi">("api_runner");

  // API Runner state
  const [selectedEndpoint, setSelectedEndpoint] = useState<Endpoint>(PRESET_ENDPOINTS[0]);
  const [pathParams, setPathParams] = useState<Record<string, string>>({});
  const [queryParams, setQueryParams] = useState<Record<string, string>>({});
  const [requestBody, setRequestBody] = useState<string>("");
  const [customHeaders, setCustomHeaders] = useState<Record<string, string>>({
    "X-Clinical-Role": "admin",
    "X-Tenant": "capstone",
    "X-Demo-Session": "public-demo",
  });

  const [responseStatus, setResponseStatus] = useState<number | null>(null);
  const [responseHeaders, setResponseHeaders] = useState<Record<string, string>>({});
  const [responseData, setResponseData] = useState<any>(null);
  const [responseLatency, setResponseLatency] = useState<number | null>(null);
  const [executing, setExecuting] = useState<boolean>(false);

  // MCP Tools state
  const [mcpLoading, setMcpLoading] = useState<boolean>(false);
  const [mcpError, setMcpError] = useState<string>("");
  const [mcpTools, setMcpTools] = useState<any[]>([]);
  const [selectedMcpTool, setSelectedMcpTool] = useState<any | null>(null);
  const [mcpArguments, setMcpArguments] = useState<string>("{\n  \n}");
  const [mcpExecStatus, setMcpExecStatus] = useState<string>("");
  const [mcpExecResult, setMcpExecResult] = useState<any>(null);
  const [mcpExecuting, setMcpExecuting] = useState<boolean>(false);

  // A2A Card state
  const [a2aLoading, setA2aLoading] = useState<boolean>(false);
  const [a2aError, setA2aError] = useState<string>("");
  const [a2aCard, setA2aCard] = useState<any>(null);

  // OpenAPI state
  const [openapiLoading, setOpenapiLoading] = useState<boolean>(false);
  const [openapiError, setOpenapiError] = useState<string>("");
  const [openapiSchema, setOpenapiSchema] = useState<any>(null);

  // Synchronize preset values when endpoint changes
  useEffect(() => {
    // Extract path params (e.g. {patient_id})
    const pathMatches = selectedEndpoint.path.match(/\{([^}]+)\}/g);
    const initialPaths: Record<string, string> = {};
    if (pathMatches) {
      pathMatches.forEach(match => {
        const paramName = match.replace(/[{}]/g, "");
        initialPaths[paramName] = paramName === "patient_id" ? "PT-8829" : "RUN-001";
      });
    }
    setPathParams(initialPaths);
    setQueryParams(selectedEndpoint.defaultParams || {});
    setRequestBody(selectedEndpoint.defaultBody || "");
    setResponseData(null);
    setResponseStatus(null);
    setResponseLatency(null);
  }, [selectedEndpoint]);

  // Load MCP tools when clicking tab
  const loadMcpTools = async () => {
    setMcpLoading(true);
    setMcpError("");
    try {
      const res = await api.mcpTools();
      setMcpTools(res.tools || []);
      if (res.tools && res.tools.length > 0) {
        setSelectedMcpTool(res.tools[0]);
        // Set sample arguments
        if (res.tools[0].inputSchema && res.tools[0].inputSchema.properties) {
          const props = res.tools[0].inputSchema.properties;
          const sample: Record<string, any> = {};
          Object.keys(props).forEach(key => {
            sample[key] = props[key].default !== undefined ? props[key].default : (props[key].type === "integer" ? 10 : "PT-8829");
          });
          setMcpArguments(JSON.stringify(sample, null, 2));
        } else {
          setMcpArguments("{\n  \n}");
        }
      }
    } catch (e: any) {
      setMcpError(e.message || "Failed to load MCP tools");
    } finally {
      setMcpLoading(false);
    }
  };

  // Load A2A card details
  const loadA2aCard = async () => {
    setA2aLoading(true);
    setA2aError("");
    try {
      const res = await api.a2aCard();
      setA2aCard(res);
    } catch (e: any) {
      setA2aError(e.message || "Failed to load A2A card");
    } finally {
      setA2aLoading(false);
    }
  };

  // Load OpenAPI schema
  const loadOpenApiSchema = async () => {
    setOpenapiLoading(true);
    setOpenapiError("");
    try {
      const res = await api.getOpenApiSchema();
      setOpenapiSchema(res);
    } catch (e: any) {
      setOpenapiError(e.message || "Failed to load OpenAPI schema");
    } finally {
      setOpenapiLoading(false);
    }
  };

  // Handle Tab Switch
  useEffect(() => {
    if (activeTab === "mcp_tools") {
      void loadMcpTools();
    } else if (activeTab === "a2a_card") {
      void loadA2aCard();
    } else if (activeTab === "openapi") {
      void loadOpenApiSchema();
    }
  }, [activeTab]);

  // Execute Preset API Call
  const executeApiCall = async () => {
    setExecuting(true);
    setResponseData(null);
    setResponseStatus(null);
    const startTime = performance.now();

    // Construct url
    let url = selectedEndpoint.path;
    Object.keys(pathParams).forEach(key => {
      url = url.replace(`{${key}}`, encodeURIComponent(pathParams[key]));
    });

    const queryStr = new URLSearchParams(queryParams).toString();
    const fullUrl = url + (queryStr ? `?${queryStr}` : "");

    try {
      const headers = new Headers();
      headers.set("Content-Type", "application/json");
      Object.keys(customHeaders).forEach(key => {
        headers.set(key, customHeaders[key]);
      });

      const response = await fetch(fullUrl, {
        method: selectedEndpoint.method,
        headers,
        body: selectedEndpoint.method !== "GET" && requestBody ? requestBody : undefined,
      });

      const endTime = performance.now();
      setResponseLatency(Math.round(endTime - startTime));
      setResponseStatus(response.status);

      // Extract headers
      const hdrs: Record<string, string> = {};
      response.headers.forEach((val, key) => {
        hdrs[key] = val;
      });
      setResponseHeaders(hdrs);

      const text = await response.text();
      try {
        setResponseData(JSON.parse(text));
      } catch {
        setResponseData(text);
      }
    } catch (e: any) {
      const endTime = performance.now();
      setResponseLatency(Math.round(endTime - startTime));
      setResponseStatus(500);
      setResponseData({ error: e.message || "Failed to fetch" });
    } finally {
      setExecuting(false);
    }
  };

  // Execute MCP Tool
  const runMcpTool = async () => {
    if (!selectedMcpTool) return;
    setMcpExecuting(true);
    setMcpExecResult(null);
    setMcpExecStatus("executing");
    try {
      const parsedArgs = JSON.parse(mcpArguments);
      const res = await api.executeMcpTool(selectedMcpTool.name, parsedArgs);
      setMcpExecResult(res.result);
      setMcpExecStatus("success");
    } catch (e: any) {
      setMcpExecResult({ error: e.message || "Failed to execute MCP tool" });
      setMcpExecStatus("error");
    } finally {
      setMcpExecuting(false);
    }
  };

  // Helper when user selects a different MCP tool
  const selectMcpTool = (tool: any) => {
    setSelectedMcpTool(tool);
    setMcpExecResult(null);
    setMcpExecStatus("");
    if (tool.inputSchema && tool.inputSchema.properties) {
      const props = tool.inputSchema.properties;
      const sample: Record<string, any> = {};
      Object.keys(props).forEach(key => {
        sample[key] = props[key].default !== undefined ? props[key].default : (props[key].type === "integer" ? 10 : "PT-8829");
      });
      setMcpArguments(JSON.stringify(sample, null, 2));
    } else {
      setMcpArguments("{\n  \n}");
    }
  };

  return (
    <div className="developer-console">
      <header className="page-head">
        <div>
          <span className="eyebrow accent">DEVELOPER TOOLING</span>
          <h1>API Command Center</h1>
          <p>Govern, execute, and monitor versioned OpenAPI services, MCP tools, and Agent-to-Agent cards.</p>
        </div>
      </header>

      {/* Tabs */}
      <nav className="tabs">
        <button className={activeTab === "api_runner" ? "active" : ""} onClick={() => setActiveTab("api_runner")}>
          API Endpoint Runner
        </button>
        <button className={activeTab === "mcp_tools" ? "active" : ""} onClick={() => setActiveTab("mcp_tools")}>
          MCP Tools Playground
        </button>
        <button className={activeTab === "a2a_card" ? "active" : ""} onClick={() => setActiveTab("a2a_card")}>
          Agent Card (A2A)
        </button>
        <button className={activeTab === "openapi" ? "active" : ""} onClick={() => setActiveTab("openapi")}>
          OpenAPI Specification
        </button>
      </nav>

      {/* API RUNNER TAB */}
      {activeTab === "api_runner" && (
        <div className="grid api-runner-layout" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
          {/* Controls */}
          <div className="runner-controls-pane">
            <Card title="Request Settings">
              {/* Endpoint selection */}
              <div className="form-group" style={{ marginBottom: "15px" }}>
                <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>Service Endpoint</label>
                <select
                  style={{ width: "100%", padding: "10px", borderRadius: "6px", backgroundColor: "var(--bg-subtle)", color: "var(--fg)", border: "1px solid var(--border)" }}
                  value={PRESET_ENDPOINTS.indexOf(selectedEndpoint)}
                  onChange={e => setSelectedEndpoint(PRESET_ENDPOINTS[Number(e.target.value)])}
                >
                  {PRESET_ENDPOINTS.map((endpoint, i) => (
                    <option key={i} value={i}>
                      {endpoint.method} {endpoint.path} ({endpoint.description})
                    </option>
                  ))}
                </select>
              </div>

              {/* Headers config */}
              <div className="form-group" style={{ marginBottom: "15px" }}>
                <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>Clinical Context Headers</label>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "10px" }}>
                  <div>
                    <small>X-Clinical-Role</small>
                    <input
                      type="text"
                      value={customHeaders["X-Clinical-Role"]}
                      onChange={e => setCustomHeaders({ ...customHeaders, "X-Clinical-Role": e.target.value })}
                      style={{ width: "100%", padding: "8px", borderRadius: "6px" }}
                    />
                  </div>
                  <div>
                    <small>X-Tenant</small>
                    <input
                      type="text"
                      value={customHeaders["X-Tenant"]}
                      onChange={e => setCustomHeaders({ ...customHeaders, "X-Tenant": e.target.value })}
                      style={{ width: "100%", padding: "8px", borderRadius: "6px" }}
                    />
                  </div>
                  <div>
                    <small>X-Demo-Session</small>
                    <input
                      type="text"
                      value={customHeaders["X-Demo-Session"]}
                      onChange={e => setCustomHeaders({ ...customHeaders, "X-Demo-Session": e.target.value })}
                      style={{ width: "100%", padding: "8px", borderRadius: "6px" }}
                    />
                  </div>
                </div>
              </div>

              {/* Path params if any */}
              {Object.keys(pathParams).length > 0 && (
                <div className="form-group" style={{ marginBottom: "15px" }}>
                  <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>Path Parameters</label>
                  {Object.keys(pathParams).map(key => (
                    <div key={key} style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                      <span style={{ minWidth: "100px", fontFamily: "monospace" }}>{key}</span>
                      <input
                        type="text"
                        value={pathParams[key]}
                        onChange={e => setPathParams({ ...pathParams, [key]: e.target.value })}
                        style={{ flex: 1, padding: "8px", borderRadius: "6px" }}
                      />
                    </div>
                  ))}
                </div>
              )}

              {/* Query params if any */}
              {Object.keys(queryParams).length > 0 && (
                <div className="form-group" style={{ marginBottom: "15px" }}>
                  <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>Query Parameters</label>
                  {Object.keys(queryParams).map(key => (
                    <div key={key} style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "8px" }}>
                      <span style={{ minWidth: "100px", fontFamily: "monospace" }}>{key}</span>
                      <input
                        type="text"
                        value={queryParams[key]}
                        onChange={e => setQueryParams({ ...queryParams, [key]: e.target.value })}
                        style={{ flex: 1, padding: "8px", borderRadius: "6px" }}
                      />
                    </div>
                  ))}
                </div>
              )}

              {/* Request Body */}
              {selectedEndpoint.method !== "GET" && (
                <div className="form-group" style={{ marginBottom: "15px" }}>
                  <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>Request Body (JSON)</label>
                  <textarea
                    value={requestBody}
                    onChange={e => setRequestBody(e.target.value)}
                    rows={8}
                    style={{ width: "100%", padding: "10px", borderRadius: "6px", fontFamily: "monospace", backgroundColor: "var(--bg-subtle)", color: "var(--fg)", border: "1px solid var(--border)" }}
                  />
                </div>
              )}

              <button
                className="button primary"
                disabled={executing}
                onClick={executeApiCall}
                style={{ width: "100%", padding: "12px", marginTop: "10px" }}
              >
                {executing ? "Sending HTTP Request..." : `Send V1/V2 ${selectedEndpoint.method} Request`}
              </button>
            </Card>
          </div>

          {/* Response */}
          <div className="runner-response-pane">
            <Card title="Response Inspector">
              {responseStatus === null ? (
                <div style={{ display: "flex", height: "300px", alignItems: "center", justifyContent: "center", color: "var(--fg-muted)" }}>
                  Send a request to see the execution audit and response details.
                </div>
              ) : (
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "15px" }}>
                    <div>
                      <span style={{ marginRight: "10px", fontWeight: "bold" }}>Status:</span>
                      <StatusBadge tone={responseStatus >= 200 && responseStatus < 300 ? "success" : "danger"}>
                        {responseStatus}
                      </StatusBadge>
                    </div>
                    {responseLatency !== null && (
                      <div>
                        <span style={{ marginRight: "10px", fontWeight: "bold" }}>Time:</span>
                        <span>{responseLatency} ms</span>
                      </div>
                    )}
                  </div>

                  <nav className="tabs" style={{ marginBottom: "10px" }}>
                    <button className="active" style={{ fontSize: "0.85em", padding: "5px 10px" }}>JSON Payload</button>
                  </nav>

                  <div style={{ maxHeight: "400px", overflowY: "auto", border: "1px solid var(--border)", borderRadius: "6px" }}>
                    <JsonViewer value={responseData} />
                  </div>

                  <details style={{ marginTop: "15px" }}>
                    <summary style={{ cursor: "pointer", fontWeight: "bold" }}>Response Headers</summary>
                    <pre style={{ fontSize: "0.8em", padding: "10px", backgroundColor: "var(--bg-subtle)", borderRadius: "6px", marginTop: "5px", whiteSpace: "pre-wrap" }}>
                      {JSON.stringify(responseHeaders, null, 2)}
                    </pre>
                  </details>
                </div>
              )}
            </Card>
          </div>
        </div>
      )}

      {/* MCP TOOLS TAB */}
      {activeTab === "mcp_tools" && (
        <div className="grid mcp-tools-layout" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px" }}>
          {/* Tools List */}
          <Card title={`Registered MCP Tools (${mcpTools.length})`}>
            {mcpLoading ? (
              <LoadingState />
            ) : mcpError ? (
              <ErrorState error={new Error(mcpError)} retry={loadMcpTools} />
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxHeight: "500px", overflowY: "auto" }}>
                {mcpTools.map(tool => (
                  <button
                    key={tool.name}
                    className={`role-row ${selectedMcpTool?.name === tool.name ? "active" : ""}`}
                    onClick={() => selectMcpTool(tool)}
                    style={{ width: "100%", textAlign: "left", padding: "12px", border: "1px solid var(--border)", borderRadius: "6px" }}
                  >
                    <strong>{tool.name}</strong>
                    <p style={{ margin: "5px 0 0 0", fontSize: "0.85em", color: "var(--fg-muted)" }}>
                      {tool.description ? tool.description.split("\n")[0] : "No description"}
                    </p>
                  </button>
                ))}
              </div>
            )}
          </Card>

          {/* Execution Playground */}
          <Card title="MCP Playground">
            {selectedMcpTool ? (
              <div>
                <h3>Execute tool: <code>{selectedMcpTool.name}</code></h3>
                <p style={{ fontSize: "0.9em", color: "var(--fg-muted)", whiteSpace: "pre-wrap", margin: "10px 0" }}>
                  {selectedMcpTool.description}
                </p>

                <div className="form-group" style={{ marginTop: "15px" }}>
                  <label style={{ display: "block", marginBottom: "5px", fontWeight: "bold" }}>Input Arguments (JSON)</label>
                  <textarea
                    value={mcpArguments}
                    onChange={() => {}} // dummy change handler
                    onInput={(e: any) => setMcpArguments(e.target.value)}
                    rows={8}
                    style={{ width: "100%", padding: "10px", borderRadius: "6px", fontFamily: "monospace", backgroundColor: "var(--bg-subtle)", color: "var(--fg)" }}
                  />
                </div>

                <button
                  className="button primary"
                  disabled={mcpExecuting}
                  onClick={runMcpTool}
                  style={{ width: "100%", padding: "10px", marginTop: "10px" }}
                >
                  {mcpExecuting ? "Executing MCP Tool..." : `Run MCP ${selectedMcpTool.name}`}
                </button>

                {mcpExecStatus && (
                  <div style={{ marginTop: "20px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "5px" }}>
                      <strong>Execution Result</strong>
                      <StatusBadge tone={mcpExecStatus === "success" ? "success" : "danger"}>
                        {mcpExecStatus.toUpperCase()}
                      </StatusBadge>
                    </div>
                    <div style={{ border: "1px solid var(--border)", borderRadius: "6px", maxHeight: "250px", overflowY: "auto" }}>
                      <JsonViewer value={mcpExecResult} />
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div style={{ display: "flex", height: "300px", alignItems: "center", justifyContent: "center", color: "var(--fg-muted)" }}>
                Select an MCP tool from the list to explore and run it.
              </div>
            )}
          </Card>
        </div>
      )}

      {/* A2A CARD TAB */}
      {activeTab === "a2a_card" && (
        <Card title="Agent Card (Agent-to-Agent Protocol)">
          {a2aLoading ? (
            <LoadingState />
          ) : a2aError ? (
            <ErrorState error={new Error(a2aError)} retry={loadA2aCard} />
          ) : a2aCard ? (
            <div>
              <h2>{a2aCard.name}</h2>
              <p style={{ fontStyle: "italic", margin: "10px 0" }}>{a2aCard.description}</p>
              
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px", marginTop: "20px" }}>
                <div>
                  <h3>Sub-Agent Pipelines</h3>
                  <ul style={{ paddingLeft: "20px" }}>
                    {a2aCard.pipelines?.map((pipe: string) => (
                      <li key={pipe} style={{ margin: "5px 0" }}><code>{pipe}</code></li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h3>Registered Tools</h3>
                  <ul style={{ paddingLeft: "20px", maxHeight: "300px", overflowY: "auto" }}>
                    {a2aCard.tools?.map((tool: string) => (
                      <li key={tool} style={{ margin: "5px 0" }}><code>{tool}</code></li>
                    ))}
                  </ul>
                </div>
              </div>

              <h3 style={{ marginTop: "20px" }}>System Prompt Instruction Excerpt</h3>
              <pre style={{ padding: "15px", backgroundColor: "var(--bg-subtle)", borderRadius: "6px", fontSize: "0.85em", whiteSpace: "pre-wrap" }}>
                {a2aCard.instruction}
              </pre>
            </div>
          ) : null}
        </Card>
      )}

      {/* OPENAPI SCHEMA TAB */}
      {activeTab === "openapi" && (
        <Card title="OpenAPI Spec Explorer">
          {openapiLoading ? (
            <LoadingState />
          ) : openapiError ? (
            <ErrorState error={new Error(openapiError)} retry={loadOpenApiSchema} />
          ) : openapiSchema ? (
            <div>
              <p style={{ marginBottom: "15px" }}>Interactive raw JSON tree for <code>openapi.json</code>. Describes all routes, schemas, and tags.</p>
              <div style={{ border: "1px solid var(--border)", borderRadius: "6px", maxHeight: "600px", overflowY: "auto" }}>
                <JsonViewer value={openapiSchema} />
              </div>
            </div>
          ) : null}
        </Card>
      )}
    </div>
  );
}
