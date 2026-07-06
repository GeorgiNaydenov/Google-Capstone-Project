"""Document parsing and upload policy for clinical evidence files."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


MAX_UPLOAD_BYTES = 10_000_000
SUPPORTED_UPLOAD_TYPES = {
    "application/pdf": "PDF",
    "image/jpeg": "JPEG image",
    "image/png": "PNG image",
    "image/webp": "WEBP image",
}
EXTENSION_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
SUPPORTED_KNOWLEDGE_BASE_TYPES = {
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "text/markdown": "Markdown",
    "text/plain": "Plain text",
    "application/json": "JSON",
    "image/jpeg": "JPEG image",
    "image/png": "PNG image",
    "image/webp": "WEBP image",
}
KNOWLEDGE_BASE_EXTENSION_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".json": "application/json",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}


class UploadPolicyError(ValueError):
    """Upload failed a documented evidence-ingestion policy."""

    status_code = 422


class UploadTooLargeError(UploadPolicyError):
    """Upload exceeds the process-memory boundary."""

    status_code = 413


class UnsupportedUploadTypeError(UploadPolicyError):
    """Upload uses a media type the extraction workflow cannot parse."""

    status_code = 415


def validate_upload(contents: bytes, content_type: str, filename: str) -> dict[str, str | int]:
    """Validate size, MIME type, extension, and file signature before storage."""

    if len(contents) > MAX_UPLOAD_BYTES:
        raise UploadTooLargeError("Uploaded file exceeds 10 MB")

    normalized_type = _normalize_content_type(content_type)
    extension_type = EXTENSION_MIME_TYPES.get(Path(filename or "").suffix.lower())
    signature_type = _detect_mime(contents)

    if normalized_type not in SUPPORTED_UPLOAD_TYPES and extension_type is None:
        raise UnsupportedUploadTypeError("Supported uploads are PDF, JPEG, PNG, and WEBP files up to 10 MB")

    if normalized_type in SUPPORTED_UPLOAD_TYPES and extension_type and normalized_type != extension_type:
        raise UploadPolicyError("File extension does not match the declared content type")

    if signature_type is None:
        raise UploadPolicyError("File signature could not be verified")

    if normalized_type in SUPPORTED_UPLOAD_TYPES and normalized_type != signature_type:
        raise UploadPolicyError("File signature does not match the declared content type")

    if extension_type and extension_type != signature_type:
        raise UploadPolicyError("File signature does not match the filename extension")

    return {
        "filename": filename or "upload",
        "contentType": signature_type,
        "sizeBytes": len(contents),
        "kind": SUPPORTED_UPLOAD_TYPES[signature_type],
    }


def validate_knowledge_base_upload(contents: bytes, content_type: str, filename: str) -> dict[str, str | int]:
    """Validate a searchable knowledge-base document without widening extraction uploads."""

    if len(contents) > MAX_UPLOAD_BYTES:
        raise UploadTooLargeError("Uploaded file exceeds 10 MB")

    extension = Path(filename or "").suffix.lower()
    expected_type = KNOWLEDGE_BASE_EXTENSION_MIME_TYPES.get(extension)
    if expected_type is None:
        raise UnsupportedUploadTypeError("Knowledge-base uploads support DOCX, PDF, MD, TXT, JSON, JPEG, PNG, and WEBP files up to 10 MB")

    normalized_type = _normalize_content_type(content_type)
    declared_type = _coerce_knowledge_base_type(normalized_type, expected_type)
    if declared_type != expected_type:
        raise UploadPolicyError("File extension does not match the declared content type")

    if expected_type == "application/pdf" and not contents.startswith(b"%PDF"):
        raise UploadPolicyError("PDF signature could not be verified")
    if expected_type.endswith("wordprocessingml.document") and not _looks_like_docx(contents):
        raise UploadPolicyError("DOCX package could not be verified")
    if expected_type == "application/json":
        try:
            json.loads(_decode_text(contents))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise UploadPolicyError("JSON document could not be parsed") from exc
    if expected_type in {"text/markdown", "text/plain"}:
        try:
            _decode_text(contents)
        except UnicodeDecodeError as exc:
            raise UploadPolicyError("Text document could not be decoded as UTF-8") from exc
    if expected_type.startswith("image/") and _detect_mime(contents) != expected_type:
        raise UploadPolicyError("Image signature does not match the filename extension")

    return {
        "filename": filename or f"upload{extension}",
        "contentType": expected_type,
        "sizeBytes": len(contents),
        "kind": SUPPORTED_KNOWLEDGE_BASE_TYPES[expected_type],
    }


def parse_upload(contents: bytes, content_type: str, filename: str) -> dict[str, Any]:
    """Extract text, image, table, and provenance metadata from clinical evidence."""

    metadata = _base_metadata(contents, content_type, filename)
    normalized_type = _normalize_content_type(content_type)
    if normalized_type == "application/pdf" or filename.lower().endswith(".pdf"):
        return _parse_pdf(contents, metadata)
    if normalized_type.startswith("image/"):
        return _parse_image(contents, metadata)
    metadata["type"] = "unsupported"
    metadata["warnings"].append("unsupported_file_type")
    return metadata


def parse_knowledge_base_upload(contents: bytes, content_type: str, filename: str) -> dict[str, Any]:
    """Extract searchable text from DOCX, PDF, Markdown, TXT, and JSON uploads."""

    metadata = _base_metadata(contents, content_type, filename)
    metadata["knowledgeBase"] = True
    extension = Path(filename or "").suffix.lower()
    if extension == ".pdf":
        parsed = _parse_pdf(contents, metadata)
        parsed["knowledgeBase"] = True
        return parsed
    if extension in {".jpg", ".jpeg", ".png", ".webp"}:
        parsed = _parse_image(contents, metadata)
        parsed["knowledgeBase"] = True
        return parsed
    if extension == ".docx":
        text = _extract_docx_text(contents, metadata["warnings"])
        source_type = "docx"
    elif extension == ".json":
        text = json.dumps(json.loads(_decode_text(contents)), indent=2, sort_keys=True)
        source_type = "json"
    else:
        text = _decode_text(contents)
        source_type = "markdown" if extension == ".md" else "text"

    metadata.update(
        {
            "type": source_type,
            "pageCount": 1,
            "textPreview": text[:1000],
            "pages": [{"pageNumber": 1, "text": text[:4000], "textBlocks": [{"text": block} for block in _paragraph_blocks(text)]}],
        }
    )
    return metadata


def _base_metadata(contents: bytes, content_type: str, filename: str) -> dict[str, Any]:
    return {
        "type": "unknown",
        "mimeType": _normalize_content_type(content_type),
        "filename": filename or "upload",
        "sizeBytes": len(contents),
        "checksum": hashlib.sha256(contents).hexdigest(),
        "textPreview": "",
        "pageCount": 0,
        "imageCount": 0,
        "pages": [],
        "images": [],
        "tables": [],
        "warnings": [],
        "thumbnail": "",
    }


def _parse_pdf(contents: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
    """Extract PDF text, page image metadata, tables, and a preview thumbnail."""

    metadata["type"] = "pdf"
    try:
        import fitz
    except ImportError:
        metadata["warnings"].append("pdf_text_extraction_unavailable:pymupdf_missing")
        return metadata

    doc = None
    try:
        doc = fitz.open(stream=contents, filetype="pdf")
        all_text: list[str] = []
        for page_index in range(len(doc)):
            page = doc[page_index]
            page_number = page_index + 1
            text = page.get_text("text") or ""
            blocks = _extract_text_blocks(page)
            page_images = _extract_pdf_image_metadata(page, page_number)
            page_tables = _extract_pdf_tables(page, page_number, metadata["warnings"])
            metadata["pages"].append(
                {
                    "pageNumber": page_number,
                    "text": text[:4000],
                    "textBlocks": blocks,
                    "imageCount": len(page_images),
                    "tableCount": len(page_tables),
                }
            )
            metadata["images"].extend(page_images)
            metadata["tables"].extend(page_tables)
            all_text.append(text)

        metadata["pageCount"] = len(metadata["pages"])
        metadata["imageCount"] = len(metadata["images"])
        metadata["textPreview"] = "\n".join(all_text).strip()[:1000]
        metadata["thumbnail"] = _render_pdf_thumbnail(doc, fitz)
        if not metadata["textPreview"]:
            metadata["warnings"].append("pdf_has_no_extractable_text:ocr_required")
        if not metadata["tables"]:
            metadata["warnings"].append("no_tables_detected")
    except Exception as exc:
        metadata["warnings"].append(f"pdf_parse_failed:{type(exc).__name__}")
    finally:
        if doc is not None:
            doc.close()
    return metadata


def _parse_image(contents: bytes, metadata: dict[str, Any]) -> dict[str, Any]:
    """Extract image dimensions and thumbnail while flagging OCR as a follow-up."""

    metadata["type"] = "image"
    metadata["imageCount"] = 1
    metadata["images"].append(
        {
            "imageId": "uploaded-source",
            "pageNumber": None,
            "mimeType": metadata["mimeType"],
            "role": "uploaded_source",
        }
    )
    metadata["warnings"].append("image_text_extraction_requires_ocr_or_vision_agent")

    try:
        from PIL import Image
    except ImportError:
        metadata["textPreview"] = "Image accepted; Pillow is not installed for local metadata extraction."
        metadata["warnings"].append("image_metadata_unavailable:pillow_missing")
        return metadata

    try:
        img = Image.open(io.BytesIO(contents))
        width, height = img.size
        fmt = img.format or metadata["mimeType"].split("/")[-1].upper()
        metadata["dimensions"] = {"width": width, "height": height}
        metadata["mode"] = img.mode
        metadata["format"] = fmt
        metadata["images"][0].update({"width": width, "height": height, "format": fmt})
        metadata["textPreview"] = f"{width}x{height} {fmt} ({metadata['mimeType']})"
        metadata["thumbnail"] = _render_image_thumbnail(img)
    except Exception as exc:
        metadata["textPreview"] = "Image accepted; local metadata extraction failed."
        metadata["warnings"].append(f"image_parse_failed:{type(exc).__name__}")
    return metadata


def _coerce_knowledge_base_type(normalized_type: str, expected_type: str) -> str:
    if normalized_type in {"", "application/octet-stream"}:
        return expected_type
    if expected_type == "text/markdown" and normalized_type == "text/plain":
        return expected_type
    if expected_type == "application/json" and normalized_type in {"text/plain", "application/octet-stream"}:
        return expected_type
    if expected_type.endswith("wordprocessingml.document") and normalized_type in {"application/zip", "application/octet-stream"}:
        return expected_type
    return normalized_type


def _decode_text(contents: bytes) -> str:
    return contents.decode("utf-8-sig")


def _paragraph_blocks(text: str) -> list[str]:
    return [block.strip()[:500] for block in text.splitlines() if block.strip()][:20]


def _looks_like_docx(contents: bytes) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(contents)) as archive:
            names = set(archive.namelist())
            return "[Content_Types].xml" in names and "word/document.xml" in names
    except zipfile.BadZipFile:
        return False


def _extract_docx_text(contents: bytes, warnings: list[str]) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(contents)) as archive:
            document = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as exc:
        warnings.append(f"docx_parse_failed:{type(exc).__name__}")
        return ""

    try:
        root = ET.fromstring(document)
    except ET.ParseError as exc:
        warnings.append(f"docx_xml_parse_failed:{type(exc).__name__}")
        return ""

    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: list[str] = []
    for paragraph in root.iter(f"{namespace}p"):
        text = "".join(node.text or "" for node in paragraph.iter(f"{namespace}t")).strip()
        if text:
            paragraphs.append(text)
    if not paragraphs:
        warnings.append("docx_has_no_extractable_text")
    return "\n".join(paragraphs)


def _extract_text_blocks(page: Any) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    try:
        for block in page.get_text("blocks")[:20]:
            if len(block) < 5:
                continue
            text = str(block[4]).strip()
            if not text:
                continue
            blocks.append(
                {
                    "bbox": [round(float(value), 2) for value in block[:4]],
                    "text": text[:500],
                }
            )
    except Exception:
        return []
    return blocks


def _extract_pdf_image_metadata(page: Any, page_number: int) -> list[dict[str, Any]]:
    images: list[dict[str, Any]] = []
    try:
        for index, item in enumerate(page.get_images(full=True), 1):
            images.append(
                {
                    "imageId": f"page-{page_number}-image-{index}",
                    "pageNumber": page_number,
                    "xref": item[0] if len(item) > 0 else None,
                    "width": item[2] if len(item) > 2 else None,
                    "height": item[3] if len(item) > 3 else None,
                    "colorspace": item[5] if len(item) > 5 else None,
                }
            )
    except Exception:
        return []
    return images


def _extract_pdf_tables(page: Any, page_number: int, warnings: list[str]) -> list[dict[str, Any]]:
    finder = getattr(page, "find_tables", None)
    if not callable(finder):
        warnings.append("pdf_table_extraction_unavailable:pymupdf_find_tables_missing")
        return []

    tables: list[dict[str, Any]] = []
    try:
        found = finder()
        raw_tables = getattr(found, "tables", found)
        for index, table in enumerate(raw_tables, 1):
            rows = table.extract()
            tables.append(
                {
                    "tableId": f"page-{page_number}-table-{index}",
                    "pageNumber": page_number,
                    "rowCount": len(rows),
                    "columnCount": max((len(row) for row in rows), default=0),
                    "rows": rows[:50],
                }
            )
    except Exception as exc:
        warnings.append(f"pdf_table_extraction_failed:{type(exc).__name__}")
    return tables


def _render_pdf_thumbnail(doc: Any, fitz: Any) -> str:
    if len(doc) == 0:
        return ""
    try:
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(0.5, 0.5), alpha=False)
        return base64.b64encode(pix.tobytes("png")).decode()
    except Exception:
        return ""


def _render_image_thumbnail(img: Any) -> str:
    thumb = img.copy()
    thumb.thumbnail((400, 400))
    buf = io.BytesIO()
    thumb.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _normalize_content_type(content_type: str) -> str:
    normalized = (content_type or "application/octet-stream").split(";", 1)[0].strip().lower()
    return "image/jpeg" if normalized == "image/jpg" else normalized


def _detect_mime(contents: bytes) -> str | None:
    if contents.startswith(b"%PDF"):
        return "application/pdf"
    if contents.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if contents.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(contents) >= 12 and contents[:4] == b"RIFF" and contents[8:12] == b"WEBP":
        return "image/webp"
    return None
