"""Deterministic product adapters for the real clinical agent tool layer."""

import json
from typing import Any

from capstone_agent.tools import (
    approve_sql_preview,
    build_citations,
    compose_clinical_answer,
    execute_approved_clinical_query,
    extract_clinical_text,
    flag_for_review,
    generate_chart_spec,
    generate_sql,
    get_database_schema,
    log_audit_event,
    lookup_patient_record,
    persist_extraction_relational,
    persist_extraction_vector,
    retrieve_imaging_evidence,
    search_clinical_notes,
    search_vector_store,
    store_to_gcs,
    transition_extraction_review,
    validate_qa_request,
    validate_sql_safety,
)


def _trace(tool: str, output: dict[str, Any]) -> dict[str, Any]:
    """Create a stable, inspectable trace entry for a product agent run."""

    return {
        "tool": tool,
        "status": output.get("status", "unknown"),
        "message": output.get("message", output.get("error", {}).get("message", "")),
        "output": output.get("data", output.get("error", {})),
    }


def extraction_tools(
    patient_id: str, asset_id: str, run_id: str
) -> list[dict[str, Any]]:
    """Run non-model extraction and audit tools for an uploaded source."""

    image_uri = f"gs://clinical-data/{patient_id}/uploads/{asset_id}"
    ocr = extract_clinical_text(image_uri, patient_id, run_id)
    review_flag = flag_for_review(
        "finding", "Evidence ready for clinician verification", 0.87
    )
    audit = log_audit_event(
        "image_extraction_pipeline",
        "extraction_review_requested",
        patient_id,
        json.dumps({"run_id": run_id, "asset_id": asset_id}),
    )
    return [
        _trace("extract_clinical_text", ocr),
        _trace("flag_for_review", review_flag),
        _trace("log_audit_event", audit),
    ]


def extraction_review_tools(
    patient_id: str,
    run_id: str,
    decision: str,
    reviewer: str,
    fields: dict[str, Any],
    reason: str,
    persist_session_id: str | None = None,
) -> list[dict[str, Any]]:
    """Run the actual review and persistence tool contracts.

    persist_session_id must reference an existing sessions row when given —
    extracted_fields enforces that foreign key — so approvals persist under
    the clinical session the caller created, not the transient run id.
    """

    action = "approve" if decision == "approved" else "reject"
    transition = transition_extraction_review(
        patient_id, run_id, "needs_review", action, reviewer, reason
    )
    traces = [_trace("transition_extraction_review", transition)]
    receipt = transition.get("data", {}).get("review_receipt", "")
    if decision == "approved" and receipt:
        payload = json.dumps(fields, sort_keys=True)
        target_session = persist_session_id or run_id
        traces.extend(
            [
                _trace(
                    "store_to_gcs", store_to_gcs(patient_id, target_session, payload)
                ),
                _trace(
                    "persist_extraction_relational",
                    persist_extraction_relational(
                        patient_id, target_session, payload, receipt
                    ),
                ),
                _trace(
                    "persist_extraction_vector",
                    persist_extraction_vector(
                        patient_id, target_session, payload, receipt
                    ),
                ),
            ]
        )
    traces.append(
        _trace(
            "log_audit_event",
            log_audit_event(
                "extraction_audit_agent",
                f"extraction_{decision}",
                patient_id,
                json.dumps({"run_id": run_id, "reviewer": reviewer}),
            ),
        )
    )
    return traces


def qa_tools(
    patient_id: str, question: str, source_types: list[str], date_range: str
) -> list[dict[str, Any]]:
    """Run validation, retrieval, citation, synthesis, and audit tools."""

    mapped_types = ["structured" if item == "lab" else item for item in source_types]
    source_filter = ",".join(mapped_types) if mapped_types else "all"
    days = 30 if date_range == "30d" else 365 if date_range == "1y" else 180
    validation = validate_qa_request(patient_id, question, source_filter, days)
    patient = lookup_patient_record(patient_id)
    notes = search_clinical_notes(patient_id, question, days)
    vectors = search_vector_store(question, patient_id, source_filter)
    images = retrieve_imaging_evidence(patient_id, question)
    evidence_items = notes.get("data", {}).get("results", []) + vectors.get(
        "data", {}
    ).get("results", [])
    citations = build_citations(json.dumps(evidence_items))
    answer = compose_clinical_answer(
        question,
        json.dumps(patient.get("data", {})),
        json.dumps(evidence_items),
        json.dumps(images.get("data", {})),
        json.dumps(citations.get("data", {})),
    )
    audit = log_audit_event(
        "qa_audit_agent",
        "question_answered",
        patient_id,
        json.dumps(
            {"source_types": source_filter, "source_count": len(evidence_items)}
        ),
    )
    return [
        _trace("validate_qa_request", validation),
        _trace("lookup_patient_record", patient),
        _trace("search_clinical_notes", notes),
        _trace("search_vector_store", vectors),
        _trace("retrieve_imaging_evidence", images),
        _trace("build_citations", citations),
        _trace("compose_clinical_answer", answer),
        _trace("log_audit_event", audit),
    ]


def database_preview_tools(question: str, sql: str) -> list[dict[str, Any]]:
    """Run schema discovery, generation context, validation, and audit tools."""

    schema = get_database_schema("patients")
    generated = generate_sql(
        question, schema.get("data", {}).get("schema_ddl", "patients")
    )
    safety = validate_sql_safety(sql)
    audit = log_audit_event(
        "sql_validator_agent",
        "database_preview_generated",
        details=json.dumps(
            {"question": question, "safe": safety.get("data", {}).get("safe", False)}
        ),
    )
    return [
        _trace("get_database_schema", schema),
        _trace("generate_sql", generated),
        _trace("validate_sql_safety", safety),
        _trace("log_audit_event", audit),
    ]


def database_execution_tools(
    question: str, sql: str, rows: list[dict[str, Any]], approver: str
) -> list[dict[str, Any]]:
    """Run explicit SQL approval, execution, chart, and audit tool contracts."""

    approval = approve_sql_preview(sql, approver)
    receipt = approval.get("data", {}).get("approval_receipt", "")
    execution = execute_approved_clinical_query(sql, receipt)
    chart = generate_chart_spec(
        json.dumps({"columns": list(rows[0]) if rows else [], "rows": rows}), question
    )
    audit = log_audit_event(
        "insight_chart_agent",
        "database_query_executed",
        details=json.dumps({"approver": approver, "row_count": len(rows)}),
    )
    return [
        _trace("approve_sql_preview", approval),
        _trace("execute_approved_clinical_query", execution),
        _trace("generate_chart_spec", chart),
        _trace("log_audit_event", audit),
    ]
