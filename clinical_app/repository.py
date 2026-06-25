"""Session-isolated mutable repository for deterministic product demos."""

from copy import deepcopy
from datetime import UTC, datetime
from collections import OrderedDict
from time import monotonic
from threading import Lock
from typing import Any


PATIENTS = [
    {"patient_id": "PT-8829", "name": "Jonathan Doe", "age": 62, "sex": "Male", "risk_level": "high", "primary_diagnosis": "Non-small cell lung cancer (NSCLC)", "assigned_clinician": "Dr. Sarah Chen", "last_session_date": "2026-06-15", "data_completeness_score": 0.92, "open_tasks": 2, "ai_review_status": "needs_review"},
    {"patient_id": "PT-1044", "name": "Sarah Smith", "age": 45, "sex": "Female", "risk_level": "needs_review", "primary_diagnosis": "Type 2 Diabetes Mellitus with complications", "assigned_clinician": "Dr. Michael Torres", "last_session_date": "2026-06-12", "data_completeness_score": 0.78, "open_tasks": 3, "ai_review_status": "needs_review"},
    {"patient_id": "PT-5510", "name": "Wei Chen", "age": 38, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Major depressive disorder, recurrent", "assigned_clinician": "Dr. Emily Nakamura", "last_session_date": "2026-06-18", "data_completeness_score": 0.95, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-9921", "name": "Maria Garcia", "age": 71, "sex": "Female", "risk_level": "needs_review", "primary_diagnosis": "Congestive heart failure", "assigned_clinician": "Dr. Sarah Chen", "last_session_date": "2026-06-10", "data_completeness_score": 0.65, "open_tasks": 4, "ai_review_status": "needs_review"},
]

PATIENTS += [
    {"patient_id": "PT-1029", "name": "Eleanor Kim", "age": 67, "sex": "Female", "risk_level": "high", "primary_diagnosis": "Chronic kidney disease, stage 4", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-22", "data_completeness_score": 0.88, "open_tasks": 3, "ai_review_status": "needs_review"},
    {"patient_id": "PT-3842", "name": "David Okafor", "age": 59, "sex": "Male", "risk_level": "high", "primary_diagnosis": "Acute coronary syndrome follow-up", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-21", "data_completeness_score": 0.84, "open_tasks": 2, "ai_review_status": "needs_review"},
    {"patient_id": "PT-7714", "name": "Amelia Rossi", "age": 73, "sex": "Female", "risk_level": "high", "primary_diagnosis": "Aortic stenosis, severe", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-20", "data_completeness_score": 0.91, "open_tasks": 2, "ai_review_status": "verified"},
    {"patient_id": "PT-2388", "name": "Noah Williams", "age": 52, "sex": "Male", "risk_level": "needs_review", "primary_diagnosis": "Crohn disease with recent flare", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-19", "data_completeness_score": 0.76, "open_tasks": 2, "ai_review_status": "needs_review"},
    {"patient_id": "PT-6503", "name": "Priya Nair", "age": 41, "sex": "Female", "risk_level": "needs_review", "primary_diagnosis": "Systemic lupus erythematosus", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-17", "data_completeness_score": 0.81, "open_tasks": 1, "ai_review_status": "needs_review"},
    {"patient_id": "PT-4337", "name": "Lucas Martin", "age": 64, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "COPD, GOLD stage II", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-16", "data_completeness_score": 0.96, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-8195", "name": "Aisha Rahman", "age": 36, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Multiple sclerosis, relapsing-remitting", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-15", "data_completeness_score": 0.93, "open_tasks": 1, "ai_review_status": "verified"},
    {"patient_id": "PT-2971", "name": "Henry Brooks", "age": 70, "sex": "Male", "risk_level": "needs_review", "primary_diagnosis": "Parkinson disease", "assigned_clinician": "Dr. James Patel", "last_session_date": "2026-06-14", "data_completeness_score": 0.79, "open_tasks": 2, "ai_review_status": "needs_review"},
    {"patient_id": "PT-5602", "name": "Sofia Alvarez", "age": 28, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Ulcerative colitis", "assigned_clinician": "Dr. James Patel", "last_session_date": "2026-06-13", "data_completeness_score": 0.97, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-1448", "name": "Owen Hughes", "age": 55, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Hypertension with left ventricular hypertrophy", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-12", "data_completeness_score": 0.90, "open_tasks": 1, "ai_review_status": "verified"},
    {"patient_id": "PT-9064", "name": "Mei Tan", "age": 48, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Rheumatoid arthritis", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-11", "data_completeness_score": 0.94, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-3256", "name": "Samuel Reed", "age": 62, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Prostate cancer in remission", "assigned_clinician": "Dr. James Patel", "last_session_date": "2026-06-10", "data_completeness_score": 0.92, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-6841", "name": "Fatima Hassan", "age": 44, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Graves disease", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-09", "data_completeness_score": 0.89, "open_tasks": 1, "ai_review_status": "verified"},
    {"patient_id": "PT-4720", "name": "Jack Thompson", "age": 33, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Epilepsy, focal onset", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-08", "data_completeness_score": 0.95, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-7539", "name": "Isabella Costa", "age": 57, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Nonalcoholic steatohepatitis", "assigned_clinician": "Dr. James Patel", "last_session_date": "2026-06-07", "data_completeness_score": 0.87, "open_tasks": 1, "ai_review_status": "verified"},
    {"patient_id": "PT-2186", "name": "Robert Lewis", "age": 69, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Osteoarthritis, bilateral knees", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-06", "data_completeness_score": 0.98, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-5368", "name": "Grace Li", "age": 31, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Hashimoto thyroiditis", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-05", "data_completeness_score": 0.96, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-8650", "name": "Mateo Silva", "age": 46, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Obstructive sleep apnea", "assigned_clinician": "Dr. James Patel", "last_session_date": "2026-06-04", "data_completeness_score": 0.86, "open_tasks": 1, "ai_review_status": "verified"},
    {"patient_id": "PT-3492", "name": "Nora Evans", "age": 50, "sex": "Female", "risk_level": "stable", "primary_diagnosis": "Migraine with aura", "assigned_clinician": "Dr. Sarah Miller", "last_session_date": "2026-06-03", "data_completeness_score": 0.93, "open_tasks": 0, "ai_review_status": "verified"},
    {"patient_id": "PT-6177", "name": "Adam Kowalski", "age": 39, "sex": "Male", "risk_level": "stable", "primary_diagnosis": "Psoriatic arthritis", "assigned_clinician": "Dr. Elena Park", "last_session_date": "2026-06-02", "data_completeness_score": 0.91, "open_tasks": 0, "ai_review_status": "verified"},
]

SESSIONS = [
    {"session_id": "SES-8829-003", "patient_id": "PT-8829", "date": "2026-06-15", "uploaded_image_count": 2, "extraction_confidence": 0.87, "clinician_verification_status": "pending", "extracted_fields": [{"field_name": "primary_tumor_size", "value": "4.2cm", "confidence": 0.91}, {"field_name": "hepatic_lesion_count", "value": "3", "confidence": 0.88}]},
    {"session_id": "SES-1044-001", "patient_id": "PT-1044", "date": "2026-06-12", "uploaded_image_count": 1, "extraction_confidence": 0.72, "clinician_verification_status": "pending", "extracted_fields": [{"field_name": "retinopathy_grade", "value": "Moderate NPDR", "confidence": 0.79}]},
    {"session_id": "SES-5510-001", "patient_id": "PT-5510", "date": "2026-06-18", "uploaded_image_count": 1, "extraction_confidence": 0.94, "clinician_verification_status": "verified", "extracted_fields": [{"field_name": "phq9_score", "value": "8", "confidence": 0.96}]},
    {"session_id": "SES-9921-001", "patient_id": "PT-9921", "date": "2026-06-10", "uploaded_image_count": 1, "extraction_confidence": 0.85, "clinician_verification_status": "pending", "extracted_fields": [{"field_name": "cardiothoracic_ratio", "value": "0.62", "confidence": 0.89}]},
]

SESSIONS += [
    {"session_id": f"SES-{patient_id[3:]}-001", "patient_id": patient_id, "date": date, "uploaded_image_count": images, "extraction_confidence": confidence, "clinician_verification_status": status, "extracted_fields": []}
    for patient_id, date, images, confidence, status in (
        ("PT-1029", "2026-06-22", 2, 0.76, "pending"),
        ("PT-3842", "2026-06-21", 1, 0.82, "pending"),
        ("PT-7714", "2026-06-20", 3, 0.94, "verified"),
        ("PT-2388", "2026-06-19", 1, 0.79, "pending"),
        ("PT-6503", "2026-06-17", 2, 0.81, "pending"),
        ("PT-4337", "2026-06-16", 1, 0.96, "verified"),
        ("PT-8195", "2026-06-15", 2, 0.93, "verified"),
        ("PT-2971", "2026-06-14", 1, 0.74, "pending"),
    )
]

EVIDENCE = {
    "PT-8829": [{"source_id": "NOTE-8829-005", "source_type": "text", "date": "2026-06-15", "text": "CT shows RUL mass increased from 3.8cm to 4.2cm and three hepatic lesions, largest 3.5cm."}, {"source_id": "SES-8829-003", "source_type": "image", "date": "2026-06-15", "text": "CT abdomen shows three hepatic lesions."}],
    "PT-1044": [{"source_id": "NOTE-1044-002", "source_type": "text", "date": "2026-06-12", "text": "HbA1c is 8.2% with moderate non-proliferative diabetic retinopathy."}],
    "PT-5510": [{"source_id": "NOTE-5510-002", "source_type": "text", "date": "2026-06-18", "text": "PHQ-9 improved from 14 to 8; no suicidal ideation."}],
    "PT-9921": [{"source_id": "NOTE-9921-002", "source_type": "text", "date": "2026-06-10", "text": "CHF exacerbation with EF 35%, BNP 890, weight gain, and bilateral effusions."}],
}


def now() -> str:
    """Return stable-format UTC timestamp."""

    return datetime.now(UTC).isoformat()


class DemoRepository:
    """Mutable state belonging to exactly one browser demo session."""

    def __init__(self) -> None:
        self.session_id = ""
        self.is_demo = True
        self.reset()

    def reset(self) -> None:
        """Restore deterministic seed state."""

        self.patients = {item["patient_id"]: item for item in deepcopy(PATIENTS)}
        self.sessions = {item["session_id"]: item for item in deepcopy(SESSIONS)}
        self.evidence = deepcopy(EVIDENCE)
        self.source_assets: dict[str, tuple[bytes, str]] = {}
        for patient_id, evidence_rows in self.evidence.items():
            for evidence in evidence_rows:
                if evidence["source_type"] == "image":
                    asset_id = evidence["source_id"]
                    self.source_assets[asset_id] = (f"DEMO IMAGE {patient_id} {asset_id}".encode(), "image/png")
                    evidence["asset_id"] = asset_id
        self.uploads: dict[str, dict[str, Any]] = {}
        self.asset_contents: dict[str, bytes] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        self.previews: dict[str, dict[str, Any]] = {}
        self.query_history: list[dict[str, Any]] = []
        self.audit: list[dict[str, Any]] = []
        self.agent_config: dict[str, Any] = {
            "version": 1,
            "autoApprovalThreshold": 90,
            "reviewThreshold": 75,
            "maxConcurrentRuns": 8,
            "databaseEnabled": True,
        }
        self.notifications = [
            {"id": "NTF-001", "title": "Diuretic change below confidence", "detail": "PT-1029 extraction scored 76%; clinician verification required.", "severity": "critical", "agent": "Validation Agent", "createdAt": now(), "read": False, "route": "/app/inbox"},
            {"id": "NTF-002", "title": "High-risk cohort increased", "detail": "Four patients crossed the high-risk threshold this week.", "severity": "info", "agent": "Database Intelligence Agent", "createdAt": now(), "read": False, "route": "/app/overview"},
            {"id": "NTF-003", "title": "Re-run extraction with high resolution OCR", "detail": "PT-8829 has a prior extraction below the preferred confidence target.", "severity": "warning", "agent": "Image Quality Agent", "createdAt": now(), "read": False, "route": "/app/extraction?patient=PT-8829"},
        ]
        self.sequence = 0

    def identifier(self, prefix: str) -> str:
        """Create deterministic identifier within session state."""

        self.sequence += 1
        return f"{prefix}-{self.sequence:04d}"

    def log(self, action: str, actor: str, role: str, **details: Any) -> dict[str, Any]:
        """Append auditable product event."""

        event = {"audit_id": self.identifier("AUD"), "timestamp": now(), "action": action, "actor": actor, "role": role, "details": details}
        self.audit.append(event)
        return event


class LiveRepository:
    """Mutable state for real-data sessions — starts empty, accumulates from agent runs."""

    def __init__(self) -> None:
        self.session_id = ""
        self.is_demo = False
        self.patients: dict[str, dict[str, Any]] = {}
        self.sessions: dict[str, dict[str, Any]] = {}
        self.evidence: dict[str, list[dict[str, Any]]] = {}
        self.source_assets: dict[str, tuple[bytes, str]] = {}
        self.uploads: dict[str, dict[str, Any]] = {}
        self.asset_contents: dict[str, bytes] = {}
        self.runs: dict[str, dict[str, Any]] = {}
        self.previews: dict[str, dict[str, Any]] = {}
        self.query_history: list[dict[str, Any]] = []
        self.audit: list[dict[str, Any]] = []
        self.agent_config: dict[str, Any] = {
            "version": 1,
            "autoApprovalThreshold": 90,
            "reviewThreshold": 75,
            "maxConcurrentRuns": 8,
            "databaseEnabled": True,
        }
        self.notifications: list[dict[str, Any]] = []
        self.sequence = 0

    def reset(self) -> None:
        """Clear session data."""

        self.__init__()  # type: ignore[misc]

    def identifier(self, prefix: str) -> str:
        """Create identifier within session state."""

        self.sequence += 1
        return f"{prefix}-{self.sequence:04d}"

    def log(self, action: str, actor: str, role: str, **details: Any) -> dict[str, Any]:
        """Append auditable event."""

        event = {"audit_id": self.identifier("AUD"), "timestamp": now(), "action": action, "actor": actor, "role": role, "details": details}
        self.audit.append(event)
        return event

    def add_patient(self, patient_id: str, name: str, **kwargs: Any) -> dict[str, Any]:
        """Register a patient from extraction results."""

        patient = {
            "patient_id": patient_id, "name": name,
            "age": kwargs.get("age"), "sex": kwargs.get("sex"),
            "risk_level": kwargs.get("risk_level", "needs_review"),
            "primary_diagnosis": kwargs.get("diagnosis", ""),
            "assigned_clinician": kwargs.get("clinician", ""),
            "last_session_date": now()[:10],
            "data_completeness_score": 0.0,
            "open_tasks": 1,
            "ai_review_status": "needs_review",
        }
        self.patients[patient_id] = patient
        return patient


class RepositoryRegistry:
    """Thread-safe registry of isolated repositories, tenant-aware."""

    def __init__(self, max_count: int = 100, ttl_seconds: int = 3600) -> None:
        self._items: OrderedDict[str, tuple[DemoRepository | LiveRepository, float]] = OrderedDict()
        self._lock = Lock()
        self._max_count = max_count
        self._ttl_seconds = ttl_seconds

    def get(self, session_id: str, tenant: str = "default") -> DemoRepository | LiveRepository:
        """Return existing repository or create tenant-appropriate session state."""

        with self._lock:
            current = monotonic()
            expired = [key for key, (_, touched) in self._items.items() if current - touched > self._ttl_seconds]
            for key in expired:
                self._items.pop(key, None)
            if session_id in self._items:
                repository, _ = self._items.pop(session_id)
            else:
                repository = LiveRepository() if tenant == "live" else DemoRepository()
            self._items[session_id] = (repository, current)
            repository.session_id = session_id
            while len(self._items) > self._max_count:
                self._items.popitem(last=False)
            return repository

    def find(self, session_id: str) -> DemoRepository | LiveRepository | None:
        """Find existing session without creating state for invalid capability URLs."""

        with self._lock:
            entry = self._items.get(session_id)
            if not entry:
                return None
            repository, touched = entry
            if monotonic() - touched > self._ttl_seconds:
                self._items.pop(session_id, None)
                return None
            return repository
