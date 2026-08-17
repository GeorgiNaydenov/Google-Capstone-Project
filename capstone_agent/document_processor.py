"""Document processing — real PDF and image extraction using PyMuPDF and Gemini.

This module handles the actual file processing pipeline:
1. PDF text extraction via PyMuPDF (fitz)
2. Image analysis via Gemini Vision API (multimodal)
3. Text chunking with overlap for search retrieval
4. Gemini-powered clinical structuring of extracted content

All extracted content is stored in SQLite via database.py for
downstream search, citation building, and Q&A.
"""

import hashlib
import json
import logging
import zipfile
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from .config import get_config
from .database import UPLOADS_ROOT

logger = logging.getLogger("capstone_agent.document_processor")

# UPLOADS_ROOT honors CLINICAL_DATA_DIR, keeping uploads on the writable
# (optionally mounted) data directory in containers where the package root
# is read-only; unset, it stays beside the project for local development.
UPLOAD_DIR = UPLOADS_ROOT
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def generate_document_id(filename: str, content: bytes) -> str:
    """Generate a deterministic document ID from filename and content hash."""
    digest = hashlib.sha256(content).hexdigest()[:16]
    return f"DOC-{digest}"


def detect_content_type(file_path: str) -> str:
    """Detect content type from file extension."""
    ext = Path(file_path).suffix.lower()
    type_map = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
        ".tiff": "image/tiff",
        ".tif": "image/tiff",
        ".bmp": "image/bmp",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".csv": "text/csv",
        ".json": "application/json",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    return type_map.get(ext, "application/octet-stream")


# ---------------------------------------------------------------------------
# PDF extraction (PyMuPDF)
# ---------------------------------------------------------------------------


def extract_text_from_pdf(file_path: str) -> dict[str, Any]:
    """Extract text from every page of a PDF using PyMuPDF.

    Returns page-by-page text, full concatenated text, and page count.
    Also extracts images embedded in the PDF for optional vision analysis.
    """
    import fitz  # PyMuPDF

    doc = fitz.open(file_path)
    pages = []
    full_text_parts = []
    image_count = 0

    for i, page in enumerate(doc):
        text = page.get_text("text")
        pages.append(
            {
                "page_number": i + 1,
                "text": text,
                "char_count": len(text),
            }
        )
        full_text_parts.append(text)
        image_count += len(page.get_images(full=True))

    doc.close()

    full_text = "\n\n".join(full_text_parts)
    return {
        "text": full_text,
        "pages": pages,
        "page_count": len(pages),
        "total_chars": len(full_text),
        "image_count": image_count,
    }


# ---------------------------------------------------------------------------
# Image extraction (Gemini Vision)
# ---------------------------------------------------------------------------


def _get_genai_client():
    """Create a google.genai Client configured for the current environment.

    Prefers API key for direct SDK calls (outside ADK framework).
    Falls back to Vertex AI only when no API key is available.
    """
    from google import genai

    config = get_config()
    if config["google_api_key"]:
        return genai.Client(api_key=config["google_api_key"], vertexai=False)
    if config["use_vertex_ai"] and config["gcp_project"]:
        return genai.Client(
            vertexai=True,
            project=config["gcp_project"],
            location=config["gcp_location"],
        )
    raise RuntimeError("No Gemini credentials: set GOOGLE_API_KEY or enable Vertex AI")


def extract_text_from_image(file_path: str) -> dict[str, Any]:
    """Analyze an image using Gemini Vision API for OCR and clinical analysis.

    Sends the image to Gemini multimodal and asks for structured extraction
    of all visible text, clinical findings, measurements, and observations.
    """
    from google.genai import types as genai_types

    config = get_config()
    client = _get_genai_client()

    with open(file_path, "rb") as f:
        image_data = f.read()

    mime_type = detect_content_type(file_path)
    model_id = config.get("model_id", "gemini-2.0-flash")

    prompt = (
        "You are a clinical document analysis system. Analyze this image thoroughly.\n\n"
        "1. Extract ALL visible text (OCR) exactly as written.\n"
        "2. If this is a clinical/medical document or image, identify:\n"
        "   - Document type (lab report, imaging study, prescription, clinical note, etc.)\n"
        "   - Key clinical findings, measurements, and values\n"
        "   - Any diagnoses, medications, or procedures mentioned\n"
        "   - Patient identifiers if visible\n"
        "3. If this is a medical image (X-ray, CT, MRI, etc.), describe:\n"
        "   - Imaging modality and body region\n"
        "   - Visible anatomical structures\n"
        "   - Any abnormalities or notable findings\n\n"
        "Return your analysis in a structured format with clear sections."
    )

    response = client.models.generate_content(
        model=model_id,
        contents=[
            genai_types.Content(
                role="user",
                parts=[
                    genai_types.Part.from_bytes(data=image_data, mime_type=mime_type),
                    genai_types.Part.from_text(text=prompt),
                ],
            )
        ],
    )

    analysis_text = response.text if response.text else "No text extracted from image."

    return {
        "text": analysis_text,
        "pages": [{"page_number": 1, "text": analysis_text}],
        "page_count": 1,
        "total_chars": len(analysis_text),
        "analysis_type": "gemini_vision",
    }


# ---------------------------------------------------------------------------
# Plain text extraction
# ---------------------------------------------------------------------------


def extract_text_from_plaintext(file_path: str) -> dict[str, Any]:
    """Read plain text files directly."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return {
        "text": text,
        "pages": [{"page_number": 1, "text": text}],
        "page_count": 1,
        "total_chars": len(text),
    }


def extract_text_from_json(file_path: str) -> dict[str, Any]:
    """Read JSON files as deterministic, searchable text."""

    with open(file_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    text = json.dumps(data, indent=2, sort_keys=True)
    return {
        "text": text,
        "pages": [{"page_number": 1, "text": text}],
        "page_count": 1,
        "total_chars": len(text),
    }


def extract_text_from_docx(file_path: str) -> dict[str, Any]:
    """Extract paragraph text from a DOCX package using only stdlib XML tools."""

    with zipfile.ZipFile(file_path) as archive:
        document = archive.read("word/document.xml")
    root = ET.fromstring(document)
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs = []
    for paragraph in root.iter(f"{namespace}p"):
        text = "".join(
            node.text or "" for node in paragraph.iter(f"{namespace}t")
        ).strip()
        if text:
            paragraphs.append(text)
    full_text = "\n".join(paragraphs)
    return {
        "text": full_text,
        "pages": [{"page_number": 1, "text": full_text}],
        "page_count": 1,
        "total_chars": len(full_text),
    }


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[dict]:
    """Split text into overlapping chunks for search indexing.

    Each chunk has enough context for meaningful retrieval while
    staying small enough for precise citation.
    """
    if not text or not text.strip():
        return []

    chunks = []
    start = 0
    index = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try to break at sentence boundary
        if end < len(text):
            for boundary in [". ", ".\n", "\n\n", "\n", " "]:
                last_boundary = text.rfind(boundary, start + chunk_size // 2, end)
                if last_boundary > start:
                    end = last_boundary + len(boundary)
                    break

        chunk_text_content = text[start:end].strip()
        if chunk_text_content:
            chunks.append(
                {
                    "index": index,
                    "text": chunk_text_content,
                    "start_char": start,
                    "end_char": end,
                }
            )
            index += 1

        start = end - overlap
        if start >= len(text) - overlap:
            break

    return chunks


# ---------------------------------------------------------------------------
# Gemini-powered clinical analysis
# ---------------------------------------------------------------------------


def analyze_with_gemini(text: str, analysis_type: str = "clinical") -> str:
    """Send extracted text to Gemini for clinical structuring and analysis.

    Uses the configured model to produce structured clinical findings
    from raw extracted text. This replaces mock structuring tools.
    """
    config = get_config()
    if not config["gemini_enabled"]:
        return "Gemini analysis unavailable: no API key configured."

    client = _get_genai_client()
    model_id = config.get("model_id", "gemini-2.0-flash")

    prompts = {
        "clinical": (
            "You are a clinical data structuring system. Analyze this extracted text "
            "and produce structured clinical findings.\n\n"
            "For each finding, provide:\n"
            "- Field name (e.g., 'primary_diagnosis', 'medication', 'lab_value')\n"
            "- Value (the actual finding)\n"
            "- Confidence (high/medium/low based on text clarity)\n"
            "- Source context (brief quote from the original text)\n\n"
            f"Text to analyze:\n{text[:8000]}"
        ),
        "summary": (
            "Summarize this clinical document concisely. Include key diagnoses, "
            "medications, lab values, and recommended actions.\n\n"
            f"Document text:\n{text[:8000]}"
        ),
        "qa_context": (
            "Extract the key facts from this text that would be useful for "
            "answering clinical questions. List each fact on its own line.\n\n"
            f"Text:\n{text[:8000]}"
        ),
    }

    prompt = prompts.get(analysis_type, prompts["clinical"])

    try:
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
        )
        return response.text if response.text else "No analysis produced."
    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        return f"Analysis error: {e}"


# ---------------------------------------------------------------------------
# Main processing pipeline
# ---------------------------------------------------------------------------


def process_document(
    file_path: str, patient_id: str = "", pre_extraction: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Process a document end-to-end: extract text, chunk, analyze, store.

    This is the main entry point called by the upload_document tool.
    Handles PDFs, images, and plain text files.

    pre_extraction lets callers that already extracted the document text
    (for example patient-id detection on an uploaded image) reuse that
    result instead of paying for a second Gemini Vision pass.

    Returns a complete processing result with document_id, extracted text,
    chunks stored, and Gemini analysis.
    """
    from . import database

    file_path = str(Path(file_path).resolve())
    if not Path(file_path).exists():
        return {"error": f"File not found: {file_path}"}

    filename = Path(file_path).name
    content_type = detect_content_type(file_path)

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    document_id = generate_document_id(filename, file_bytes)

    # Check if already processed
    existing = database.get_document(document_id)
    if existing:
        return {
            "document_id": document_id,
            "filename": filename,
            "status": "already_processed",
            "page_count": existing["page_count"],
            "message": f"Document '{filename}' was already processed.",
        }

    logger.info(f"Processing document: {filename} ({content_type})")

    # Extract text based on content type
    if pre_extraction is not None:
        extraction = pre_extraction
    elif content_type == "application/pdf":
        extraction = extract_text_from_pdf(file_path)
    elif content_type.startswith("image/"):
        extraction = extract_text_from_image(file_path)
    elif content_type.endswith("wordprocessingml.document"):
        extraction = extract_text_from_docx(file_path)
    elif content_type == "application/json":
        extraction = extract_text_from_json(file_path)
    elif content_type.startswith("text/"):
        extraction = extract_text_from_plaintext(file_path)
    else:
        return {"error": f"Unsupported file type: {content_type}"}

    raw_text = extraction["text"]
    page_count = extraction["page_count"]

    # Run Gemini clinical analysis on extracted text
    gemini_analysis = ""
    config = get_config()
    if config["gemini_enabled"] and raw_text.strip():
        gemini_analysis = analyze_with_gemini(raw_text, "clinical")

    # Store document in database
    database.store_document(
        document_id=document_id,
        filename=filename,
        content_type=content_type,
        file_path=file_path,
        raw_text=raw_text,
        page_count=page_count,
        patient_id=patient_id,
        gemini_analysis=gemini_analysis,
    )

    # Chunk text and store for search
    chunks = chunk_text(raw_text)
    chunk_dicts = []
    for chunk in chunks:
        page_num = None
        if "pages" in extraction:
            cumulative = 0
            for pg in extraction["pages"]:
                cumulative += len(pg["text"])
                if chunk["start_char"] < cumulative:
                    page_num = pg["page_number"]
                    break
        chunk_dicts.append(
            {
                "index": chunk["index"],
                "text": chunk["text"],
                "page": page_num,
            }
        )

    chunk_count = database.store_document_chunks(document_id, chunk_dicts, patient_id)

    # Log to audit trail
    database.log_audit(
        agent_name="document_processor",
        action="document_uploaded",
        patient_id=patient_id,
        details=json.dumps(
            {
                "document_id": document_id,
                "filename": filename,
                "page_count": page_count,
                "chunk_count": chunk_count,
                "content_type": content_type,
            }
        ),
    )

    return {
        "document_id": document_id,
        "filename": filename,
        "content_type": content_type,
        "page_count": page_count,
        "total_chars": extraction.get("total_chars", len(raw_text)),
        "chunk_count": chunk_count,
        "gemini_analysis": gemini_analysis[:2000] if gemini_analysis else "",
        "text_preview": raw_text[:500],
        "status": "processed",
        "message": f"Successfully processed '{filename}': {page_count} pages, {chunk_count} chunks indexed.",
    }
