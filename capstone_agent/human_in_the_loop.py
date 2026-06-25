"""Human-in-the-loop / long-running operations (Day 2b).

Clinical workflows require human oversight for consequential decisions:
- Low-confidence extraction fields need clinician verification
- Treatment-affecting data changes require physician approval
- Bulk patient record modifications need administrative sign-off

ADK's pattern is a *long-running tool* that PAUSES the run to request a
human decision, then RESUMES exactly where it left off once the decision
arrives.

Three execution paths inside one tool (the canonical Day 2b shape):
1. Auto-approve  — the request meets confidence thresholds → proceed.
2. First call    — needs review → `tool_context.request_confirmation(...)`
   and return a "pending_review" status. ADK suspends the invocation.
3. Resume call   — the clinician answered → `tool_context.tool_confirmation`
   tells you approved/rejected → finish accordingly.

Wiring (see app.py): the agent must run inside an `App` with
`ResumabilityConfig(is_resumable=True)` so state survives the pause, and
the tool must be registered as a `LongRunningFunctionTool`.
"""

from typing import Any

from google.adk.tools.tool_context import ToolContext

from .observability import log_security_event

# Extraction fields with confidence above this threshold auto-approve.
# Below it, a clinician must verify before the data enters the record.
CONFIDENCE_THRESHOLD = 0.80

# Actions affecting more than this many patient records need admin approval.
BULK_RECORD_THRESHOLD = 5


def request_sensitive_action(
    action_type: str,
    patient_id: str,
    details: str,
    confidence: float = 1.0,
    affected_records: int = 1,
    tool_context: ToolContext = None,
) -> dict[str, Any]:
    """Pause for clinical review when an action needs human oversight.

    Covers three clinical scenarios:
    - extraction_review: AI-extracted data below confidence threshold
    - treatment_data_change: modifications to treatment-affecting records
    - bulk_modification: changes spanning multiple patient records

    Auto-approves when confidence is high and scope is small.
    Otherwise pauses the pipeline for clinician or admin review.

    Args:
        action_type: One of 'extraction_review', 'treatment_data_change',
            'bulk_modification', or a custom action label.
        patient_id: The patient this action concerns (for audit trail).
        details: Human-readable description of what needs review.
        confidence: Confidence score (0-1) for extraction reviews.
            Actions above CONFIDENCE_THRESHOLD auto-approve.
        affected_records: Number of records affected. Bulk changes
            above BULK_RECORD_THRESHOLD always require admin approval.
        tool_context: ADK ToolContext (injected automatically by the framework).

    Returns:
        A status dict: 'approved' (done), 'pending_review' (awaiting
        clinician), or 'rejected' (clinician declined).
    """
    # --- Path 1: auto-approve low-risk actions ---
    is_high_confidence = confidence >= CONFIDENCE_THRESHOLD
    is_small_scope = affected_records <= BULK_RECORD_THRESHOLD
    is_routine = action_type not in ("treatment_data_change", "bulk_modification")

    if is_high_confidence and is_small_scope and is_routine:
        return {
            "status": "approved",
            "action_type": action_type,
            "patient_id": patient_id,
            "message": (
                f"Auto-approved: confidence {confidence:.2f} >= {CONFIDENCE_THRESHOLD}, "
                f"{affected_records} record(s) affected."
            ),
        }

    # --- Path 3: resuming after clinician decision ---
    if tool_context and tool_context.tool_confirmation is not None:
        if tool_context.tool_confirmation.confirmed:
            log_security_event(
                "clinical_review_approved",
                {
                    "action_type": action_type,
                    "patient_id": patient_id,
                    "confidence": confidence,
                },
            )
            return {
                "status": "approved",
                "action_type": action_type,
                "patient_id": patient_id,
                "message": f"Clinician approved: {details}",
            }
        log_security_event(
            "clinical_review_rejected",
            {
                "action_type": action_type,
                "patient_id": patient_id,
                "confidence": confidence,
            },
        )
        return {
            "status": "rejected",
            "action_type": action_type,
            "patient_id": patient_id,
            "message": f"Clinician rejected: {details}. No changes applied.",
        }

    # --- Path 2: first call → pause for clinical review ---
    if action_type == "extraction_review":
        hint = (
            f"CLINICAL REVIEW REQUIRED — Patient {patient_id}\n"
            f"Extraction confidence: {confidence:.2f} (threshold: {CONFIDENCE_THRESHOLD})\n"
            f"Details: {details}\n"
            "Please verify the extracted data before it enters the patient record."
        )
    elif action_type == "bulk_modification":
        hint = (
            f"ADMIN APPROVAL REQUIRED — {affected_records} records affected\n"
            f"Patient: {patient_id}\n"
            f"Details: {details}\n"
            "This bulk operation requires administrative sign-off."
        )
    else:
        hint = (
            f"CLINICIAN APPROVAL REQUIRED — Patient {patient_id}\n"
            f"Action: {action_type}\n"
            f"Details: {details}\n"
            "This action may affect treatment decisions. Please review."
        )

    log_security_event(
        "clinical_review_requested",
        {
            "action_type": action_type,
            "patient_id": patient_id,
            "confidence": confidence,
            "affected_records": affected_records,
        },
    )

    if tool_context:
        tool_context.request_confirmation(
            hint=hint,
            payload={
                "action_type": action_type,
                "patient_id": patient_id,
                "details": details,
                "confidence": confidence,
                "affected_records": affected_records,
            },
        )

    return {
        "status": "pending_review",
        "action_type": action_type,
        "patient_id": patient_id,
        "message": f"Awaiting clinical review: {details}",
    }


def find_pending_confirmation(events: list) -> dict[str, Any] | None:
    """Scan a run's events for a pending tool-confirmation request.

    A driver loop calls this after `runner.run_async(...)`. If it returns a
    dict, the run paused awaiting a clinician decision; resume with the same
    `invocation_id` and a FunctionResponse carrying the clinician's answer.

    Args:
        events: The events collected from one `run_async` pass.

    Returns:
        {'invocation_id', 'function_call_id', 'hint'} if a confirmation is
        pending, else None.
    """
    for event in events:
        actions = getattr(event, "actions", None)
        requested = getattr(actions, "requested_tool_confirmations", None) if actions else None
        if requested:
            function_call_id, confirmation = next(iter(requested.items()))
            return {
                "invocation_id": getattr(event, "invocation_id", None),
                "function_call_id": function_call_id,
                "hint": getattr(confirmation, "hint", ""),
            }
    return None
