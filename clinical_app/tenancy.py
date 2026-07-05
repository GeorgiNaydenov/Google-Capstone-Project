"""Tenant registry for the clinician product — single source of truth.

Defines the organizations selectable in the product UI, how each one maps to
data and execution behavior, and how legacy header values resolve. Demo
tenants serve deterministic in-memory fixtures so the product can be explored
without credentials; real tenants execute the live ADK agent stack against
their own isolated SQLite database and uploads directory, starting empty.
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
    ),
    "northstar-health": TenantConfig(
        id="northstar-health",
        display_name="Northstar Health",
        kind=TenantKind.DEMO,
        dataset="northstar",
    ),
    "capstone": TenantConfig(
        id="capstone",
        display_name="Capstone",
        kind=TenantKind.REAL,
        db_filename="capstone.db",
        uploads_dirname="uploads_capstone",
    ),
}

# Header values older browser sessions may still send in X-Tenant.
LEGACY_ALIASES: dict[str, str] = {
    "local": DEFAULT_TENANT_ID,
    "demo": DEFAULT_TENANT_ID,
    "default": DEFAULT_TENANT_ID,
    "live": "capstone",
}


def resolve_tenant(header_value: str | None) -> TenantConfig:
    """Resolve an X-Tenant header value to a tenant configuration.

    Unknown values fall back to the default demo tenant so an unrecognized
    caller can never reach the real tenant's live execution or database.
    """

    key = (header_value or "").strip().casefold()
    key = LEGACY_ALIASES.get(key, key)
    return TENANTS.get(key, TENANTS[DEFAULT_TENANT_ID])
