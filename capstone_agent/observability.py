"""Observability — structured logging, tracing, and audit trail.

Implements the observability pillar from Day 4 of the course:
Logs (diary), Traces (narrative), Metrics (health report).

All log output passes through config.redact_secrets() to prevent
accidental secret leakage. Security events get their own audit
trail via log_security_event().

Design decisions:
- Structured JSON logging by default (machine-parseable, searchable).
- OpenTelemetry tracing is opt-in via ENABLE_TRACING env var.
- Tool call logging captures name, args, result, and duration
  for debugging and performance analysis.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any

from .config import get_config, redact_secrets

_logger = logging.getLogger("capstone_agent")


def setup_logging(level: str | None = None) -> logging.Logger:
    """Configure structured logging for the agent.

    Uses JSON-like format for machine parseability.
    All output is redacted for secrets before emission.
    """
    config = get_config()
    log_level = level or config["log_level"]

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            '{"time":"%(asctime)s","level":"%(levelname)s","module":"%(name)s","message":"%(message)s"}'
        )
    )

    logger = logging.getLogger("capstone_agent")
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    return logger


def setup_tracing() -> None:
    """Initialize OpenTelemetry tracing if ENABLE_TRACING is set.

    Sends traces to an OTLP-compatible collector. This is opt-in
    because it requires a collector endpoint to be running.
    """
    config = get_config()
    if not config["enable_tracing"]:
        _logger.info("Tracing disabled (set ENABLE_TRACING=TRUE to enable)")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": config["app_name"]})
        provider = TracerProvider(resource=resource)

        # Exporter is selectable: 'gcp' sends spans to Google Cloud Trace (Day 4a,
        # the production target for deployed agents); 'otlp' (default) sends to any
        # OpenTelemetry collector. GCP exporter degrades to OTLP if not installed.
        exporter = _build_span_exporter(config["trace_exporter"])
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _logger.info(
            f"OpenTelemetry tracing initialized (exporter={config['trace_exporter']})"
        )
    except ImportError:
        _logger.warning("OpenTelemetry packages not installed; tracing disabled")


def _build_span_exporter(exporter: str):
    """Build the configured OTel span exporter (Cloud Trace or OTLP)."""
    if exporter == "gcp":
        try:
            from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter

            return CloudTraceSpanExporter()
        except ImportError:
            _logger.warning(
                "opentelemetry-exporter-gcp-trace not installed; falling back to OTLP"
            )

    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    return OTLPSpanExporter()


def log_tool_call(
    tool_name: str,
    args: dict[str, Any],
    result: dict[str, Any],
    duration_ms: float,
) -> None:
    """Log a structured tool call event for debugging and audit.

    Args are redacted to prevent secret leakage in logs.
    """
    _logger.info(
        redact_secrets(
            f"tool_call: name={tool_name} "
            f"args={args} "
            f"status={result.get('status', 'unknown')} "
            f"duration_ms={duration_ms:.1f}"
        )
    )


def log_security_event(event_type: str, details: dict[str, Any]) -> None:
    """Log a security event for audit trail.

    Called when input is blocked, PII is detected, secrets are found,
    or tool authorization fails. These events should be monitored
    in production for threat detection.
    """
    _logger.warning(
        redact_secrets(f"security_event: type={event_type} details={details}")
    )


def log_clinical_event(
    event_type: str,
    details: dict[str, Any],
    patient_id: str | None = None,
) -> None:
    """Log a clinical access or action event for HIPAA-style audit.

    Clinical events track every consequential action touching patient
    data: record access, evidence retrieval, extraction completion,
    clinical review decisions, PHI redaction, and query execution.

    Valid event_type values:
        patient_record_accessed, extraction_completed,
        clinical_review_requested, clinical_review_approved,
        clinical_review_rejected, phi_redaction_applied,
        evidence_retrieved, query_executed, memory_persisted

    Args:
        event_type: The clinical event category for filtering and alerting.
        details: Structured event metadata (agent name, action, etc.).
            Never include raw PHI — use patient_id for linking.
        patient_id: Patient identifier (never a name or MRN). Kept
            separate so audit queries can filter by patient scope.
    """
    audit_payload = {
        "event_type": event_type,
        "patient_id": patient_id or "system",
        "data_classification": "phi" if patient_id else "internal",
        **details,
    }
    _logger.info(redact_secrets(f"clinical_event: {audit_payload}"))


@contextmanager
def timed_operation(operation_name: str):
    """Context manager that measures and logs operation duration.

    Usage:
        with timed_operation("example_search"):
            result = do_search(query)
    """
    start = time.perf_counter()
    try:
        yield
    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        _logger.debug(
            f"timing: operation={operation_name} duration_ms={duration_ms:.1f}"
        )
