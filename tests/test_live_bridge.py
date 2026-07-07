"""Unit tests for the live-mode ADK bridge parsing helpers.

Pure-function coverage for field, SQL, and confidence extraction — no model
call, no API key, no ADK runtime required.
"""

from clinical_app.live_bridge import (
    _extract_confidence,
    _extract_fields,
    _extract_sql,
    _string_source,
)


class TestExtractFields:
    """_extract_fields must tolerate nested JSON, code fences, and prose."""

    def test_flat_json(self) -> None:
        assert _extract_fields('{"bp": "120/80", "hr": "72"}') == {"bp": "120/80", "hr": "72"}

    def test_nested_json_values_serialized(self) -> None:
        fields = _extract_fields('{"vitals": {"bp": "120/80"}, "note": "stable"}')
        assert fields["note"] == "stable"
        assert fields["vitals"] == '{"bp": "120/80"}'

    def test_json_inside_code_fence(self) -> None:
        text = 'Findings below.\n```json\n{"diagnosis": "T2DM", "confidence": 0.91}\n```'
        fields = _extract_fields(text)
        assert fields["diagnosis"] == "T2DM"

    def test_json_embedded_in_prose(self) -> None:
        text = 'The structured result is {"finding": "lesion", "site": {"organ": "liver"}} as extracted.'
        fields = _extract_fields(text)
        assert fields["finding"] == "lesion"
        assert fields["site"] == '{"organ": "liver"}'

    def test_line_based_fallback(self) -> None:
        text = "Diagnosis: hypertension\n- Medication: lisinopril\n# heading: ignored"
        fields = _extract_fields(text)
        assert fields["Diagnosis"] == "hypertension"
        assert fields["Medication"] == "lisinopril"
        assert "heading" not in fields

    def test_no_structure_returns_empty(self) -> None:
        assert _extract_fields("plain narrative with no delimiters") == {}


class TestExtractSql:
    """_extract_sql pulls the first SELECT statement out of agent text."""

    def test_plain_select(self) -> None:
        sql = _extract_sql("SELECT risk_level FROM patients_core;")
        assert sql == "SELECT risk_level FROM patients_core"

    def test_select_inside_narration(self) -> None:
        sql = _extract_sql("Here is the query:\nSELECT COUNT(*) FROM sessions WHERE date > '2026-01-01'")
        assert sql.startswith("SELECT COUNT(*)")

    def test_no_select_returns_empty(self) -> None:
        assert _extract_sql("I could not generate a query for that request.") == ""

    def test_cte_kept_whole(self) -> None:
        """WITH ... AS (SELECT ...) must not be sliced at the inner SELECT."""

        text = "WITH diabetics AS (SELECT patient_id FROM patient_conditions) SELECT p.name FROM patients_core p JOIN diabetics d ON p.patient_id = d.patient_id;"
        sql = _extract_sql(text)
        assert sql.startswith("WITH diabetics AS (SELECT")
        assert sql.endswith("d.patient_id")

    def test_fenced_sql_preferred_over_prose(self) -> None:
        """The ```sql fence the prompts require wins over SELECT-ish prose."""

        text = "The word SELECT appears here first.\n```sql\nWITH recent AS (SELECT 1) SELECT * FROM lab_results\n```\nDone."
        assert _extract_sql(text) == "WITH recent AS (SELECT 1) SELECT * FROM lab_results"


class TestStringSource:
    """_string_source prefers earlier state keys and serializes structured values."""

    def test_prefers_first_available_key(self) -> None:
        outputs = {"validated_sql": "SELECT 1", "generated_sql": "SELECT 2"}
        assert _string_source(outputs, ("validated_sql", "generated_sql")) == "SELECT 1"

    def test_falls_through_empty_values(self) -> None:
        outputs = {"validated_sql": "  ", "generated_sql": "SELECT 2"}
        assert _string_source(outputs, ("validated_sql", "generated_sql")) == "SELECT 2"

    def test_serializes_dict_values(self) -> None:
        outputs = {"structured_output": {"finding": "lesion"}}
        assert _string_source(outputs, ("structured_output",)) == '{"finding": "lesion"}'

    def test_missing_keys_return_empty(self) -> None:
        assert _string_source({}, ("structured_output",)) == ""


class TestExtractConfidence:
    """_extract_confidence normalizes percentages and defaults sensibly."""

    def test_percentage(self) -> None:
        assert _extract_confidence("Overall confidence: 92%") == 0.92

    def test_fraction(self) -> None:
        assert _extract_confidence("confidence 0.75 across fields") == 0.75

    def test_default_when_absent(self) -> None:
        assert _extract_confidence("no score present") == 0.85


class TestIsTransient:
    """_is_transient must retry only genuine transient model failures."""

    def test_transient_signatures_match(self) -> None:
        from clinical_app.live_bridge import _is_transient

        for message in (
            "429 RESOURCE_EXHAUSTED: quota exceeded",
            "Service UNAVAILABLE, please retry",
            "HTTP 503 from upstream",
            "DEADLINE exceeded while streaming",
            "the model is overloaded",
        ):
            assert _is_transient(message)

    def test_permanent_failures_do_not_match(self) -> None:
        from clinical_app.live_bridge import _is_transient

        for message in (
            "Live ADK runtime unavailable: No module named 'google.adk'",
            "invalid credentials",
            "PERMISSION_DENIED: caller lacks role",
            "400 INVALID_ARGUMENT",
        ):
            assert not _is_transient(message)
