"""Generate multimodal patient bundles for the Q&A agent.

Each bundle contains one dense patient record, many comparator patients,
uploadable PDF evidence documents, evidence citations, Plotly visualization
specs, Matplotlib chart images, and ready-to-run Q&A prompts.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import zipfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape as xml_escape

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import showcase_clinical_core as core


DEFAULT_OUTPUT = Path("showcase_data/multimodal")
DEFAULT_PDFS_PER_BUNDLE = 36
DEFAULT_KB_DOCS_PER_BUNDLE = 25
KB_EXTENSIONS = (".pdf", ".docx", ".md", ".txt", ".json")
DIAGNOSES = (
    "Metastatic NSCLC",
    "Heart failure with reduced EF",
    "Type 2 diabetes with retinopathy",
    "Chronic kidney disease stage 4",
    "Crohn disease flare",
)
METRICS = ("tumor_size_cm", "cea_ng_ml", "bnp_pg_ml", "egfr", "hba1c_pct", "crp_mg_l")
MODALITIES = (
    "CT chest",
    "CT abdomen",
    "MRI brain",
    "X-Ray chest",
    "Fundoscopy",
    "Clinical photo",
)
CLINICIANS = ("Dr. Sarah Miller", "Dr. Elena Park", "Dr. James Patel", "Dr. Priya Rao")
# Chart colors mirror the frontend ChartPanel palette so static exports and
# live Plotly renders stay visually consistent across the product.
CHART_PALETTE = (
    "#2563eb",
    "#16a34a",
    "#b45309",
    "#dc2626",
    "#0284c7",
    "#7c3aed",
    "#0f766e",
)
METRIC_COLORS = {"tumor_size_cm": "#dc2626", "cea_ng_ml": "#2563eb", "egfr": "#16a34a"}
RISK_COLORS = {"high": "#dc2626", "needs_review": "#f59e0b", "stable": "#16a34a"}


def _wrap(text: str, width: int = 88) -> list[str]:
    """Split text into short display lines for generated PDF pages."""

    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        if sum(len(item) for item in current) + len(current) + len(word) > width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def _trend(
    start: float, drift: float, count: int, rng: random.Random, minimum: float = 0.1
) -> list[float]:
    """Create deterministic longitudinal values."""

    values = []
    current = start
    for _ in range(count):
        current += drift + rng.uniform(-abs(drift) * 1.8 - 0.2, abs(drift) * 1.8 + 0.2)
        values.append(round(max(minimum, current), 2))
    return values


def _patient(patient_id: str, rng: random.Random) -> dict[str, Any]:
    """Create focus patient metadata."""

    diagnosis = rng.choice(DIAGNOSES)
    return {
        "patient_id": patient_id,
        "name": f"Multimodal Patient {patient_id[-4:]}",
        "age": rng.randint(42, 79),
        "sex": rng.choice(("Female", "Male")),
        "risk_level": rng.choice(("high", "needs_review")),
        "primary_diagnosis": diagnosis,
        "assigned_clinician": rng.choice(CLINICIANS),
        "data_completeness_score": round(rng.uniform(0.86, 0.98), 2),
        "care_team": list(rng.sample(CLINICIANS, 2)),
        "allergies": rng.sample(
            ("Penicillin", "Sulfonamides", "Iodine contrast", "NSAIDs", "None"), 2
        ),
        "medications": [
            {"name": "Pembrolizumab", "dose": "200 mg IV q3w", "status": "active"},
            {"name": "Furosemide", "dose": "40 mg daily", "status": "active"},
            {"name": "Metformin", "dose": "1000 mg BID", "status": "active"},
            {"name": "Atorvastatin", "dose": "40 mg daily", "status": "active"},
        ],
    }


def _patient_from_profile(
    profile: dict[str, Any], rng: random.Random, demo_platform: str
) -> dict[str, Any]:
    """Create focus patient metadata from the shared enterprise blueprint."""

    meds = [
        {
            "name": item["name"],
            "dose": f"{item['dose']} {item['frequency']}",
            "status": item["status"],
        }
        for item in profile.get("medications", [])[:5]
    ]
    allergies = [item["allergen"] for item in profile.get("allergies", [])]
    care_gaps = [
        {
            "type": gap[0],
            "description": gap[1],
            "priority": "high" if profile.get("risk_tier") == "High" else "medium",
            "status": "open",
        }
        for gap in profile.get("care_gaps", [])
    ]
    tenant = core.TENANT_THEMES.get(demo_platform, core.TENANT_THEMES["primary"])
    return {
        "patient_id": profile["patient_id"],
        "name": profile["name"],
        "age": profile["age"],
        "sex": profile["sex"],
        "risk_level": profile["risk_level"],
        "primary_diagnosis": profile["primary_diagnosis"],
        "assigned_clinician": profile["provider"]["full_name"],
        "data_completeness_score": profile["completeness"],
        "care_team": profile.get("care_team", [profile["provider"]["full_name"]]),
        "allergies": allergies or ["None documented"],
        "medications": meds,
        "care_gaps": care_gaps,
        "organization": tenant["org"],
        "source_systems": list(profile.get("source_systems", [])),
        "review_focus": f"{profile['primary_diagnosis']} longitudinal trend, care gaps, payer context, and abnormal evidence review",
        "privacy_class": profile["privacy_class"],
        "cohort_archetype": profile["archetype"],
    }


def _timeline(
    patient_id: str,
    rng: random.Random,
    event_count: int,
    patient: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Build dated clinical events across notes, labs, images, and decisions."""

    today = date(2026, 6, 24)
    events = []
    for index in range(event_count):
        day = today - timedelta(days=event_count - index)
        source_type = rng.choice(
            ("clinical_note", "lab", "image", "medication", "care_plan")
        )
        events.append(
            {
                "event_id": f"EV-{patient_id}-{index + 1:04d}",
                "date": day.isoformat(),
                "source_type": source_type,
                "title": f"{source_type.replace('_', ' ').title()} event {index + 1}",
                "summary": f"{source_type.replace('_', ' ').title()} evidence contributes to longitudinal answer synthesis for {patient['primary_diagnosis'] if patient else patient_id}.",
                "citation_id": f"CIT-{patient_id}-{index + 1:04d}",
            }
        )
    return events


def _labs(patient_id: str, rng: random.Random, days: int) -> list[dict[str, Any]]:
    """Create dense longitudinal lab and metric rows."""

    start = date(2026, 6, 24) - timedelta(days=days)
    seeds = {
        "tumor_size_cm": (3.1, 0.006),
        "cea_ng_ml": (4.5, 0.04),
        "bnp_pg_ml": (220, 1.8),
        "egfr": (68, -0.05),
        "hba1c_pct": (7.2, 0.004),
        "crp_mg_l": (5.0, 0.03),
    }
    series = {
        name: _trend(base, drift, days, rng, 0.1)
        for name, (base, drift) in seeds.items()
    }
    rows = []
    for day_index in range(days):
        row_date = start + timedelta(days=day_index)
        for metric in METRICS:
            value = series[metric][day_index]
            rows.append(
                {
                    "patient_id": patient_id,
                    "date": row_date.isoformat(),
                    "metric": metric,
                    "value": value,
                    "unit": metric.rsplit("_", 1)[-1],
                    "flag": "high"
                    if value > series[metric][max(0, day_index - 30)] * 1.1
                    else "normal",
                }
            )
    return rows


def _images(patient_id: str, rng: random.Random, count: int) -> list[dict[str, Any]]:
    """Create image evidence metadata."""

    images = []
    for index in range(1, count + 1):
        modality = rng.choice(MODALITIES)
        images.append(
            {
                "image_id": f"IMG-{patient_id}-{index:03d}",
                "gcs_uri": f"gs://clinical-data/{patient_id}/multimodal/{index:03d}.png",
                "modality": modality,
                "date": (date(2026, 6, 24) - timedelta(days=index * 18)).isoformat(),
                "description": f"{modality} evidence with annotated regions and extraction metadata.",
                "quality_score": round(rng.uniform(0.72, 0.98), 2),
                "visual_findings": rng.sample(
                    ("growth", "stable", "effusion", "edema", "lesion", "artifact"), 3
                ),
            }
        )
    return images


def _notes(
    patient_id: str,
    rng: random.Random,
    count: int,
    patient: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Create vector-searchable note chunks."""

    notes = []
    for index in range(1, count + 1):
        topic = rng.choice(
            (
                "progression",
                "medication adherence",
                "lab worsening",
                "symptom change",
                "care plan",
                "imaging comparison",
            )
        )
        diagnosis = patient["primary_diagnosis"] if patient else patient_id
        review_focus = (
            patient.get("review_focus", "longitudinal synthesis")
            if patient
            else "longitudinal synthesis"
        )
        notes.append(
            {
                "note_id": f"NOTE-{patient_id}-{index:03d}",
                "date": (date(2026, 6, 24) - timedelta(days=index * 5)).isoformat(),
                "author": patient["assigned_clinician"]
                if patient and index % 3
                else rng.choice(CLINICIANS),
                "note_type": rng.choice(
                    ("Progress Note", "Consult", "Radiology Summary", "Care Plan")
                ),
                "text": f"Longitudinal {topic} evidence for {patient_id} with {diagnosis}. This note links symptoms, imaging, structured labs, clinician plan, and review focus: {review_focus}.",
                "vector_chunk_id": f"VEC-{patient_id}-{index:03d}",
                "keywords": [topic, "longitudinal", "multimodal"],
            }
        )
    return notes


def _comparators(
    bundle_index: int,
    count: int,
    rng: random.Random,
    patient_prefix: str = "PT-D",
    demo_platform: str = "primary",
) -> list[dict[str, Any]]:
    """Create surrounding cohort rows for population-aware answers."""

    rows = []
    for index in range(1, count + 1):
        comparator_index = ((bundle_index - 1) * count + index) % 10000 + 1
        rows.append(
            {
                "patient_id": f"{patient_prefix}{comparator_index:05d}",
                "age": rng.randint(18, 90),
                "risk_level": rng.choices(
                    ("high", "needs_review", "stable"), weights=(16, 29, 55)
                )[0],
                "primary_diagnosis": rng.choice(DIAGNOSES),
                "latest_confidence": round(rng.uniform(0.67, 0.99), 2),
                "open_tasks": rng.randint(0, 5),
                "evidence_count": rng.randint(8, 72),
            }
        )
    return rows


def _plotly_specs(
    patient_id: str,
    labs: list[dict[str, Any]],
    images: list[dict[str, Any]],
    comparators: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build Plotly-ready chart specifications."""

    recent = [
        row for row in labs if row["metric"] in {"tumor_size_cm", "cea_ng_ml", "egfr"}
    ]
    modality_counts: dict[str, int] = {}
    for image in images:
        modality_counts[image["modality"]] = (
            modality_counts.get(image["modality"], 0) + 1
        )
    risk_counts: dict[str, int] = {}
    for row in comparators:
        risk_counts[row["risk_level"]] = risk_counts.get(row["risk_level"], 0) + 1
    return {
        "metric_trends": {
            "data": [
                {
                    "type": "scatter",
                    "mode": "lines",
                    "name": metric,
                    "line": {"color": METRIC_COLORS[metric]},
                    "x": [row["date"] for row in recent if row["metric"] == metric],
                    "y": [row["value"] for row in recent if row["metric"] == metric],
                }
                for metric in ("tumor_size_cm", "cea_ng_ml", "egfr")
            ],
            "layout": {"title": f"{patient_id} longitudinal metric trends"},
        },
        "image_modalities": {
            "data": [
                {
                    "type": "bar",
                    "x": list(modality_counts),
                    "y": list(modality_counts.values()),
                    "marker": {
                        "color": [
                            CHART_PALETTE[index % len(CHART_PALETTE)]
                            for index in range(len(modality_counts))
                        ]
                    },
                }
            ],
            "layout": {"title": "Image evidence by modality"},
        },
        "comparator_risk": {
            "data": [
                {
                    "type": "pie",
                    "labels": list(risk_counts),
                    "values": list(risk_counts.values()),
                    "marker": {
                        "colors": [
                            RISK_COLORS.get(label, CHART_PALETTE[0])
                            for label in risk_counts
                        ]
                    },
                }
            ],
            "layout": {"title": "Comparator cohort risk mix"},
        },
    }


def _write_charts(
    bundle_dir: Path,
    patient_id: str,
    labs: list[dict[str, Any]],
    comparators: list[dict[str, Any]],
) -> list[str]:
    """Render Matplotlib visualizations for the bundle."""

    chart_dir = bundle_dir / "charts"
    chart_dir.mkdir(exist_ok=True)
    chart_paths = []
    trend_path = chart_dir / "metric_trends.png"
    plt.figure(figsize=(10, 5))
    for metric in ("tumor_size_cm", "cea_ng_ml", "egfr"):
        rows = [row for row in labs if row["metric"] == metric][::10]
        plt.plot(
            [row["date"] for row in rows],
            [row["value"] for row in rows],
            label=metric,
            color=METRIC_COLORS[metric],
        )
    plt.xticks(rotation=35, ha="right")
    plt.ylabel("measured value")
    plt.grid(alpha=0.3)
    plt.title(f"{patient_id} multimodal trend summary")
    plt.legend()
    plt.tight_layout()
    plt.savefig(trend_path, dpi=150, bbox_inches="tight")
    plt.close()
    chart_paths.append(str(trend_path))

    risk_path = chart_dir / "comparator_risk.png"
    counts = {
        risk: len([row for row in comparators if row["risk_level"] == risk])
        for risk in ("high", "needs_review", "stable")
    }
    plt.figure(figsize=(6, 4))
    plt.bar(
        list(counts),
        list(counts.values()),
        color=[RISK_COLORS[risk] for risk in counts],
    )
    plt.ylabel("cohort patients")
    plt.grid(axis="y", alpha=0.3)
    plt.title("Comparator cohort risk")
    plt.tight_layout()
    plt.savefig(risk_path, dpi=150, bbox_inches="tight")
    plt.close()
    chart_paths.append(str(risk_path))
    return chart_paths


def _write_pdf_corpus(
    bundle_dir: Path,
    patient: dict[str, Any],
    labs: list[dict[str, Any]],
    images: list[dict[str, Any]],
    notes: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    pdf_count: int,
) -> list[dict[str, Any]]:
    """Render uploadable PDF evidence files with text, table, and visual panels."""

    document_dir = bundle_dir / "documents"
    document_dir.mkdir(exist_ok=True)
    patient_id = patient["patient_id"]
    documents = []
    metric_order = ("tumor_size_cm", "cea_ng_ml", "egfr")
    for index in range(1, pdf_count + 1):
        note = notes[(index - 1) % len(notes)]
        image = images[(index - 1) % len(images)]
        event = timeline[(index - 1) % len(timeline)]
        metric = metric_order[(index - 1) % len(metric_order)]
        metric_rows = [row for row in labs if row["metric"] == metric]
        if not metric_rows and labs:
            metric_rows = labs
        window_start = ((index - 1) * 7) % max(1, len(metric_rows) - 8)
        trend_rows = metric_rows[window_start : window_start + 8]
        table_rows = [
            [row["date"], row["metric"], row["value"], row["unit"], row["flag"]]
            for row in trend_rows[:6]
        ]
        if not table_rows:
            table_rows = [["N/A", "N/A", "N/A", "N/A", "N/A"]]
        document_id = f"PDF-{patient_id}-{index:03d}"
        path = document_dir / f"{document_id}.pdf"
        with PdfPages(path) as pdf:
            fig = plt.figure(figsize=(8.5, 11))
            page = fig.add_axes([0, 0, 1, 1])
            page.axis("off")
            page.text(
                0.08,
                0.94,
                f"{patient.get('organization', 'Clinical')} Multimodal Evidence Packet",
                fontsize=16,
                weight="bold",
            )
            page.text(
                0.08,
                0.90,
                f"{document_id} | {patient_id} | {note['date']}",
                fontsize=10,
            )
            page.text(
                0.08,
                0.86,
                f"Diagnosis: {patient['primary_diagnosis']} | Risk: {patient['risk_level']}",
                fontsize=10,
            )
            page.text(
                0.08,
                0.82,
                f"Clinician: {note['author']} | Source: {note['note_type']}",
                fontsize=10,
            )

            y = 0.76
            for line in _wrap(note["text"] + " " + event["summary"], 92)[:5]:
                page.text(0.08, y, line, fontsize=9)
                y -= 0.035

            page.text(
                0.08, 0.56, "Structured evidence table", fontsize=11, weight="bold"
            )
            table = page.table(
                cellText=table_rows,
                colLabels=["Date", "Metric", "Value", "Unit", "Flag"],
                bbox=[0.08, 0.36, 0.84, 0.17],
            )
            table.auto_set_font_size(False)
            table.set_fontsize(7)

            page.text(0.08, 0.30, "Image evidence summary", fontsize=11, weight="bold")
            page.text(
                0.08,
                0.265,
                f"{image['modality']} | {image['date']} | quality {image['quality_score']}",
                fontsize=9,
            )
            page.text(0.08, 0.235, ", ".join(image["visual_findings"]), fontsize=9)

            chart = fig.add_axes([0.12, 0.06, 0.76, 0.14])
            chart.plot(
                [row["date"] for row in trend_rows],
                [row["value"] for row in trend_rows],
                marker="o",
                color=METRIC_COLORS.get(metric, CHART_PALETTE[0]),
            )
            chart.set_title(f"{metric} trend")
            chart.tick_params(axis="x", rotation=35, labelsize=6)
            chart.tick_params(axis="y", labelsize=7)
            chart.grid(alpha=0.25)
            fig.savefig(pdf, format="pdf")
            plt.close(fig)

        documents.append(
            {
                "document_id": document_id,
                "path": str(path),
                "content_type": "application/pdf",
                "patient_id": patient_id,
                "date": note["date"],
                "page_count": 1,
                "contains": [
                    "clinical_text",
                    "structured_table",
                    "trend_chart",
                    "image_evidence_summary",
                ],
                "source_note_id": note["note_id"],
                "source_image_id": image["image_id"],
            }
        )
    return documents


def _write_minimal_docx(path: Path, paragraphs: list[str]) -> None:
    """Create a small valid DOCX package without external dependencies."""

    body = "".join(
        f"<w:p><w:r><w:t>{xml_escape(paragraph)}</w:t></w:r></w:p>"
        for paragraph in paragraphs
    )
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}<w:sectPr/></w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    relationships = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
        "</Relationships>"
    )
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", relationships)
        archive.writestr("word/document.xml", document_xml)


def _kb_paragraphs(
    patient: dict[str, Any],
    note: dict[str, Any],
    event: dict[str, Any],
    table_rows: list[dict[str, Any]],
) -> list[str]:
    """Build reusable knowledge-base text across file formats."""

    rows = "; ".join(
        f"{row['date']} {row['metric']}={row['value']} {row['unit']} ({row['flag']})"
        for row in table_rows[:5]
    )
    return [
        f"Patient {patient['patient_id']} knowledge-base evidence",
        f"Diagnosis: {patient['primary_diagnosis']}. Risk level: {patient['risk_level']}.",
        f"Enterprise context: {patient.get('organization', 'Clinical tenant')} | sources: {', '.join(patient.get('source_systems', []))}.",
        f"Review focus: {patient.get('review_focus', 'longitudinal synthesis')}.",
        f"Clinical note: {note['text']}",
        f"Timeline event: {event['summary']}",
        f"Structured table rows: {rows}",
        "Expected Q&A output: concise text answer, evidence table, and visual trend reference.",
    ]


def _write_kb_pdf(
    path: Path,
    document_id: str,
    paragraphs: list[str],
    table_rows: list[dict[str, Any]],
) -> None:
    """Render one compact PDF for the mixed-format knowledge base."""

    if not table_rows:
        table_rows = [{"date": "N/A", "metric": "N/A", "value": "N/A", "flag": "N/A"}]

    with PdfPages(path) as pdf:
        fig = plt.figure(figsize=(8.5, 11))
        page = fig.add_axes([0, 0, 1, 1])
        page.axis("off")
        page.text(0.08, 0.94, document_id, fontsize=16, weight="bold")
        y = 0.88
        for paragraph in paragraphs[:5]:
            for line in _wrap(paragraph, 88)[:3]:
                page.text(0.08, y, line, fontsize=9)
                y -= 0.032
        table = page.table(
            cellText=[
                [row["date"], row["metric"], row["value"], row["flag"]]
                for row in table_rows[:6]
            ],
            colLabels=["Date", "Metric", "Value", "Flag"],
            bbox=[0.08, 0.18, 0.84, 0.20],
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        chart = fig.add_axes([0.14, 0.48, 0.70, 0.18])
        chart.plot(
            [row["date"] for row in table_rows],
            [row["value"] for row in table_rows],
            marker="o",
        )
        chart.tick_params(axis="x", rotation=30, labelsize=6)
        chart.set_title("Knowledge-base trend")
        fig.savefig(pdf, format="pdf")
        plt.close(fig)


def _write_knowledge_base_corpus(
    bundle_dir: Path,
    patient: dict[str, Any],
    labs: list[dict[str, Any]],
    notes: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    doc_count: int,
) -> list[dict[str, Any]]:
    """Create mixed DOCX/PDF/Markdown/TXT/JSON files for Q&A knowledge-base upload."""

    kb_dir = bundle_dir / "knowledge_base"
    kb_dir.mkdir(exist_ok=True)
    patient_id = patient["patient_id"]
    documents = []
    metric_rows = [
        row for row in labs if row["metric"] in {"tumor_size_cm", "cea_ng_ml", "egfr"}
    ]
    if not metric_rows and labs:
        metric_rows = labs
    for index in range(1, doc_count + 1):
        extension = KB_EXTENSIONS[(index - 1) % len(KB_EXTENSIONS)]
        note = notes[(index - 1) % len(notes)]
        event = timeline[(index - 1) % len(timeline)]
        start = ((index - 1) * 9) % max(1, len(metric_rows) - 8)
        rows = metric_rows[start : start + 8]
        document_id = f"KB-{patient_id}-{index:03d}"
        path = kb_dir / f"{document_id}{extension}"
        paragraphs = _kb_paragraphs(patient, note, event, rows)
        if extension == ".pdf":
            _write_kb_pdf(path, document_id, paragraphs, rows)
            content_type = "application/pdf"
        elif extension == ".docx":
            _write_minimal_docx(path, paragraphs)
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif extension == ".json":
            path.write_text(
                json.dumps(
                    {
                        "document_id": document_id,
                        "patient": patient,
                        "note": note,
                        "timeline_event": event,
                        "table": rows,
                        "answer_requires": ["text", "table", "visual"],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            content_type = "application/json"
        elif extension == ".md":
            path.write_text(
                "# " + paragraphs[0] + "\n\n" + "\n\n".join(paragraphs[1:]),
                encoding="utf-8",
            )
            content_type = "text/markdown"
        else:
            path.write_text("\n\n".join(paragraphs), encoding="utf-8")
            content_type = "text/plain"
        documents.append(
            {
                "document_id": document_id,
                "path": str(path),
                "extension": extension,
                "content_type": content_type,
                "patient_id": patient_id,
                "expected_ingestion": {
                    "api": "/api/knowledge-base/assets",
                    "adk_tool": "upload_document",
                },
                "expected_retrieval": {
                    "route": "/api/runs/qa",
                    "source_types": ["document"],
                },
            }
        )
    return documents


def build_bundle(
    bundle_index: int,
    output: Path,
    rng: random.Random,
    days: int,
    comparators: int,
    pdfs_per_bundle: int,
    kb_docs_per_bundle: int,
    demo_platform: str = "primary",
    patient_prefix: str = "PT-D",
    seed: int = 240624,
    providers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build one complete multimodal Q&A bundle."""

    provider_rows = providers or core.build_providers(seed, demo_platform)
    profile = core.build_patient(
        bundle_index,
        seed,
        patient_prefix,
        date(2026, 7, 5),
        4,
        provider_rows,
        demo_platform,
    )
    patient_id = profile["patient_id"]
    bundle_dir = output / patient_id
    bundle_dir.mkdir(parents=True, exist_ok=True)
    patient = _patient_from_profile(profile, rng, demo_platform)
    labs = _labs(patient_id, rng, days)
    images = _images(patient_id, rng, 18)
    notes = _notes(patient_id, rng, 72, patient)
    timeline = _timeline(patient_id, rng, 160, patient)
    comparator_rows = _comparators(
        bundle_index, comparators, rng, patient_prefix, demo_platform
    )
    plotly = _plotly_specs(patient_id, labs, images, comparator_rows)
    chart_paths = _write_charts(bundle_dir, patient_id, labs, comparator_rows)
    pdf_documents = _write_pdf_corpus(
        bundle_dir, patient, labs, images, notes, timeline, pdfs_per_bundle
    )
    knowledge_base_documents = _write_knowledge_base_corpus(
        bundle_dir, patient, labs, notes, timeline, kb_docs_per_bundle
    )
    citations = (
        [
            {
                "citation_id": document["document_id"],
                "source_id": document["path"],
                "kind": "document",
                "excerpt": "Knowledge-base upload file with searchable patient evidence.",
            }
            for document in knowledge_base_documents[:16]
        ]
        + [
            {
                "citation_id": document["document_id"],
                "source_id": document["path"],
                "kind": "pdf",
                "excerpt": "Uploadable PDF packet with clinical text, evidence table, and embedded trend chart.",
            }
            for document in pdf_documents[:16]
        ]
        + [
            {
                "citation_id": note["vector_chunk_id"],
                "source_id": note["note_id"],
                "kind": "text",
                "excerpt": note["text"],
            }
            for note in notes[:20]
        ]
        + [
            {
                "citation_id": image["image_id"],
                "source_id": image["gcs_uri"],
                "kind": "image",
                "excerpt": image["description"],
            }
            for image in images[:8]
        ]
    )
    prompts = [
        {
            "question": "What changed across the last 90 days and which evidence supports it?",
            "expected_sources": ["metric_trends", "clinical_notes", "image_modalities"],
            "expected_output": "Narrative answer with cited trend, note, and image evidence.",
        },
        {
            "question": "Use the uploaded PDFs to answer with a short summary, a table, and one visual trend.",
            "expected_sources": ["pdf_documents", "metric_trends", "citations"],
            "expected_output": "Multimodal answer containing text, tabular evidence, and chart/image evidence.",
        },
        {
            "question": "Search the uploaded knowledge base and answer using DOCX, PDF, Markdown, TXT, and JSON sources.",
            "expected_sources": [
                "knowledge_base_documents",
                "citations",
                "metric_trends",
            ],
            "expected_output": "Evidence-grounded answer from mixed document formats with citations.",
        },
        {
            "question": "Compare this patient against similar high-risk patients and show visual evidence.",
            "expected_sources": ["comparator_risk", "metric_trends"],
            "expected_output": "Population-aware summary with comparator distribution and patient-specific trend.",
        },
        {
            "question": "Which findings require clinician review before persistence?",
            "expected_sources": ["timeline", "citations", "labs"],
            "expected_output": "Review checklist with reopenable citations and confidence caveats.",
        },
    ]
    bundle = {
        "patient": patient,
        "row_counts": {
            "labs": len(labs),
            "images": len(images),
            "pdf_documents": len(pdf_documents),
            "knowledge_base_documents": len(knowledge_base_documents),
            "notes": len(notes),
            "timeline": len(timeline),
            "comparators": len(comparator_rows),
            "citations": len(citations),
        },
        "labs": labs,
        "images": images,
        "pdf_documents": pdf_documents,
        "knowledge_base_documents": knowledge_base_documents,
        "notes": notes,
        "timeline": timeline,
        "comparator_cohort": comparator_rows,
        "citations": citations,
        "plotly": plotly,
        "matplotlib_pngs": chart_paths,
        "qa_prompts": prompts,
        "backend_contract": {
            "route": "/api/runs/qa",
            "requiredBody": {
                "patientId": patient_id,
                "question": "...",
                "source_types": ["document", "pdf", "text", "image", "lab"],
            },
        },
    }
    (bundle_dir / "bundle.json").write_text(
        json.dumps(bundle, indent=2), encoding="utf-8"
    )
    (bundle_dir / "qa_prompts.json").write_text(
        json.dumps(prompts, indent=2), encoding="utf-8"
    )
    (bundle_dir / "plotly_specs.json").write_text(
        json.dumps(plotly, indent=2), encoding="utf-8"
    )
    return {
        "patient_id": patient_id,
        "risk_level": patient.get("risk_level", "needs_review"),
        "completeness": patient.get("data_completeness_score", 0.9),
        "organization": patient.get("organization"),
        "source_systems": patient.get("source_systems", []),
        "path": str(bundle_dir / "bundle.json"),
        "pdf_directory": str(bundle_dir / "documents"),
        "knowledge_base_directory": str(bundle_dir / "knowledge_base"),
        "row_counts": bundle["row_counts"],
    }


def build_bundle_from_template_item(
    bundle_index: int, item: dict[str, Any], output: Path, rng: random.Random
) -> dict[str, Any]:
    """Build one complete multimodal Q&A bundle from a template item."""

    patient_data = item["patient"]
    patient_id = patient_data["patient_id"]
    bundle_dir = output / patient_id
    bundle_dir.mkdir(parents=True, exist_ok=True)

    # 1. Map labs
    labs = []
    for idx, lab in enumerate(item.get("labs", []), 1):
        labs.append(
            {
                "patient_id": patient_id,
                "date": lab.get("date", "2026-07-05"),
                "metric": lab.get("metric") or lab.get("component") or "tumor_size_cm",
                "value": lab.get("value", 0),
                "unit": lab.get("unit", ""),
                "flag": lab.get("flag", "normal"),
            }
        )
    if not labs:
        labs = [
            {
                "patient_id": patient_id,
                "date": "2026-07-05",
                "metric": "tumor_size_cm",
                "value": 3.0,
                "unit": "cm",
                "flag": "normal",
            }
        ]

    # 2. Map notes
    notes = []
    for idx, note in enumerate(item.get("notes", []), 1):
        notes.append(
            {
                "note_id": note.get("note_id") or f"NOTE-{patient_id}-{idx:03d}",
                "patient_id": patient_id,
                "date": note.get("date", "2026-07-05"),
                "author": note.get("author") or "Dr. Sarah Miller",
                "note_type": note.get("note_type")
                or note.get("type")
                or "Progress Note",
                "text": note.get("text", ""),
                "vector_chunk_id": note.get("vector_chunk_id")
                or f"VEC-{patient_id}-{idx:03d}",
                "keywords": note.get("keywords") or ["clinical"],
            }
        )
    if not notes:
        notes = [
            {
                "note_id": f"NOTE-{patient_id}-001",
                "patient_id": patient_id,
                "date": "2026-07-05",
                "author": "Dr. Sarah Miller",
                "note_type": "Progress Note",
                "text": "Initial template note.",
                "vector_chunk_id": f"VEC-{patient_id}-001",
                "keywords": ["clinical"],
            }
        ]

    # 3. Map timeline
    timeline = []
    for idx, event in enumerate(item.get("timeline", []), 1):
        timeline.append(
            {
                "patient_id": patient_id,
                "date": event.get("date", "2026-07-05"),
                "event_id": f"EVT-{patient_id}-{idx:03d}",
                "event_type": event.get("event_type")
                or event.get("type")
                or "Encounter",
                "summary": event.get("summary") or event.get("description") or "",
                "author": event.get("author") or "Dr. Sarah Miller",
            }
        )
    if not timeline:
        timeline = [
            {
                "patient_id": patient_id,
                "date": "2026-07-05",
                "event_id": f"EVT-{patient_id}-001",
                "event_type": "Encounter",
                "summary": "Initial intake encounter.",
                "author": "Dr. Sarah Miller",
            }
        ]

    # 4. Map images
    images = []
    for idx, img in enumerate(item.get("images", []), 1):
        images.append(
            {
                "image_id": img.get("image_id") or f"IMG-{patient_id}-{idx:03d}",
                "patient_id": patient_id,
                "date": img.get("date", "2026-07-05"),
                "gcs_uri": img.get("gcs_uri")
                or f"gs://clinical-data/{patient_id}/images/img-{idx}.png",
                "modality": img.get("modality") or "CT",
                "body_region": img.get("body_region") or "Chest",
                "description": img.get("description") or "",
                "quality_score": img.get("quality_score") or 0.95,
                "visual_findings": img.get("visual_findings") or ["stable", "lesion"],
            }
        )
    if not images:
        images = [
            {
                "image_id": f"IMG-{patient_id}-001",
                "patient_id": patient_id,
                "date": "2026-07-05",
                "gcs_uri": f"gs://clinical-data/{patient_id}/images/img-1.png",
                "modality": "CT",
                "body_region": "Chest",
                "description": "Dummy image",
                "quality_score": 0.95,
                "visual_findings": ["stable"],
            }
        ]

    # 5. Map comparators
    comparator_rows = []
    for idx, comp in enumerate(item.get("comparator_cohort", []), 1):
        comparator_rows.append(
            {
                "patient_id": comp.get("patient_id") or f"COMP-{patient_id}-{idx:03d}",
                "name": comp.get("name") or f"Comparator Patient {idx:03d}",
                "age": comp.get("age") or 60,
                "sex": comp.get("sex") or "Male",
                "risk_level": comp.get("risk_level") or "stable",
                "primary_diagnosis": comp.get("primary_diagnosis")
                or "Metastatic NSCLC",
                "assigned_clinician": comp.get("assigned_clinician")
                or "Dr. Sarah Miller",
            }
        )
    if not comparator_rows:
        comparator_rows = [
            {
                "patient_id": f"COMP-{patient_id}-001",
                "name": "Dummy Comparator",
                "age": 60,
                "sex": "Male",
                "risk_level": "stable",
                "primary_diagnosis": "Metastatic NSCLC",
                "assigned_clinician": "Dr. Sarah Miller",
            }
        ]

    # 6. Specs, charts, PDFs, KB
    plotly = _plotly_specs(patient_id, labs, images, comparator_rows)
    chart_paths = _write_charts(bundle_dir, patient_id, labs, comparator_rows)

    pdf_count = min(3, len(notes))
    kb_count = min(3, len(notes))
    pdf_documents = _write_pdf_corpus(
        bundle_dir, patient_data, labs, images, notes, timeline, pdf_count
    )
    knowledge_base_documents = _write_knowledge_base_corpus(
        bundle_dir, patient_data, labs, notes, timeline, kb_count
    )

    citations = (
        [
            {
                "citation_id": document["document_id"],
                "source_id": document["path"],
                "kind": "document",
                "excerpt": "Knowledge-base upload file.",
            }
            for document in knowledge_base_documents
        ]
        + [
            {
                "citation_id": document["document_id"],
                "source_id": document["path"],
                "kind": "pdf",
                "excerpt": "Uploadable PDF packet.",
            }
            for document in pdf_documents
        ]
        + [
            {
                "citation_id": note["vector_chunk_id"],
                "source_id": note["note_id"],
                "kind": "text",
                "excerpt": note["text"],
            }
            for note in notes
        ]
        + [
            {
                "citation_id": image["image_id"],
                "source_id": image["gcs_uri"],
                "kind": "image",
                "excerpt": image["description"],
            }
            for image in images
        ]
    )

    # 7. Prompts
    prompts = []
    for prompt in item.get("qa_prompts", []):
        prompts.append(
            {
                "question": prompt["question"],
                "expected_sources": prompt.get("expected_sources", ["clinical_notes"]),
                "expected_output": prompt["expected_output"],
            }
        )
    if not prompts:
        prompts = [
            {
                "question": "What is the status of the patient?",
                "expected_sources": ["clinical_notes"],
                "expected_output": f"The patient is {patient_data['name']} with {patient_data['primary_diagnosis']}.",
            }
        ]

    bundle = {
        "patient": patient_data,
        "row_counts": {
            "labs": len(labs),
            "images": len(images),
            "pdf_documents": len(pdf_documents),
            "knowledge_base_documents": len(knowledge_base_documents),
            "notes": len(notes),
            "timeline": len(timeline),
            "comparators": len(comparator_rows),
            "citations": len(citations),
        },
        "labs": labs,
        "images": images,
        "pdf_documents": pdf_documents,
        "knowledge_base_documents": knowledge_base_documents,
        "notes": notes,
        "timeline": timeline,
        "comparator_cohort": comparator_rows,
        "citations": citations,
        "plotly": plotly,
        "matplotlib_pngs": chart_paths,
        "qa_prompts": prompts,
        "backend_contract": {
            "route": "/api/runs/qa",
            "requiredBody": {
                "patientId": patient_id,
                "question": "...",
                "source_types": ["document", "pdf", "text", "image", "lab"],
            },
        },
    }

    (bundle_dir / "bundle.json").write_text(
        json.dumps(bundle, indent=2), encoding="utf-8"
    )
    (bundle_dir / "qa_prompts.json").write_text(
        json.dumps(prompts, indent=2), encoding="utf-8"
    )
    (bundle_dir / "plotly_specs.json").write_text(
        json.dumps(plotly, indent=2), encoding="utf-8"
    )
    return {
        "patient_id": patient_id,
        "path": str(bundle_dir / "bundle.json"),
        "pdf_directory": str(bundle_dir / "documents"),
        "knowledge_base_directory": str(bundle_dir / "knowledge_base"),
        "row_counts": bundle["row_counts"],
    }


def _app_contract(bundles: list[dict[str, Any]], demo_platform: str) -> dict[str, Any]:
    """Create app-facing dashboard, file-picker, and retrieval seed data."""

    totals: dict[str, int] = {}
    for bundle in bundles:
        for key, value in bundle["row_counts"].items():
            totals[key] = totals.get(key, 0) + int(value)
    patients = [bundle["patient_id"] for bundle in bundles]
    high_risk = sum(1 for bundle in bundles if bundle.get("risk_level") == "high")
    pending_review = sum(
        1 for bundle in bundles if bundle.get("risk_level") in {"high", "needs_review"}
    )
    stored_files = totals.get("pdf_documents", 0) + totals.get(
        "knowledge_base_documents", 0
    )
    avg_completeness = round(
        sum(float(bundle.get("completeness", 0.9)) for bundle in bundles)
        / max(1, len(bundles))
        * 100
    )
    return {
        "demoPlatform": demo_platform,
        "dashboardSeed": {
            "patients": len(patients),
            "sessions": totals.get("timeline", 0),
            "highRiskEstimate": high_risk,
            "pendingReviewEstimate": pending_review,
            "storedFiles": stored_files,
            "storedAssets": stored_files,
            "imageEvidence": totals.get("images", 0),
            "notes": totals.get("notes", 0),
            "citations": totals.get("citations", 0),
            "comparators": totals.get("comparators", 0),
            "knowledgeBaseDocuments": totals.get("knowledge_base_documents", 0),
            "qaPrompts": len(patients) * 5,
            "agentRuns24h": max(8, len(patients) * 3),
            "auditEvents": len(patients) * 12,
            "openAiAlerts": pending_review,
            "completeness": avg_completeness,
            "failedExtractions": 0,
        },
        "storageSeed": {
            "cloudObjects": stored_files,
            "jsonDocuments": len(patients),
            "relationalRows": totals.get("labs", 0) + totals.get("timeline", 0),
            "vectorRecords": totals.get("notes", 0) + totals.get("citations", 0),
            "auditEvents": len(patients) * 12,
            "failedRecords": 0,
        },
        "syntheticKnowledgeBase": [
            {
                "patientId": bundle["patient_id"],
                "bundlePath": bundle["path"],
                "pdfDirectory": bundle["pdf_directory"],
                "knowledgeBaseDirectory": bundle["knowledge_base_directory"],
                "rowCounts": bundle["row_counts"],
                "organization": bundle.get("organization"),
                "sourceSystems": bundle.get("source_systems", []),
            }
            for bundle in bundles
        ],
        "agentMonitoringSeed": [
            {
                "pipeline": "qa",
                "agent": "context_assembly_agent",
                "runs": len(patients) * 3,
                "avgConfidence": 0.92,
                "failureRate": 0.0,
                "reviewRate": round(pending_review / max(1, len(patients)), 2),
                "avgDurationMs": 620,
            },
            {
                "pipeline": "qa",
                "agent": "evidence_retrieval_agent",
                "runs": len(patients) * 3,
                "avgConfidence": 0.9,
                "failureRate": 0.0,
                "reviewRate": 0.0,
                "avgDurationMs": 1380,
            },
            {
                "pipeline": "qa",
                "agent": "image_evidence_agent",
                "runs": len(patients) * 2,
                "avgConfidence": 0.88,
                "failureRate": 0.0,
                "reviewRate": 0.0,
                "avgDurationMs": 1660,
            },
            {
                "pipeline": "qa",
                "agent": "citation_builder_agent",
                "runs": len(patients) * 3,
                "avgConfidence": 0.93,
                "failureRate": 0.0,
                "reviewRate": 0.0,
                "avgDurationMs": 840,
            },
            {
                "pipeline": "qa",
                "agent": "answer_synthesis_agent",
                "runs": len(patients) * 3,
                "avgConfidence": 0.91,
                "failureRate": 0.0,
                "reviewRate": 0.0,
                "avgDurationMs": 1810,
            },
        ],
    }


def generate(
    output: Path,
    bundle_count: int,
    days: int,
    comparators: int,
    seed: int,
    pdfs_per_bundle: int = DEFAULT_PDFS_PER_BUNDLE,
    kb_docs_per_bundle: int = DEFAULT_KB_DOCS_PER_BUNDLE,
    template_path: Path | None = None,
    demo_platform: str = "primary",
    patient_prefix: str = "PT-D",
) -> dict[str, Any]:
    """Generate all multimodal bundles."""

    rng = random.Random(seed)
    output.mkdir(parents=True, exist_ok=True)
    providers = core.build_providers(seed, demo_platform)

    if template_path:
        with open(template_path, "r", encoding="utf-8") as f:
            template_data = json.load(f)
        if not isinstance(template_data, list):
            template_data = [template_data]

        bundles = []
        index = 0
        for item in template_data:
            if not isinstance(item, dict) or "patient" not in item:
                continue
            index += 1
            bundles.append(build_bundle_from_template_item(index, item, output, rng))
    else:
        bundles = [
            build_bundle(
                index,
                output,
                rng,
                days,
                comparators,
                pdfs_per_bundle,
                kb_docs_per_bundle,
                demo_platform,
                patient_prefix,
                seed,
                providers,
            )
            for index in range(1, bundle_count + 1)
        ]

    app_contract = _app_contract(bundles, demo_platform)
    manifest = {
        "module": "multimodal_patient_qa",
        "demo_platform": demo_platform,
        "patient_prefix": patient_prefix,
        "focus_patient_ids": [bundle["patient_id"] for bundle in bundles],
        "bundle_count": len(bundles),
        "pdf_count": sum(bundle["row_counts"]["pdf_documents"] for bundle in bundles),
        "knowledge_base_document_count": sum(
            bundle["row_counts"]["knowledge_base_documents"] for bundle in bundles
        ),
        "bundles": bundles,
        "upload_contract": {
            "route": "/api/assets",
            "contentType": "application/pdf",
            "batchPattern": "Upload files from each bundle documents/ directory, then ask one patient-scoped Q&A prompt.",
        },
        "knowledge_base_contract": {
            "route": "/api/knowledge-base/assets",
            "extensions": list(KB_EXTENSIONS),
            "contentTypes": [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "text/markdown",
                "text/plain",
                "application/json",
            ],
            "followupRoute": "/api/runs/qa",
            "sourceTypes": ["document"],
        },
        "frontend_contract": {
            "views": [
                "Patient profile",
                "Multimodal patient Q&A",
                "Evidence citations",
                "Chart builder",
            ],
            "needs": [
                "dense patient detail",
                "PDF source viewer",
                "multiple Plotly panels",
                "citation table",
            ],
            **app_contract,
        },
    }
    (output / "app_manifest.json").write_text(
        json.dumps(app_contract, indent=2), encoding="utf-8"
    )
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(
        description="Generate multimodal patient Q&A showcase bundles."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bundle-count", type=int, default=12)
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--comparators", type=int, default=420)
    parser.add_argument("--pdfs-per-bundle", type=int, default=DEFAULT_PDFS_PER_BUNDLE)
    parser.add_argument(
        "--kb-docs-per-bundle", type=int, default=DEFAULT_KB_DOCS_PER_BUNDLE
    )
    parser.add_argument("--seed", type=int, default=240624)
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--demo-platform", default="primary")
    parser.add_argument("--patient-prefix", default="PT-D")
    args = parser.parse_args()
    manifest = generate(
        args.output,
        args.bundle_count,
        args.days,
        args.comparators,
        args.seed,
        args.pdfs_per_bundle,
        args.kb_docs_per_bundle,
        args.template,
        args.demo_platform,
        args.patient_prefix,
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "bundle_count": manifest["bundle_count"],
                "pdf_count": manifest["pdf_count"],
                "knowledge_base_document_count": manifest[
                    "knowledge_base_document_count"
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
