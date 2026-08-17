"""Tenant registry for the clinician product — single source of truth.

Defines the organizations selectable in the product UI and how legacy header
values resolve. All public product tenants serve deterministic fixtures; this
keeps a deployed demo unable to invoke paid model, Vertex, MCP, or A2A
services, even when callers forge an ``X-Tenant`` header.
"""

from enum import StrEnum

from pydantic import BaseModel


class TenantKind(StrEnum):
    """Whether a tenant serves deterministic demo data or real execution."""

    DEMO = "demo"
    REAL = "real"


class TenantConfig(BaseModel, frozen=True):
    """Immutable tenant definition resolved from the X-Tenant header.

    Demo tenants reference a fixture dataset key; real tenants reference the
    SQLite file and uploads directory that isolate their persisted data from
    the legacy clinical.db store.
    """

    id: str
    display_name: str
    kind: TenantKind
    dataset: str | None = None
    db_filename: str | None = None
    uploads_dirname: str | None = None


DEFAULT_TENANT_ID = "research-clinic"

TENANTS: dict[str, TenantConfig] = {
    "research-clinic": TenantConfig(
        id="research-clinic",
        display_name="Research Clinic",
        kind=TenantKind.DEMO,
        dataset="research_clinic",
        db_filename="showcase_data/database/clinical_showcase.db",
    ),
    "northstar-health": TenantConfig(
        id="northstar-health",
        display_name="Northstar Health",
        kind=TenantKind.DEMO,
        dataset="northstar",
        db_filename="showcase_data/demo2/database/clinical_showcase_demo2.db",
    ),
}

# Header values older browser sessions may still send in X-Tenant.
LEGACY_ALIASES: dict[str, str] = {
    "local": DEFAULT_TENANT_ID,
    "demo": DEFAULT_TENANT_ID,
    "default": DEFAULT_TENANT_ID,
    "live": DEFAULT_TENANT_ID,
    "capstone": DEFAULT_TENANT_ID,
}


def resolve_tenant(header_value: str | None) -> TenantConfig:
    """Resolve an X-Tenant header value to a tenant configuration.

    Unknown and retired live values fall back to the default demo tenant.
    This is an intentional server-side paid-service kill switch, not a UI
    preference, so crafted headers cannot restore agent execution.
    """

    key = (header_value or "").strip().casefold()
    key = LEGACY_ALIASES.get(key, key)
    return TENANTS.get(key, TENANTS[DEFAULT_TENANT_ID])
