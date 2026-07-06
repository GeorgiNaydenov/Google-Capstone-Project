import React, { useState, useEffect } from "react";
import { useSearchParams, useLocation, useNavigate } from "react-router-dom";
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
  { method: "GET", path: "/api/v1/patients/PT-D00008", description: "Get a specific patient profile by ID" },
  { method: "GET", path: "/api/v1/sessions", description: "List all clinical sessions, optionally filtered by patient_id", defaultParams: { patient_id: "PT-D00008" } },
  { method: "GET", path: "/api/v1/dashboard", description: "Retrieve metrics, patients, sessions, and activity logs", defaultParams: { role: "clinician" } },
  { method: "POST", path: "/api/v1/orchestrate", description: "Classify user natural language request and output a workflow plan", defaultBody: JSON.stringify({ query: "show me all patients with high risk of heart failure", patientId: "PT-D00008" }, null, 2) },
  { method: "POST", path: "/api/v1/runs/qa", description: "Execute patient-scoped grounded Q&A", defaultBody: JSON.stringify({ patientId: "PT-D00008", question: "What is the most recent ejection fraction?", source_types: ["text", "image"], filters: { dateRange: "30d" } }, null, 2) },
  { method: "POST", path: "/api/v1/runs/database/preview", description: "Generate safe read-only SQL query for population questions", defaultBody: JSON.stringify({ question: "How many patients are active?" }, null, 2) },
  { method: "POST", path: "/api/v1/import", description: "Import patient-cohort data or documents through agent ETL (live mode only)", defaultBody: JSON.stringify({ importType: "database" }, null, 2) },
  { method: "GET", path: "/api/v2/health", description: "Fetch advanced system health checking database and storage connectivity" },
  { method: "GET", path: "/api/v2/mcp/tools", description: "List all dynamic tools registered on the FastMCP clinical server" },
  { method: "GET", path: "/api/v2/a2a/card", description: "Retrieve Agent Card metadata for Agent-to-Agent discovery" },
];
function renderMarkdown(md: string): string {
  if (!md) return "";
  let html = md;

  // Escape HTML tags to prevent arbitrary execution, but keep basic formatting
  html = html
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Bold
  html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

  // Headings
  html = html.replace(/^### (.*$)/gim, "<h3>$1</h3>");
  html = html.replace(/^## (.*$)/gim, "<h2>$1</h2>");
  html = html.replace(/^# (.*$)/gim, "<h1>$1</h1>");

  // Blockquotes / alerts
  html = html.replace(/^> \[\!([A-Z]+)\]\s*(.*$)/gim, '<div class="alert-box alert-$1" style="border-left: 4px solid var(--blue); padding: 8px 12px; background: var(--bg-subtle); margin: 10px 0;"><strong>$1</strong>: $2</div>');
  html = html.replace(/^> (.*$)/gim, '<blockquote style="border-left: 3px solid var(--border); padding-left: 10px; margin: 10px 0; color: var(--fg-muted)">$1</blockquote>');

  // Code blocks
  html = html.replace(/```([\s\S]*?)```/gm, '<pre style="background: var(--bg-subtle); padding: 12px; border-radius: 6px; overflow-x: auto; font-family: monospace; font-size: 0.9em; margin: 12px 0; border: 1px solid var(--border);"><code style="white-space: pre;">$1</code></pre>');
  html = html.replace(/`([^`]+)`/g, '<code style="background: var(--bg-subtle); padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em; border: 1px solid var(--border);">$1</code>');

  // Wikilinks [[Note|Label]] or [[Note]]
  html = html.replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, '<span class="wiki-link" style="color:var(--blue);cursor:pointer;text-decoration:underline;">$2</span>');
  html = html.replace(/\[\[([^\]]+)\]\]/g, '<span class="wiki-link" style="color:var(--blue);cursor:pointer;text-decoration:underline;">$1</span>');

  // Normal links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" style="color:var(--blue);text-decoration:underline;">$1</a>');

  // Unordered list
  html = html.replace(/^\- (.*$)/gim, "<li>$1</li>");

  // GFM style tables
  const lines = html.split("\n");
  let inTable = false;
  let tableHtml = "";
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line.startsWith("|") && line.endsWith("|")) {
      if (!inTable) {
        inTable = true;
        tableHtml += '<table class="dense-table" style="width:100%; border-collapse: collapse; margin: 15px 0;">';
      }
      const cells = line.split("|").slice(1, -1).map(c => c.trim());
      if (cells.every(c => c.startsWith("-") || c.startsWith(":") || c === "")) {
        continue;
      }
      const tag = tableHtml.includes("<thead>") ? "td" : "th";
      const wrapStart = tag === "th" ? '<thead style="background: var(--bg-subtle);"><tr>' : "<tr>";
      const wrapEnd = tag === "th" ? "</tr></thead><tbody>" : "</tr>";
      tableHtml += wrapStart + cells.map(c => `<${tag} style="border: 1px solid var(--border); padding: 8px; text-align: left; font-weight: ${tag === "th" ? "bold" : "normal"};">${c}</${tag}>`).join("") + wrapEnd;
    } else {
      if (inTable) {
        inTable = false;
        tableHtml += "</tbody></table>";
        lines[i] = tableHtml + "\n" + lines[i];
        tableHtml = "";
      }
    }
  }
  if (inTable) {
    tableHtml += "</tbody></table>";
    html = lines.join("\n") + "\n" + tableHtml;
  } else {
    html = lines.join("\n");
  }

  // Convert remaining linebreaks to <br />
  html = html.split("\n").join("<br />");

  return html;
}

export function DeveloperConsole() {
  const [searchParams, setSearchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const isStandalone = location.pathname === "/docs-viewer";
  const tabParam = searchParams.get("tab");
  const activeTab = (tabParam as any) || "api_runner";

  const setActiveTab = (tab: string) => {
    setSearchParams(prev => {
      prev.set("tab", tab);
      return prev;
    });
  };

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

  // API Documentation view state
  const [apiDocsMode, setApiDocsMode] = useState<"swagger" | "redoc" | "raw">("swagger");

  // Wiki state
  const [docsList, setDocsList] = useState<{ obsidian: any[]; karpathy: any[] } | null>(null);
  const [docsListLoading, setDocsListLoading] = useState<boolean>(false);
  const [docsListError, setDocsListError] = useState<string>("");
  const [selectedDocPath, setSelectedDocPath] = useState<string>("");
  const [docContent, setDocContent] = useState<string>("");
  const [docLoading, setDocLoading] = useState<boolean>(false);
  const [docError, setDocError] = useState<string>("");

  // Synchronize preset values when endpoint changes
  useEffect(() => {
    // Extract path params (e.g. {patient_id})
    const pathMatches = selectedEndpoint.path.match(/\{([^}]+)\}/g);
    const initialPaths: Record<string, string> = {};
    if (pathMatches) {
      pathMatches.forEach(match => {
        const paramName = match.replace(/[{}]/g, "");
        initialPaths[paramName] = paramName === "patient_id" ? "PT-D00008" : "RUN-001";
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
            sample[key] = props[key].default !== undefined ? props[key].default : (props[key].type === "integer" ? 10 : "PT-D00008");
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

  const loadDocsList = async () => {
    setDocsListLoading(true);
    setDocsListError("");
    try {
      const res = await api.docsList();
      setDocsList(res);
      const files = activeTab === "obsidian_wiki" ? res.obsidian : res.karpathy;
      if (files && files.length > 0) {
        setSelectedDocPath(files[0].path);
      }
    } catch (e: any) {
      setDocsListError(e.message || "Failed to load documentation list");
    } finally {
      setDocsListLoading(false);
    }
  };

  const loadDocFile = async (type: "obsidian" | "karpathy", path: string) => {
    if (!path) return;
    setDocLoading(true);
    setDocError("");
    setDocContent("");
    try {
      const res = await api.docsFile(type, path);
      setDocContent(res.content);
    } catch (e: any) {
      setDocError(e.message || "Failed to load document content");
    } finally {
      setDocLoading(false);
    }
  };

  // Handle Tab Switch
  useEffect(() => {
    if (activeTab === "mcp_tools") {
      void loadMcpTools();
    } else if (activeTab === "a2a_card") {
      void loadA2aCard();
    } else if (activeTab === "api_docs" && apiDocsMode === "raw") {
      void loadOpenApiSchema();
    } else if (activeTab === "obsidian_wiki" || activeTab === "karpathy_wiki") {
      if (!docsList) {
        void loadDocsList();
      } else {
        const files = activeTab === "obsidian_wiki" ? docsList.obsidian : docsList.karpathy;
        if (files && files.length > 0) {
          setSelectedDocPath(files[0].path);
        }
      }
    }
  }, [activeTab, apiDocsMode]);

  useEffect(() => {
    if (activeTab === "obsidian_wiki" && selectedDocPath) {
      void loadDocFile("obsidian", selectedDocPath);
    } else if (activeTab === "karpathy_wiki" && selectedDocPath) {
      void loadDocFile("karpathy", selectedDocPath);
    }
  }, [selectedDocPath, activeTab]);

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
        sample[key] = props[key].default !== undefined ? props[key].default : (props[key].type === "integer" ? 10 : "PT-D00008");
      });
      setMcpArguments(JSON.stringify(sample, null, 2));
    } else {
      setMcpArguments("{\n  \n}");
    }
  };

  return (
    <div className={isStandalone ? "standalone-docs-viewer" : "developer-console"} style={isStandalone ? { minHeight: "100vh", display: "flex", flexDirection: "column", background: "var(--bg)" } : undefined}>
      {isStandalone ? (
        <header className="landing-nav" style={{ position: "sticky", top: 0, zIndex: 30, display: "flex", height: "64px", alignItems: "center", justifyContent: "space-between", padding: "0 4vw", borderBottom: "1px solid var(--border-strong)", background: "#ffffffeb", backdropFilter: "blur(14px) saturate(1.12)", width: "100%" }}>
          <div className="product-lockup" style={{ display: "flex", alignItems: "center", gap: "10px", cursor: "pointer" }} onClick={() => navigate("/")}>
            <span className="product-symbol" style={{ display: "flex", alignItems: "center" }}>
              <img src="/favicon.png" alt="" width={26} height={26} style={{objectFit:"contain"}}/>
            </span>
            <span style={{ display: "flex", flexDirection: "column", lineHeight: "1.2" }}><strong style={{ fontSize: "14px", color: "var(--blue-dark)" }}>Clinician AI KIT</strong><small style={{ fontSize: "10px", color: "var(--muted)" }}>Documentation Viewer</small></span>
          </div>
          <nav className="tabs" style={{ display: "flex", gap: "10px", borderBottom: "none", padding: 0, margin: 0, height: "100%", alignItems: "center" }}>
            <button className={activeTab === "api_docs" ? "active" : ""} onClick={() => setActiveTab("api_docs")} style={{ padding: "8px 16px", border: "none", background: "none", color: activeTab === "api_docs" ? "var(--blue)" : "#475569", fontWeight: activeTab === "api_docs" ? "700" : "500", cursor: "pointer", borderBottom: activeTab === "api_docs" ? "2px solid var(--blue)" : "none", height: "100%", fontSize: "13px" }}>
              Interactive API Docs
            </button>
            <a href="/documentation/project-wiki/Home.html" style={{ padding: "8px 16px", color: "#475569", fontWeight: "500", fontSize: "13px", textDecoration: "none", display: "flex", alignItems: "center", height: "100%" }}>
              Obsidian Wiki
            </a>
            <a href="/documentation/llm-wiki/index.html" style={{ padding: "8px 16px", color: "#475569", fontWeight: "500", fontSize: "13px", textDecoration: "none", display: "flex", alignItems: "center", height: "100%" }}>
              Karpathy LLM Wiki
            </a>
            <button className={activeTab === "api_runner" ? "active" : ""} onClick={() => setActiveTab("api_runner")} style={{ padding: "8px 16px", border: "none", background: "none", color: activeTab === "api_runner" ? "var(--blue)" : "#475569", fontWeight: activeTab === "api_runner" ? "700" : "500", cursor: "pointer", borderBottom: activeTab === "api_runner" ? "2px solid var(--blue)" : "none", height: "100%", fontSize: "13px" }}>
              API Console
            </button>
          </nav>
          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            <button className="button secondary" onClick={() => navigate("/")} style={{ padding: "8px 16px", borderRadius: "6px", border: "1px solid var(--border)", background: "#fff", cursor: "pointer", fontSize: "13px", fontWeight: "600", color: "#475569", fontFamily: "inherit" }}>Exit Viewer</button>
            <button className="button primary" onClick={() => navigate("/roles")} style={{ padding: "8px 16px", borderRadius: "6px", border: "none", background: "var(--blue)", color: "#fff", cursor: "pointer", fontSize: "13px", fontWeight: "600", fontFamily: "inherit" }}>Enter Workspace</button>
          </div>
        </header>
      ) : (
        <>
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
            <button className={activeTab === "api_docs" ? "active" : ""} onClick={() => setActiveTab("api_docs")}>
              Interactive API Docs
            </button>
            <a href="/documentation/project-wiki/Home.html" style={{ display: "flex", alignItems: "center", padding: "0 14px", textDecoration: "none", color: "#475569" }}>
              Obsidian Wiki
            </a>
            <a href="/documentation/llm-wiki/index.html" style={{ display: "flex", alignItems: "center", padding: "0 14px", textDecoration: "none", color: "#475569" }}>
              Karpathy LLM Wiki
            </a>
          </nav>
        </>
      )}

      <div className={isStandalone ? "standalone-docs-content" : ""} style={isStandalone ? { flex: 1, padding: "35px 4vw", maxWidth: "1600px", width: "100%", margin: "0 auto", display: "flex", flexDirection: "column" } : undefined}>

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

      {/* API DOCUMENTATION TAB */}
      {activeTab === "api_docs" && (
        <Card title="Interactive OpenAPI Documentation">
          <div style={{ display: "flex", flexDirection: "column", gap: "15px", marginTop: "10px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "15px", marginBottom: "10px" }}>
              <label style={{ fontWeight: "bold" }}>Select Documentation View:</label>
              <select
                value={apiDocsMode}
                onChange={e => setApiDocsMode(e.target.value as any)}
                style={{
                  padding: "8px 12px",
                  borderRadius: "6px",
                  backgroundColor: "var(--bg-subtle)",
                  color: "var(--fg)",
                  border: "1px solid var(--border)",
                  cursor: "pointer"
                }}
              >
                <option value="swagger">Swagger UI Console (Interactive)</option>
                <option value="redoc">ReDoc Specifications (Reader)</option>
                <option value="raw">Raw OpenAPI Schema (Explorer)</option>
              </select>
            </div>

            {apiDocsMode === "swagger" && (
              <div style={{ border: "1px solid var(--border)", borderRadius: "8px", overflow: "hidden", height: "800px", background: "#fff" }}>
                <iframe
                  src="/docs"
                  title="Swagger UI"
                  style={{ width: "100%", height: "100%", border: "none" }}
                />
              </div>
            )}

            {apiDocsMode === "redoc" && (
              <div style={{ border: "1px solid var(--border)", borderRadius: "8px", overflow: "hidden", height: "800px", background: "#fff" }}>
                <iframe
                  src="/redoc"
                  title="ReDoc"
                  style={{ width: "100%", height: "100%", border: "none" }}
                />
              </div>
            )}

            {apiDocsMode === "raw" && (
              <div>
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
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Obsidian Wiki Tab */}
      {activeTab === "obsidian_wiki" && (
        <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "20px", height: "800px" }}>
          <Card title="Obsidian Notes">
            <div style={{ height: "720px", overflowY: "auto", marginTop: "10px" }}>
              {docsListLoading ? (
                <LoadingState />
              ) : docsListError ? (
                <ErrorState error={new Error(docsListError)} retry={loadDocsList} />
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "5px", paddingRight: "10px" }}>
                  {docsList?.obsidian.map(file => (
                    <button
                      key={file.path}
                      onClick={() => setSelectedDocPath(file.path)}
                      style={{
                        textAlign: "left",
                        padding: "10px",
                        borderRadius: "6px",
                        border: "1px solid var(--border)",
                        backgroundColor: selectedDocPath === file.path ? "var(--blue-soft)" : "transparent",
                        color: selectedDocPath === file.path ? "var(--blue-dark)" : "var(--fg)",
                        cursor: "pointer",
                        fontSize: "0.9em",
                        fontWeight: selectedDocPath === file.path ? "bold" : "normal"
                      }}
                    >
                      {file.title}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </Card>
          <Card title={selectedDocPath ? `Document: ${selectedDocPath.split('/').pop()}` : "Document Reader"}>
            <div style={{ height: "720px", overflowY: "auto", padding: "10px", marginTop: "10px" }}>
              {docLoading ? (
                <LoadingState />
              ) : docError ? (
                <ErrorState error={new Error(docError)} retry={() => loadDocFile("obsidian", selectedDocPath)} />
              ) : docContent ? (
                <div
                  className="markdown-body"
                  style={{
                    lineHeight: "1.6",
                    color: "var(--fg)",
                    fontSize: "0.95em",
                  }}
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(docContent) }}
                />
              ) : (
                <div style={{ color: "var(--fg-muted)", textAlign: "center", marginTop: "100px" }}>Select a note from the list to view its content.</div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* Karpathy LLM Wiki Tab */}
      {activeTab === "karpathy_wiki" && (
        <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: "20px", height: "800px" }}>
          <Card title="Compiled Wiki Pages">
            <div style={{ height: "720px", overflowY: "auto", marginTop: "10px" }}>
              {docsListLoading ? (
                <LoadingState />
              ) : docsListError ? (
                <ErrorState error={new Error(docsListError)} retry={loadDocsList} />
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "5px", paddingRight: "10px" }}>
                  {docsList?.karpathy.map(file => (
                    <button
                      key={file.path}
                      onClick={() => setSelectedDocPath(file.path)}
                      style={{
                        textAlign: "left",
                        padding: "10px",
                        borderRadius: "6px",
                        border: "1px solid var(--border)",
                        backgroundColor: selectedDocPath === file.path ? "var(--blue-soft)" : "transparent",
                        color: selectedDocPath === file.path ? "var(--blue-dark)" : "var(--fg)",
                        cursor: "pointer",
                        fontSize: "0.9em",
                        fontWeight: selectedDocPath === file.path ? "bold" : "normal"
                      }}
                    >
                      {file.title}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </Card>
          <Card title={selectedDocPath ? `Wiki Page: ${selectedDocPath.split('/').pop()}` : "Wiki Page Reader"}>
            <div style={{ height: "720px", overflowY: "auto", padding: "10px", marginTop: "10px" }}>
              {docLoading ? (
                <LoadingState />
              ) : docError ? (
                <ErrorState error={new Error(docError)} retry={() => loadDocFile("karpathy", selectedDocPath)} />
              ) : docContent ? (
                <div
                  className="markdown-body"
                  style={{
                    lineHeight: "1.6",
                    color: "var(--fg)",
                    fontSize: "0.95em",
                  }}
                  dangerouslySetInnerHTML={{ __html: renderMarkdown(docContent) }}
                />
              ) : (
                <div style={{ color: "var(--fg-muted)", textAlign: "center", marginTop: "100px" }}>Select a wiki page from the list to view its content.</div>
              )}
            </div>
          </Card>
        </div>
      )}
      </div>
    </div>
  );
}
