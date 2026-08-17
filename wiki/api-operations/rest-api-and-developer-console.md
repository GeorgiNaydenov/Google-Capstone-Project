# REST API and Developer Console

> Sources: Antigravity, 2026-07-05
> Raw: [REST API and Developer Console Source Note](../../raw/api-operations/2026-07-05-rest-api-and-developer-console.md)

## Overview

The Nexus platform features a versioned, secure REST API backend built on FastAPI and a React-based interactive Developer/API Console. These systems enable developers and operators to run diagnostics, test endpoints, execute MCP tools, and discover A2A capabilities.

## API Versioning and Architecture

The API endpoints are segmented into three distinct groups:
- **V1 Router (`/api/v1`)**: Exposes core clinical entities (patients, sessions, storage assets, dashboard statistics).
- **V2 Router (`/api/v2`)**: System diagnostics health checks, FastMCP tool discovery and playground, and A2A card metadata.
- **Compatibility Router (`/api`)**: Re-maps core requests to the V1 router for backwards compatibility.

## Swagger and ReDoc Customization

A customized glassmorphic dark-theme is applied to the Swagger UI page at `/docs`. Every endpoint is annotated with standard HTTP response statuses (`400`, `401`, `403`, `404`, `422`, `500`) mapped to a shared Pydantic `ErrorResponse` schema.

## Interactive Developer Console

Accessible at `/app/console`, the console provides:
- An API Endpoint Runner (with customizable headers and JSON payloads).
- An MCP Playground to execute FastMCP database tools.
- An A2A Card Viewer displaying discovery metadata.
- An OpenAPI Specification Explorer.
