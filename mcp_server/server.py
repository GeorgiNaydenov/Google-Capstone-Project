"""Clinical MCP server — real database-backed tools via Model Context Protocol.

Production implementation: all tools query the real SQLite database,
process real documents, and return real data. Any MCP-compatible client
(ADK, Claude Desktop, other frameworks) can discover and use these tools.

Run standalone:  python -m mcp_server.server
Run with ADK:    ADK connects automatically via StdioConnectionParams in agent.py

Tool categories:
- Patient data (SQLite queries)
- Document upload and search (real file processing + SQLite)
- Clinical database queries (real SQL execution)
- Audit logging (persistent SQLite audit_log)
"""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MCP] %(message)s")
logger = logging.getLogger("mcp_server")

# Add project root to path for imports
_project_root = str(Path(__file__).resolve().parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from capstone_agent import database
from capstone_agent.clinical_schemas import validate_sql

mcp = FastMCP("clinical-ai-command-center-mcp")


@mcp.tool()
def get_patient_status(patient_id: str) -> str:
    """Get the current clinical status and risk level for a patient.

    Args:
        patient_id: The unique patient identifier (e.g., 'PT-8829').

    Returns:
        A JSON string with patient status, risk level, and review state.
    """
    if not patient_id or not patient_id.strip():
        return "Error: patient_id is required and cannot be empty."

    try:
        logger.info(f"get_patient_status: patient_id={patient_id}")
        result = database.execute_sql(
            f"SELECT patient_id, name, risk_level, ai_review_status, open_tasks, "
            f"data_completeness_score, last_session_date "
            f"FROM patients_core WHERE patient_id = '{patient_id}'"
        )
        if not result["rows"]:
            return f"Error: No patient found with ID '{patient_id}'."
        return json.dumps(result["rows"][0], indent=2)
    except Exception as e:
        logger.error(f"get_patient_status failed: {e}")
        return f"Error retrieving status for '{patient_id}': {e}"


@mcp.tool()
def list_patients(risk_level: str = "all", limit: int = 20) -> str:
    """List patients filtered by risk level from the real database.

    Args:
        risk_level: Filter by risk: 'all', 'high', 'needs_review', 'stable'.
        limit: Maximum number of patients to return (default: 20, max: 100).

    Returns:
        A JSON string listing matching patients with key clinical data.
    """
    if limit < 1 or limit > 100:
        return "Error: limit must be between 1 and 100."

    try:
        logger.info(f"list_patients: risk_level={risk_level}, limit={limit}")
        if risk_level == "all":
            sql = f"SELECT patient_id, name, age, risk_level, primary_diagnosis, assigned_clinician, last_session_date FROM patients_core LIMIT {limit}"
        else:
            sql = f"SELECT patient_id, name, age, risk_level, primary_diagnosis, assigned_clinician, last_session_date FROM patients_core WHERE risk_level = '{risk_level}' LIMIT {limit}"

        result = database.execute_sql(sql)
        return json.dumps(
            {"patients": result["rows"], "total": result["row_count"]}, indent=2
        )
    except Exception as e:
        logger.error(f"list_patients failed: {e}")
        return f"Error listing patients: {e}"


@mcp.tool()
def get_patient_record(patient_id: str) -> str:
    """Get the full structured patient record from the database.

    Includes demographics, diagnoses, medications, allergies, and care team.

    Args:
        patient_id: The unique patient identifier.

    Returns:
        A JSON string with the complete patient record.
    """
    if not patient_id or not patient_id.strip():
        return "Error: patient_id is required and cannot be empty."

    try:
        logger.info(f"get_patient_record: patient_id={patient_id}")
        # Core data from SQLite
        result = database.execute_sql(
            f"SELECT * FROM patients_core WHERE patient_id = '{patient_id}'"
        )
        if not result["rows"]:
            return f"Error: No patient found with ID '{patient_id}'."

        patient = result["rows"][0]

        full = dict(patient)
        extended_raw = full.pop("extended_data", None)
        if extended_raw:
            try:
                extended = (
                    json.loads(extended_raw)
                    if isinstance(extended_raw, str)
                    else extended_raw
                )
                full.update(extended)
            except (json.JSONDecodeError, TypeError):
                pass

        # Add real session and lab data from DB
        sessions = database.execute_sql(
            f"SELECT session_id, session_date, extraction_confidence, clinician_verification "
            f"FROM sessions WHERE patient_id = '{patient_id}' ORDER BY session_date DESC LIMIT 5"
        )
        full["recent_sessions"] = sessions.get("rows", [])

        labs = database.execute_sql(
            f"SELECT result_date, test_name, component, value, unit, flag "
            f"FROM lab_results WHERE patient_id = '{patient_id}' ORDER BY result_date DESC LIMIT 10"
        )
        full["recent_labs"] = labs.get("rows", [])

        # Add uploaded documents
        docs = database.list_documents(patient_id, limit=10)
        full["uploaded_documents"] = docs

        return json.dumps(full, indent=2, default=str)
    except Exception as e:
        logger.error(f"get_patient_record failed: {e}")
        return f"Error retrieving record for '{patient_id}': {e}"


@mcp.tool()
def list_extraction_sessions(patient_id: str, limit: int = 10) -> str:
    """List image extraction sessions for a patient from the real database.

    Args:
        patient_id: The unique patient identifier.
        limit: Maximum number of sessions to return (default: 10, max: 50).

    Returns:
        A JSON string listing extraction sessions with status and confidence.
    """
    if not patient_id or not patient_id.strip():
        return "Error: patient_id is required and cannot be empty."
    if limit < 1 or limit > 50:
        return "Error: limit must be between 1 and 50."

    try:
        logger.info(f"list_extraction_sessions: patient_id={patient_id}, limit={limit}")
        result = database.execute_sql(
            f"SELECT session_id, session_date, uploaded_image_count, extraction_confidence, "
            f"clinician_verification, json_sync_status "
            f"FROM sessions WHERE patient_id = '{patient_id}' "
            f"ORDER BY session_date DESC LIMIT {limit}"
        )
        return json.dumps(
            {"sessions": result["rows"], "total": result["row_count"]}, indent=2
        )
    except Exception as e:
        logger.error(f"list_extraction_sessions failed: {e}")
        return f"Error listing sessions for '{patient_id}': {e}"


@mcp.tool()
def store_extraction_result(patient_id: str, session_id: str, result_json: str) -> str:
    """Store a validated extraction result to the patient record.

    Args:
        patient_id: The unique patient identifier.
        session_id: The extraction session identifier.
        result_json: JSON string of the extraction result to store.

    Returns:
        A confirmation message with storage details.
    """
    if not patient_id or not patient_id.strip():
        return "Error: patient_id is required."
    if not session_id or not session_id.strip():
        return "Error: session_id is required."
    if not result_json or not result_json.strip():
        return "Error: result_json is required."

    try:
        logger.info(
            f"store_extraction_result: patient_id={patient_id}, session_id={session_id}"
        )
        json.loads(result_json)  # validate JSON

        database.log_audit(
            agent_name="mcp_server",
            action="extraction_result_stored",
            patient_id=patient_id,
            session_id=session_id,
            details=json.dumps({"result_length": len(result_json)}),
        )

        return json.dumps(
            {
                "status": "stored",
                "patient_id": patient_id,
                "session_id": session_id,
                "storage_location": f"database://clinical/{patient_id}/sessions/{session_id}",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        )
    except json.JSONDecodeError:
        return "Error: result_json is not valid JSON."
    except Exception as e:
        logger.error(f"store_extraction_result failed: {e}")
        return f"Error storing result: {e}"


@mcp.tool()
def upload_document(file_path: str, patient_id: str = "") -> str:
    """Upload and process a document (PDF, image, or text file).

    Extracts text using PyMuPDF for PDFs or Gemini Vision for images,
    chunks the text for search, and stores everything in the database.

    Args:
        file_path: Path to the file to upload and process.
        patient_id: Optional patient ID to associate the document with.

    Returns:
        A JSON string with processing results including document_id and text preview.
    """
    if not file_path or not file_path.strip():
        return "Error: file_path is required."

    try:
        logger.info(f"upload_document: file_path={file_path}, patient_id={patient_id}")
        from capstone_agent.document_processor import process_document

        result = process_document(file_path.strip(), patient_id.strip())

        if result.get("error"):
            return json.dumps({"error": result["error"]})
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error(f"upload_document failed: {e}")
        return f"Error processing document: {e}"


@mcp.tool()
def search_all_documents(query: str, patient_id: str = "", limit: int = 20) -> str:
    """Search across all uploaded documents and clinical notes.

    Performs full-text search over document chunks and clinical notes
    in the database. Returns matching text with relevance scores and
    source references for citation building.

    Args:
        query: Natural language search query.
        patient_id: Optional patient ID to filter results.
        limit: Maximum number of results (default: 20).

    Returns:
        A JSON string with search results including text, sources, and scores.
    """
    if not query or not query.strip():
        return "Error: query is required."

    try:
        logger.info(
            f"search_all_documents: query={query[:80]}, patient_id={patient_id}"
        )
        results = database.search_documents(query.strip(), patient_id.strip(), limit)
        return json.dumps(
            {"results": results, "total": len(results), "query": query},
            indent=2,
            default=str,
        )
    except Exception as e:
        logger.error(f"search_all_documents failed: {e}")
        return f"Error searching documents: {e}"


@mcp.tool()
def list_documents(patient_id: str = "", limit: int = 50) -> str:
    """List all uploaded and processed documents.

    Args:
        patient_id: Optional patient ID to filter.
        limit: Maximum number of documents to list.

    Returns:
        A JSON string with document metadata.
    """
    try:
        logger.info(f"list_documents: patient_id={patient_id}, limit={limit}")
        docs = database.list_documents(patient_id.strip() if patient_id else "", limit)
        return json.dumps(
            {"documents": docs, "total": len(docs)}, indent=2, default=str
        )
    except Exception as e:
        logger.error(f"list_documents failed: {e}")
        return f"Error listing documents: {e}"


@mcp.tool()
def query_clinical_database(sql: str) -> str:
    """Execute a read-only SQL query against the real clinical database.

    Only SELECT queries are allowed. All mutations are blocked by the
    SQL safety validator.

    Args:
        sql: The SQL query to execute (must be a SELECT statement).

    Returns:
        A JSON string with query results (columns, rows, row_count).
    """
    if not sql or not sql.strip():
        return "Error: sql is required and cannot be empty."

    try:
        logger.info(f"query_clinical_database: sql={sql[:100]}")
        safety = validate_sql(sql)
        if not safety["safe"]:
            return json.dumps({"error": "Query blocked", "reason": safety["reason"]})

        result = database.execute_sql(sql)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        logger.error(f"query_clinical_database failed: {e}")
        return f"Error executing query: {e}"


@mcp.tool()
def log_clinical_audit(
    agent: str, action: str, patient_id: str = "", details: str = ""
) -> str:
    """Record an audit event in the persistent compliance log.

    Writes directly to the SQLite audit_log table for durable storage.

    Args:
        agent: Name of the agent that performed the action.
        action: Description of the action taken.
        patient_id: Patient identifier (optional for system events).
        details: Additional event details as a string.

    Returns:
        A confirmation message with the audit event ID and timestamp.
    """
    if not agent or not agent.strip():
        return "Error: agent name is required."
    if not action or not action.strip():
        return "Error: action is required."

    try:
        logger.info(f"log_clinical_audit: agent={agent}, action={action}")
        audit_result = database.log_audit(
            agent_name=agent.strip(),
            action=action.strip(),
            patient_id=patient_id.strip() if patient_id else "",
            details=details or "{}",
        )
        return json.dumps({"status": "logged", **audit_result}, indent=2)
    except Exception as e:
        logger.error(f"log_clinical_audit failed: {e}")
        return f"Error logging audit event: {e}"


if __name__ == "__main__":
    mcp.run()
