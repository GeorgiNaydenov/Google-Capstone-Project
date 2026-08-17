# REST API and Developer Console Source Note

> Source: Project Wiki/06 Operations/REST API and Developer Console.md
> Collected: 2026-07-05
> Published: 2026-07-05

REST API and Developer Console:
Nexus exposes a versioned, secure REST API backend built on FastAPI and a React-based interactive Developer/API Console to assist developers in testing, auditing, and executing agent pipelines and MCP tools.
1. V1 API (`/api/v1`): Core clinical endpoints.
2. V2 API (`/api/v2`): System diagnostics, MCP tool catalog, execution runner, A2A card.
3. Compatibility API (`/api`): Backward compatibility routing.
4. Swagger & ReDoc Console: Customized styled dark theme at `/docs` and `/redoc` with ErrorResponse.
5. Developer Console: Tabbed endpoint runner, MCP tool playground, A2A card viewer at `/app/console`.
