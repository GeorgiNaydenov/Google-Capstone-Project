"""Observability plugins (Day 4a).

ADK plugins hook the *whole* agent lifecycle (before/after agent, model, tool,
plus error hooks) in one object — broader than the per-agent callbacks in
callbacks.py, which are reserved for security. This module adds:

- `ObservabilityPlugin` — a ``BasePlugin`` that routes every lifecycle event
  into the structured, secret-redacted logging in observability.py, and logs a
  per-call token-budget estimate (wiring context.estimate_tokens into the live
  path). It records tool results and model/tool errors for the audit trail.
- `ClinicalAuditPlugin` — a domain plugin that tracks patient-data access
  across tool calls and emits HIPAA-style audit events via
  ``observability.log_clinical_event()``. Accumulates per-session metrics
  (tools invoked, patients accessed, PHI redactions) and flushes a summary
  after each agent turn completes.
- ``build_plugins()`` — the standard plugin set to attach to the App/Runner:
  ADK's built-in ``LoggingPlugin`` (verbose request/response tracing), our
  ``ObservabilityPlugin`` (redacted, structured, security-aware), and the
  ``ClinicalAuditPlugin`` (HIPAA audit trail).

Plugins are attached in app.py via ``App(..., plugins=build_plugins())``.
"""

import logging
from typing import Any, Optional

from google.adk.models import LlmRequest, LlmResponse
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.plugins.logging_plugin import LoggingPlugin

from .callbacks import _extract_last_user_text
from .config import redact_secrets
from .context import estimate_tokens
from .observability import log_clinical_event, log_security_event, log_tool_call
from .security import detect_phi

_logger = logging.getLogger("capstone_agent")

# Tools that access patient data and require HIPAA audit logging.
_PATIENT_DATA_TOOLS: set[str] = {
    "lookup_patient_record",
    "search_clinical_notes",
    "search_vector_store",
    "retrieve_imaging_evidence",
    "analyze_clinical_image",
    "execute_clinical_query",
    "fetch_image_from_gcs",
}


class ObservabilityPlugin(BasePlugin):
    """Lifecycle-wide observability that respects the harness's redaction rules.

    Everything emitted here passes through `redact_secrets` (directly or via the
    observability helpers), so plugin logs never leak credentials — unlike a
    naive print/trace of raw requests.
    """

    def __init__(self, name: str = "capstone_observability") -> None:
        super().__init__(name=name)

    async def before_model_callback(
        self, *, callback_context, llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Log a token-budget estimate before each model call (Day 4a metrics)."""
        try:
            text = _extract_last_user_text(llm_request)
            _logger.info(
                redact_secrets(
                    f"model_request: agent={getattr(callback_context, 'agent_name', '?')} "
                    f"est_input_tokens={estimate_tokens(text)}"
                )
            )
        except Exception:  # observability must never break the run
            pass
        return None

    async def after_tool_callback(
        self, *, tool, tool_args: dict[str, Any], tool_context, result: dict
    ) -> Optional[dict]:
        """Audit-log every tool result with redaction (timing handled by tools)."""
        try:
            log_tool_call(
                getattr(tool, "name", str(tool)),
                dict(tool_args),
                result if isinstance(result, dict) else {"status": "ok"},
                0.0,
            )
        except Exception:
            pass
        return None

    async def on_tool_error_callback(
        self, *, tool, tool_args: dict[str, Any], tool_context, error: Exception
    ) -> Optional[dict]:
        """Record tool failures in the audit trail."""
        log_security_event(
            "tool_error",
            {"tool": getattr(tool, "name", str(tool)), "error": str(error)},
        )
        return None

    async def on_model_error_callback(
        self, *, callback_context, llm_request: LlmRequest, error: Exception
    ) -> Optional[LlmResponse]:
        """Record model failures (after retries are exhausted) in the audit trail."""
        log_security_event("model_error", {"error": str(error)})
        return None


class ClinicalAuditPlugin(BasePlugin):
    """HIPAA-style audit plugin tracking patient-data access and PHI metrics.

    Hooks into the tool lifecycle to detect when patient-identifying tools are
    invoked, logs each access via ``log_clinical_event()``, scans tool results
    for PHI leakage, and emits a per-turn summary after the agent completes.

    Accumulated counters reset after each ``after_agent_callback`` flush so
    metrics stay scoped to a single agent turn — long-lived aggregation belongs
    in the external log pipeline, not in-process state.
    """

    def __init__(self, name: str = "clinical_audit") -> None:
        super().__init__(name=name)
        self._tools_invoked: int = 0
        self._patients_accessed: set[str] = set()
        self._phi_detections: int = 0
        self._evidence_retrievals: int = 0

    # -- tool hooks ----------------------------------------------------------

    async def before_tool_callback(
        self, *, tool, tool_args: dict[str, Any], tool_context, **kwargs
    ) -> Optional[dict]:
        """Log patient-data tool access for HIPAA audit trail."""
        tool_name = getattr(tool, "name", str(tool))
        self._tools_invoked += 1

        if tool_name in _PATIENT_DATA_TOOLS:
            patient_id = tool_args.get("patient_id") or tool_args.get("patient")
            if patient_id:
                self._patients_accessed.add(str(patient_id))
            log_clinical_event(
                "patient_record_accessed",
                {"tool": tool_name, "args_keys": list(tool_args.keys())},
                patient_id=str(patient_id) if patient_id else None,
            )

        if tool_name in {"search_clinical_notes", "search_vector_store", "retrieve_imaging_evidence"}:
            self._evidence_retrievals += 1

        return None

    async def after_tool_callback(
        self, *, tool, tool_args: dict[str, Any], tool_context, result: dict
    ) -> Optional[dict]:
        """Scan tool results for PHI leakage and count detections."""
        try:
            result_text = str(result) if result else ""
            phi_hits = detect_phi(result_text)
            if phi_hits:
                self._phi_detections += len(phi_hits)
                log_clinical_event(
                    "phi_redaction_applied",
                    {
                        "tool": getattr(tool, "name", str(tool)),
                        "phi_types": list({h["type"] for h in phi_hits}),
                        "count": len(phi_hits),
                    },
                )
        except Exception:
            pass
        return None

    # -- agent hooks ---------------------------------------------------------

    async def after_agent_callback(
        self, *, callback_context, **kwargs
    ) -> None:
        """Flush per-turn clinical metrics summary and reset counters."""
        if self._tools_invoked == 0:
            return

        log_clinical_event(
            "turn_audit_summary",
            {
                "agent": getattr(callback_context, "agent_name", "unknown"),
                "tools_invoked": self._tools_invoked,
                "patients_accessed": len(self._patients_accessed),
                "patient_ids": sorted(self._patients_accessed),
                "evidence_retrievals": self._evidence_retrievals,
                "phi_detections": self._phi_detections,
            },
        )

        self._tools_invoked = 0
        self._patients_accessed.clear()
        self._phi_detections = 0
        self._evidence_retrievals = 0


def build_plugins() -> list[BasePlugin]:
    """Return the standard plugin set for the App/Runner.

    Includes infrastructure observability, verbose request tracing,
    and the clinical HIPAA audit plugin for patient-data access tracking.
    """
    return [LoggingPlugin(), ObservabilityPlugin(), ClinicalAuditPlugin()]
