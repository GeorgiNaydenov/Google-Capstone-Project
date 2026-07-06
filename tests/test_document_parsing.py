"""Document upload policy and extraction contract tests."""

import io
import json
import zipfile

import pytest
from pydantic import ValidationError

from clinical_app.document import (
    MAX_UPLOAD_BYTES,
    UploadPolicyError,
    UnsupportedUploadTypeError,
    parse_knowledge_base_upload,
    parse_upload,
    validate_knowledge_base_upload,
    validate_upload,
)
from clinical_app.models import UploadRequest


PDF_BYTES = b"%PDF-1.4\n% synthetic clinical document\n"
PNG_BYTES = b"\x89PNG\r\n\x1a\nsynthetic image bytes"


def docx_bytes(text: str) -> bytes:
    """Create a minimal valid DOCX package for parser tests."""

    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body></w:document>"
    )
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", document_xml)
    return buf.getvalue()


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


@pytest.mark.parametrize(
    ("filename", "contents", "content_type", "expected_type"),
    [
        ("summary.md", b"# Plan\nBNP rising", "text/markdown", "text/markdown"),
        ("note.txt", b"plain clinical text", "text/plain", "text/plain"),
        ("facts.json", json.dumps({"care_gap": "BNP follow-up"}).encode(), "application/json", "application/json"),
        ("packet.docx", docx_bytes("DOCX clinical care gap"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("scan.png", PNG_BYTES, "image/png", "image/png"),
    ],
)
def test_knowledge_base_upload_accepts_searchable_formats(filename: str, contents: bytes, content_type: str, expected_type: str) -> None:
    """Knowledge-base uploads support mixed document formats outside extraction policy."""

    metadata = validate_knowledge_base_upload(contents, content_type, filename)
    parsed = parse_knowledge_base_upload(contents, expected_type, filename)

    assert metadata["contentType"] == expected_type
    assert parsed["knowledgeBase"] is True
    assert parsed["textPreview"]


def test_agent_document_processor_supports_knowledge_base_formats(tmp_path) -> None:
    """ADK upload_document path can read generated DOCX, Markdown, TXT, and JSON files."""

    from capstone_agent.document_processor import detect_content_type, extract_text_from_docx, extract_text_from_json, extract_text_from_plaintext

    docx_path = tmp_path / "summary.docx"
    json_path = tmp_path / "facts.json"
    md_path = tmp_path / "note.md"
    docx_path.write_bytes(docx_bytes("DOCX longitudinal evidence"))
    json_path.write_text(json.dumps({"signal": "abnormal CRP"}), encoding="utf-8")
    md_path.write_text("# Evidence\nabnormal BNP", encoding="utf-8")

    assert detect_content_type(str(docx_path)).endswith("wordprocessingml.document")
    assert detect_content_type(str(md_path)) == "text/markdown"
    assert "DOCX longitudinal evidence" in extract_text_from_docx(str(docx_path))["text"]
    assert "abnormal CRP" in extract_text_from_json(str(json_path))["text"]
    assert "abnormal BNP" in extract_text_from_plaintext(str(md_path))["text"]


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
