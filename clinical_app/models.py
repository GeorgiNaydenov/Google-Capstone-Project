"""Pydantic contracts for the clinician product API."""

from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from clinical_app.document import MAX_UPLOAD_BYTES


Role = Literal["clinician", "admin"]


class UploadRequest(BaseModel):
    """Metadata for a clinical file selected by a user."""

    filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(default="application/octet-stream", max_length=100)
    size_bytes: int = Field(ge=1, le=MAX_UPLOAD_BYTES)
    modality: str = Field(default="Document", max_length=50)


class RunRequest(BaseModel):
    """Request to start deterministic extraction for uploaded evidence."""

    model_config = ConfigDict(populate_by_name=True)

    patient_id: str = Field(validation_alias=AliasChoices("patientId", "patient_id"))
    upload_ids: list[str] = Field(default_factory=list, validation_alias=AliasChoices("uploadIds", "upload_ids"))
    asset_id: str | None = Field(default=None, validation_alias=AliasChoices("assetId", "asset_id"))


class ReviewRequest(BaseModel):
    """Clinician decision on an extraction run."""

    decision: Literal["approved", "rejected"]
    comment: str = Field(default="", max_length=1000)
    field_updates: dict[str, Any] = Field(default_factory=dict, validation_alias=AliasChoices("fields", "field_updates"))


class QuestionRequest(BaseModel):
    """Patient-grounded clinical question."""

    model_config = ConfigDict(populate_by_name=True)

    patient_id: str = Field(validation_alias=AliasChoices("patientId", "patient_id"))
    question: str = Field(min_length=3, max_length=2000)
    source_types: list[Literal["text", "image", "lab"]] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)


class DatabaseRequest(BaseModel):
    """Natural-language database intelligence request."""

    question: str = Field(min_length=3, max_length=1000)


class OrchestrateRequest(BaseModel):
    """Natural-language workflow routing request."""

    model_config = ConfigDict(populate_by_name=True)

    query: str = Field(min_length=3, max_length=2000)
    patient_id: str | None = Field(default=None, validation_alias=AliasChoices("patientId", "patient_id"))


class ExecuteRequest(BaseModel):
    """Approved preview identifier for deterministic execution."""

    preview_id: str


class ApiMessage(BaseModel):
    """Simple API status message."""

    status: str
    details: dict[str, Any] = Field(default_factory=dict)
