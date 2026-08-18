"""Dependency-light metadata for the public clinical agent topology.

This module is the canonical source for agent names shown by the product API,
frontend, documentation, and topology contract tests. Runtime builders remain
in :mod:`capstone_agent.orchestration`; tests verify those builders match this
catalog so public claims cannot silently drift from executable code.
"""

from typing import Final


PIPELINE_AGENT_NAMES: Final[dict[str, tuple[str, ...]]] = {
    "extraction": (
        "quality_assessor_agent",
        "ocr_processor_agent",
        "vision_analyzer_agent",
        "clinical_structuring_agent",
        "extraction_critic_agent",
        "extraction_refiner_agent",
        "clinical_review_request_agent",
    ),
    "qa": (
        "qa_request_validation_agent",
        "context_assembly_agent",
        "evidence_retrieval_agent",
        "image_evidence_agent",
        "citation_builder_agent",
        "answer_synthesis_agent",
        "qa_audit_agent",
        "qa_response_agent",
    ),
    "database": (
        "schema_discovery_agent",
        "nl_to_sql_agent",
        "sql_validator_agent",
        "sql_preview_approval_agent",
        "query_executor_agent",
        "insight_chart_agent",
    ),
}

PIPELINE_DISPLAY: Final[dict[str, tuple[str, str]]] = {
    "extraction": ("Clinical Evidence Extraction", "/app/extraction"),
    "qa": ("Patient Q&A", "/app/qa"),
    "database": ("Population Insights", "/app/database"),
}

SPECIALIST_LLM_AGENT_COUNT: Final[int] = sum(
    len(names) for names in PIPELINE_AGENT_NAMES.values()
)
TOTAL_LLM_AGENT_COUNT: Final[int] = SPECIALIST_LLM_AGENT_COUNT + 1


def public_pipeline_catalog() -> list[dict[str, object]]:
    """Return fresh JSON-ready pipeline metadata for public API responses."""

    return [
        {
            "id": pipeline_id,
            "name": PIPELINE_DISPLAY[pipeline_id][0],
            "route": PIPELINE_DISPLAY[pipeline_id][1],
            "agents": list(agent_names),
        }
        for pipeline_id, agent_names in PIPELINE_AGENT_NAMES.items()
    ]
