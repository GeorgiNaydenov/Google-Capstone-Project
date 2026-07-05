"""Real system introspection and tenant governance storage.

This module backs the "honest data" endpoints: component health is measured
against the actual process (database reachability, package imports, writable
storage) rather than reported from constants, and the real tenant's user
directory and role-permission matrix live in its own SQLite database so admin
edits survive across sessions and deployments.
"""

import importlib.util
import json
import os
import sqlite3
import tempfile
from pathlib import Path
from time import monotonic
from typing import Any

from pydantic import BaseModel, Field


PROJECT_ROOT = Path(__file__).resolve().parents[1]

ROLES = ["Admin", "Clinician", "Reviewer", "Read-only Viewer", "Data Manager"]


class DirectoryUser(BaseModel):
    """Validated seed row for the real tenant's read-only user directory."""

    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    email: str = Field(min_length=3)
    roles: list[str] = Field(min_length=1)
    scope: str
    status: str = "Active"


DEFAULT_USERS: list[DirectoryUser] = [
    DirectoryUser(id="USR-001", name="Dr. Sarah Miller", email="sarah.miller@capstone.health", roles=["Admin", "Clinician", "Reviewer"], scope="Organization"),
    DirectoryUser(id="USR-002", name="Dr. Elena Park", email="elena.park@capstone.health", roles=["Clinician"], scope="Assigned patients"),
    DirectoryUser(id="USR-003", name="Dr. James Patel", email="james.patel@capstone.health", roles=["Clinician", "Reviewer"], scope="Assigned patients"),
    DirectoryUser(id="USR-004", name="Alex Morgan", email="alex.morgan@capstone.health", roles=["Data Manager"], scope="Data platform"),
    DirectoryUser(id="USR-005", name="Riley Chen", email="riley.chen@capstone.health", roles=["Read-only Viewer"], scope="Audit and reports"),
]

# Default matrix mirrors the product permission model; the real tenant
# persists admin edits on top of it, demo tenants keep it session-scoped.
DEFAULT_PERMISSIONS: list[dict[str, Any]] = [
    {"permission": "View assigned patients", "grants": {"Admin": True, "Clinician": True, "Reviewer": True, "Read-only Viewer": True, "Data Manager": False}},
    {"permission": "Run clinical agents", "grants": {"Admin": True, "Clinician": True, "Reviewer": False, "Read-only Viewer": False, "Data Manager": False}},
    {"permission": "Approve clinical output", "grants": {"Admin": True, "Clinician": True, "Reviewer": True, "Read-only Viewer": False, "Data Manager": False}},
    {"permission": "Query population database", "grants": {"Admin": True, "Clinician": True, "Reviewer": False, "Read-only Viewer": True, "Data Manager": True}},
    {"permission": "Configure agent policy", "grants": {"Admin": True, "Clinician": False, "Reviewer": False, "Read-only Viewer": False, "Data Manager": False}},
    {"permission": "Manage storage and indexes", "grants": {"Admin": True, "Clinician": False, "Reviewer": False, "Read-only Viewer": False, "Data Manager": True}},
]


def _timed(check: Any) -> tuple[str, str, float]:
    """Run one check callable, returning (status, detail, latency_ms).

    A check returns a detail string on success and raises on failure; the
    measured wall time covers only the check itself.
    """

    started = monotonic()
    try:
        detail = check()
        return "operational", str(detail), (monotonic() - started) * 1000.0
    except Exception as exc:  # component check must never take the API down
        return "unavailable", f"{type(exc).__name__}: {exc}", (monotonic() - started) * 1000.0


def component_checks(repo: Any) -> list[dict[str, Any]]:
    """Measure real component health for the caller's tenant.

    Every row is produced by actually exercising the component: the tenant
    database answers a query, the uploads directory accepts a tempfile, the
    agent and MCP packages import, and model credentials are inspected
    (without calling the model). Both demo and real tenants run the same
    checks so service health is never fabricated.
    """

    db_path = getattr(repo, "db_path", None)
    uploads_root = getattr(repo, "uploads_root", None)

    def check_database() -> str:
        if db_path is not None:
            with sqlite3.connect(db_path) as connection:
                connection.execute("SELECT 1").fetchone()
            return f"SQLite reachable at {Path(db_path).name}"
        # Demo tenants run from in-memory fixtures; the check proves the
        # fixture registry is loaded rather than pretending a DB exists.
        return f"In-memory demo dataset loaded ({len(repo.patients)} patients)"

    def check_agent_package() -> str:
        if importlib.util.find_spec("capstone_agent") is None:
            raise ModuleNotFoundError("capstone_agent not importable")
        return "ADK agent package importable"

    def check_mcp_server() -> str:
        if importlib.util.find_spec("mcp_server.server") is None:
            raise ModuleNotFoundError("mcp_server.server not importable")
        return "MCP clinical server module importable"

    def check_uploads() -> str:
        target = Path(uploads_root) if uploads_root is not None else Path(tempfile.gettempdir())
        target.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target, prefix=".healthcheck-", delete=True):
            pass
        label = target.name if uploads_root is not None else "temp storage"
        return f"Uploads writable ({label})"

    def check_model_config() -> str:
        if os.environ.get("GOOGLE_API_KEY"):
            return "Gemini API key configured"
        if os.environ.get("GOOGLE_GENAI_USE_VERTEXAI", "").upper() == "TRUE" and os.environ.get("GOOGLE_CLOUD_PROJECT"):
            return f"Vertex AI configured ({os.environ['GOOGLE_CLOUD_PROJECT']})"
        raise LookupError("No GOOGLE_API_KEY or Vertex AI project configured")

    def check_frontend() -> str:
        if not (PROJECT_ROOT / "frontend" / "dist" / "index.html").is_file():
            raise FileNotFoundError("frontend/dist/index.html missing; run npm run build")
        return "Frontend production bundle present"

    components = []
    for name, check in (
        ("Clinical database", check_database),
        ("ADK agent runtime", check_agent_package),
        ("MCP tool server", check_mcp_server),
        ("Upload storage", check_uploads),
        ("Model credentials", check_model_config),
        ("Frontend bundle", check_frontend),
    ):
        status, detail, latency = _timed(check)
        components.append({"name": name, "status": status, "detail": detail, "latencyMs": round(latency, 1)})
    return components


def _governance_connection(db_path: Path) -> sqlite3.Connection:
    """Open the tenant database with row access by column name."""

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def seed_users(db_path: Path) -> None:
    """Create and seed the users and role_permissions tables idempotently.

    The real tenant's directory is read-only in the product, so seeding only
    inserts missing rows and never overwrites persisted permission edits.
    """

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _governance_connection(db_path) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "user_id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, "
            "roles TEXT NOT NULL, scope TEXT NOT NULL, status TEXT NOT NULL)"
        )
        connection.execute(
            "CREATE TABLE IF NOT EXISTS role_permissions ("
            "permission TEXT PRIMARY KEY, grants TEXT NOT NULL, "
            "version INTEGER NOT NULL DEFAULT 1, updated_by TEXT)"
        )
        for user in DEFAULT_USERS:
            connection.execute(
                "INSERT OR IGNORE INTO users (user_id, name, email, roles, scope, status) VALUES (?, ?, ?, ?, ?, ?)",
                (user.id, user.name, user.email, json.dumps(user.roles), user.scope, user.status),
            )
        for row in DEFAULT_PERMISSIONS:
            connection.execute(
                "INSERT OR IGNORE INTO role_permissions (permission, grants) VALUES (?, ?)",
                (row["permission"], json.dumps(row["grants"])),
            )
        connection.commit()


def load_users(db_path: Path) -> list[dict[str, Any]]:
    """Return the persisted user directory for a real tenant."""

    with _governance_connection(db_path) as connection:
        rows = connection.execute("SELECT user_id, name, email, roles, scope, status FROM users ORDER BY user_id").fetchall()
    return [
        {"id": row["user_id"], "name": row["name"], "email": row["email"], "roles": json.loads(row["roles"]), "scope": row["scope"], "status": row["status"]}
        for row in rows
    ]


def load_permissions(db_path: Path) -> dict[str, Any]:
    """Return the persisted permission matrix for a real tenant."""

    with _governance_connection(db_path) as connection:
        rows = connection.execute("SELECT permission, grants, version FROM role_permissions").fetchall()
    order = {row["permission"]: index for index, row in enumerate(DEFAULT_PERMISSIONS)}
    matrix = [{"permission": row["permission"], "grants": json.loads(row["grants"])} for row in rows]
    matrix.sort(key=lambda row: order.get(row["permission"], len(order)))
    version = max((row["version"] for row in rows), default=1)
    return {"roles": ROLES, "matrix": matrix, "version": version}


def save_permissions(db_path: Path, matrix: list[dict[str, Any]], actor: str) -> dict[str, Any]:
    """Persist an edited permission matrix and bump its version."""

    current = load_permissions(db_path)
    version = int(current["version"]) + 1
    with _governance_connection(db_path) as connection:
        for row in matrix:
            connection.execute(
                "INSERT INTO role_permissions (permission, grants, version, updated_by) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(permission) DO UPDATE SET grants=excluded.grants, version=excluded.version, updated_by=excluded.updated_by",
                (row["permission"], json.dumps(row["grants"]), version, actor),
            )
        connection.commit()
    return load_permissions(db_path)
