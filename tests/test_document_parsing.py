"""Document upload policy and extraction contract tests."""

import pytest
from pydantic import ValidationError

from clinical_app.document import (
    MAX_UPLOAD_BYTES,
    UploadPolicyError,
    UnsupportedUploadTypeError,
    parse_upload,
    validate_upload,
)
from clinical_app.models import UploadRequest


PDF_BYTES = b"%PDF-1.4\n% synthetic clinical document\n"
PNG_BYTES = b"\x89PNG\r\n\x1a\nsynthetic image bytes"


def test_validate_upload_accepts_supported_pdf_signature() -> None:
    """PDF uploads must validate by size, declared type, extension, and signature."""

    metadata = validate_upload(PDF_BYTES, "application/pdf", "report.pdf")

    assert metadata["contentType"] == "application/pdf"
    assert metadata["sizeBytes"] == len(PDF_BYTES)
    assert metadata["kind"] == "PDF"


def test_validate_upload_rejects_unsupported_file_type() -> None:
    """Unsupported files should fail before entering the repository."""

    with pytest.raises(UnsupportedUploadTypeError):
        validate_upload(b"plain text", "text/plain", "note.txt")


def test_validate_upload_rejects_content_type_signature_mismatch() -> None:
    """A renamed image should not be accepted as a PDF."""

    with pytest.raises(UploadPolicyError):
        validate_upload(PNG_BYTES, "application/pdf", "scan.pdf")


def test_parse_pdf_returns_agent_ready_contract() -> None:
    """PDF extraction should always expose pages, images, tables, warnings, and provenance."""

    parsed = parse_upload(PDF_BYTES, "application/pdf", "report.pdf")

    assert parsed["type"] == "pdf"
    assert parsed["mimeType"] == "application/pdf"
    assert parsed["filename"] == "report.pdf"
    assert parsed["checksum"]
    assert isinstance(parsed["pages"], list)
    assert isinstance(parsed["images"], list)
    assert isinstance(parsed["tables"], list)
    assert isinstance(parsed["warnings"], list)


def test_parse_image_returns_image_contract_and_ocr_warning() -> None:
    """Image extraction should expose image metadata fields and flag OCR as agent work."""

    parsed = parse_upload(PNG_BYTES, "image/png", "evidence.png")

    assert parsed["type"] == "image"
    assert parsed["imageCount"] == 1
    assert parsed["images"][0]["mimeType"] == "image/png"
    assert "image_text_extraction_requires_ocr_or_vision_agent" in parsed["warnings"]


def test_upload_request_uses_shared_10mb_limit() -> None:
    """Pydantic metadata should reject the same max size as the upload endpoint."""

    UploadRequest(filename="evidence.png", content_type="image/png", size_bytes=MAX_UPLOAD_BYTES)
    with pytest.raises(ValidationError):
        UploadRequest(filename="evidence.png", content_type="image/png", size_bytes=MAX_UPLOAD_BYTES + 1)
