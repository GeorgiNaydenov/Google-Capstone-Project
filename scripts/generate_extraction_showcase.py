"""Generate production-like extraction packets for the extraction agent.

The output is a set of five-patient PDF packets plus PNG previews and JSON
ground truth. Each packet is acceptable by the app upload policy, while each
patient preview gives the frontend a fast visual picker for demo mode.
"""

from __future__ import annotations

import argparse
import json
import random
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import showcase_clinical_core as core


DEFAULT_OUTPUT = Path("showcase_data/extraction")
DEFAULT_FRONTEND_PUBLIC = Path("frontend/public/demo-data/extraction")
DEFAULT_ANCHOR_DATE = date(2026, 7, 5)
DEFAULT_PATIENTS_PER_FILE = 5


def _font(size: int) -> ImageFont.ImageFont:
    """Load a readable font with a platform-safe fallback."""

    for name in ("arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _series(base: float, points: int, rng: random.Random) -> list[float]:
    """Create a noisy clinical trend series for the embedded chart."""

    values = []
    current = base
    for _ in range(points):
        current += rng.uniform(-0.8, 1.2)
        values.append(round(max(0.1, current), 1))
    return values


def _numeric_value(value: Any) -> float:
    """Return a numeric plotting value from a generated lab value."""

    try:
        return float(value)
    except (TypeError, ValueError):
        return 1.0


def _wrap(text: str, width: int) -> list[str]:
    """Wrap simple text without pulling in external layout dependencies."""

    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join([*current, word])
        if len(candidate) > width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


def _draw_chart(
    draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], values: list[float]
) -> None:
    """Draw a compact trend visualization inside the source page."""

    left, top, right, bottom = box
    draw.rectangle(box, outline="#90a4b8", width=2, fill="#f7fafc")
    draw.text(
        (left + 12, top + 8), "Longitudinal signal", fill="#0f172a", font=_font(18)
    )
    chart_left, chart_top, chart_right, chart_bottom = (
        left + 40,
        top + 48,
        right - 24,
        bottom - 26,
    )
    draw.line(
        (chart_left, chart_bottom, chart_right, chart_bottom), fill="#64748b", width=2
    )
    draw.line(
        (chart_left, chart_top, chart_left, chart_bottom), fill="#64748b", width=2
    )
    high = max(values)
    low = min(values)
    span = max(0.1, high - low)
    points: list[tuple[float, float]] = []
    for index, value in enumerate(values):
        x = chart_left + index * ((chart_right - chart_left) / max(1, len(values) - 1))
        y = chart_bottom - ((value - low) / span) * (chart_bottom - chart_top)
        points.append((x, y))
    draw.line(points, fill="#2563eb", width=4)
    for x, y in points:
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill="#dc2626")
    draw.text(
        (chart_left, chart_bottom + 4), f"low {low}", fill="#475569", font=_font(13)
    )
    draw.text(
        (chart_right - 72, chart_bottom + 4),
        f"high {high}",
        fill="#475569",
        font=_font(13),
    )


def build_sample(
    index: int,
    rng: random.Random,
    demo_platform: str = "primary",
    patient_prefix: str = "PT-D",
    anchor_date: date = DEFAULT_ANCHOR_DATE,
    seed: int = 240624,
    providers: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Create one extraction target with expected structured output."""

    provider_rows = providers or core.build_providers(seed, demo_platform)
    profile = core.build_patient(
        index, seed, patient_prefix, anchor_date, 4, provider_rows, demo_platform
    )
    encounter = anchor_date - timedelta(days=7 + index)
    lab_results = [
        result
        for panel in profile.get("panels", [])
        for result in panel.get("results", [])
    ]
    lab_components = (
        rng.sample(lab_results, min(6, len(lab_results))) if lab_results else []
    )
    fields = []
    for result in lab_components:
        value = result.get("value", "")
        flag = result.get("flag", "normal")
        low = result.get("low", "")
        high = result.get("high", "")
        confidence = round(rng.uniform(0.72, 0.98), 2)
        label = str(result.get("test", "clinical_metric"))
        fields.append(
            {
                "field_name": label.lower().replace(" ", "_").replace("/", "_"),
                "label": label,
                "panel": result.get("category", "Lab"),
                "value": value,
                "unit": result.get("unit", ""),
                "referenceRange": f"{low}-{high}" if low != "" and high != "" else "",
                "loinc": result.get("loinc", ""),
                "flag": flag,
                "confidence": confidence,
                "needs_review": flag != "normal" or confidence < 0.82,
            }
        )
    if not fields:
        for metric, value in list(profile.get("key_metrics", {}).items())[:4]:
            fields.append(
                {
                    "field_name": metric,
                    "label": metric.replace("_", " ").title(),
                    "panel": "Key metrics",
                    "value": value,
                    "unit": "",
                    "referenceRange": "",
                    "flag": "normal",
                    "confidence": 0.9,
                    "needs_review": False,
                }
            )

    first_numeric = _numeric_value(fields[0]["value"])
    trend_values = _series(first_numeric, 8, rng)
    flagged = [field["label"] for field in fields if field["needs_review"]]
    authored_note = profile.get("notes", [{}])[0].get("text", "")
    note = "\n".join(
        [
            authored_note,
            f"Packet signal: {fields[0]['label']} changed from {trend_values[0]} to {trend_values[-1]} across 8 points.",
            f"Source systems: {', '.join(profile.get('source_systems', []))}.",
            f"Review focus: {profile.get('primary_diagnosis')} longitudinal evidence, care gaps, payer context, and recent abnormal labs.",
            f"Review flags: {', '.join(flagged) if flagged else 'none above threshold'}.",
        ]
    )
    patient = {
        "patient_id": profile["patient_id"],
        "mrn": profile["mrn"],
        "name": profile["name"],
        "age": profile["age"],
        "sex": profile["sex"],
        "diagnosis": profile["primary_diagnosis"],
        "clinician": profile["provider"]["full_name"],
        "riskLevel": profile["risk_level"],
        "preferredLanguage": profile["language"],
        "archetype": profile["archetype"],
        "privacyClass": profile["privacy_class"],
    }
    return {
        "sample_id": f"EXT-{index:04d}",
        "patient": patient,
        "encounter_date": encounter.isoformat(),
        "note": note,
        "fields": fields,
        "trend_values": trend_values,
        "expected_agent_output": {
            "documentType": "Enterprise five-patient clinical packet",
            "patientMatch": patient["patient_id"],
            "finding": note,
            "extractedFields": fields,
            "visualization": {"type": "line", "points": trend_values},
            "reviewRequired": any(field["needs_review"] for field in fields),
        },
    }


def _draw_patient_page(
    sample: dict[str, Any],
    demo_platform: str,
    packet_id: str,
    page_number: int,
    packet_total: int,
) -> Image.Image:
    """Render one patient page used both as PDF page and PNG preview."""

    tenant = core.TENANT_THEMES.get(demo_platform, core.TENANT_THEMES["primary"])
    image = Image.new("RGB", (1500, 1100), "#f8fafc")
    draw = ImageDraw.Draw(image)
    title_font = _font(32)
    body_font = _font(22)
    small_font = _font(18)
    mono_font = _font(18)

    draw.rectangle((0, 0, 1500, 104), fill="#0f172a")
    draw.text(
        (36, 22),
        f"{tenant['org']} Enterprise Extraction Packet",
        fill="white",
        font=title_font,
    )
    draw.text((1030, 28), "SYNTHETIC DEMO DATA", fill="#bfdbfe", font=body_font)
    draw.text(
        (1030, 62),
        f"{packet_id} | Page {page_number} of {packet_total}",
        fill="#cbd5e1",
        font=small_font,
    )

    patient = sample["patient"]
    y = 132
    lines = [
        f"Patient: {patient['name']}   ID: {patient['patient_id']}   MRN: {patient['mrn']}",
        f"Age/Sex: {patient['age']} / {patient['sex']}   Clinician: {patient['clinician']}",
        f"Risk: {patient['riskLevel']}   Language: {patient['preferredLanguage']}   Encounter: {sample['encounter_date']}",
        f"Diagnosis: {patient['diagnosis']}",
    ]
    for line in lines:
        draw.text((48, y), line, fill="#0f172a", font=body_font)
        y += 36

    draw.rounded_rectangle(
        (42, 292, 865, 746), radius=12, outline="#cbd5e1", width=2, fill="#ffffff"
    )
    draw.text(
        (70, 318), "Clinician narrative / OCR target", fill="#1e3a8a", font=body_font
    )
    note_lines: list[str] = []
    for source_line in sample["note"].splitlines():
        note_lines.extend(_wrap(source_line, 76))
    for index, line in enumerate(note_lines[:12]):
        draw.text((75, 363 + index * 29), line, fill="#1f2937", font=small_font)

    draw.rounded_rectangle(
        (910, 292, 1450, 746), radius=12, outline="#cbd5e1", width=2, fill="#ffffff"
    )
    draw.text(
        (940, 318), "Structured extraction target", fill="#1e3a8a", font=body_font
    )
    draw.line((930, 356, 1425, 356), fill="#94a3b8", width=2)
    draw.text((940, 370), "field", fill="#475569", font=mono_font)
    draw.text((1168, 370), "value", fill="#475569", font=mono_font)
    draw.text((1322, 370), "flag", fill="#475569", font=mono_font)
    for index, field in enumerate(sample["fields"][:6]):
        row_y = 411 + index * 49
        draw.text(
            (940, row_y), str(field["label"])[:20], fill="#0f172a", font=mono_font
        )
        draw.text(
            (1168, row_y),
            f"{field['value']} {field['unit']}",
            fill="#0f172a",
            font=mono_font,
        )
        draw.text(
            (1322, row_y),
            str(field["flag"])[:10],
            fill="#b45309" if field["flag"] != "normal" else "#166534",
            font=mono_font,
        )

    draw.rounded_rectangle(
        (42, 770, 700, 1042), radius=12, outline="#cbd5e1", width=2, fill="#ffffff"
    )
    draw.text((70, 797), "Cross-system context", fill="#1e3a8a", font=body_font)
    context_lines = [
        f"Care archetype: {patient['archetype']}",
        f"Privacy class: {patient['privacyClass']}",
        f"Review required: {'yes' if sample['expected_agent_output']['reviewRequired'] else 'no'}",
        "Packet rule: five patients per accepted PDF source file",
    ]
    for index, line in enumerate(context_lines):
        draw.text((76, 842 + index * 34), line, fill="#334155", font=small_font)

    _draw_chart(draw, (730, 770, 1450, 1042), sample["trend_values"])
    return image


def _write_packet(
    samples: list[dict[str, Any]], packet_path: Path, demo_platform: str, packet_id: str
) -> None:
    """Write a multi-page PDF packet with one patient page per sample."""

    pages = [
        _draw_patient_page(sample, demo_platform, packet_id, index, len(samples))
        for index, sample in enumerate(samples, 1)
    ]
    pages[0].save(
        packet_path, "PDF", resolution=150.0, save_all=True, append_images=pages[1:]
    )


def _attach_packet_artifacts(
    output: Path,
    samples: list[dict[str, Any]],
    demo_platform: str,
    patients_per_file: int,
) -> list[dict[str, Any]]:
    """Render PDF packets and per-patient preview images, then attach paths."""

    image_dir = output / "images"
    packet_dir = output / "packets"
    image_dir.mkdir(parents=True, exist_ok=True)
    packet_dir.mkdir(parents=True, exist_ok=True)
    packets: list[dict[str, Any]] = []

    for packet_index, start in enumerate(range(0, len(samples), patients_per_file), 1):
        packet_samples = samples[start : start + patients_per_file]
        packet_id = f"PKT-EXT-{packet_index:04d}"
        packet_path = packet_dir / f"{packet_id}.pdf"
        _write_packet(packet_samples, packet_path, demo_platform, packet_id)
        patient_ids = [sample["patient"]["patient_id"] for sample in packet_samples]
        packets.append(
            {
                "packet_id": packet_id,
                "packet_path": str(packet_path),
                "patient_ids": patient_ids,
                "patient_count": len(packet_samples),
                "content_type": "application/pdf",
            }
        )
        for page_number, sample in enumerate(packet_samples, 1):
            preview_path = image_dir / f"{sample['sample_id']}.png"
            page = _draw_patient_page(
                sample, demo_platform, packet_id, page_number, len(packet_samples)
            )
            page.save(preview_path)
            sample["asset_path"] = str(packet_path)
            sample["preview_path"] = str(preview_path)
            sample["content_type"] = "application/pdf"
            sample["preview_content_type"] = "image/png"
            sample["packet_id"] = packet_id
            sample["packet_path"] = str(packet_path)
            sample["packet_patient_ids"] = patient_ids
            sample["patient_count_in_file"] = len(packet_samples)
    return packets


def _sample_from_template(item: dict[str, Any], index: int) -> dict[str, Any]:
    """Normalize a user template row into the generated sample contract."""

    fields = []
    for field in item.get("fields", []):
        fields.append(
            {
                "field_name": field["field_name"],
                "label": field.get("label", field["field_name"]),
                "panel": field.get("panel", "Template"),
                "value": field["value"],
                "unit": field.get("unit", ""),
                "referenceRange": field.get("referenceRange", ""),
                "flag": field.get("flag", "normal"),
                "confidence": field.get("confidence", 0.95),
                "needs_review": field.get("needs_review", False),
            }
        )
    patient = item["patient"]
    patient.setdefault("riskLevel", "moderate")
    patient.setdefault("preferredLanguage", "English")
    patient.setdefault("archetype", "template")
    patient.setdefault("privacyClass", "synthetic")
    note = item.get("note", "")
    return {
        "sample_id": f"EXT-T{index:04d}",
        "patient": patient,
        "encounter_date": item.get("encounter_date", DEFAULT_ANCHOR_DATE.isoformat()),
        "note": note,
        "fields": fields,
        "trend_values": item.get("trend_values", [1, 2, 3, 4, 5, 6, 7, 8]),
        "expected_agent_output": {
            "documentType": "Enterprise five-patient clinical packet",
            "patientMatch": patient["patient_id"],
            "finding": note,
            "extractedFields": fields,
            "visualization": {"type": "line", "points": item.get("trend_values", [])},
            "reviewRequired": any(field["needs_review"] for field in fields),
        },
    }


def _write_frontend_catalog(
    samples: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    demo_platform: str,
    frontend_public: Path | None,
    patients_per_file: int,
) -> dict[str, Any]:
    """Write an app-facing synthetic picker catalog and optionally copy previews."""

    picker = []
    target_dir = None
    if frontend_public:
        target_dir = frontend_public / demo_platform / "images"
        target_dir.mkdir(parents=True, exist_ok=True)
    for index, sample in enumerate(samples[:10], 1):
        preview_source = Path(sample["preview_path"])
        public_path = (
            f"/demo-data/extraction/{demo_platform}/images/{preview_source.name}"
        )
        if target_dir:
            shutil.copy2(preview_source, target_dir / preview_source.name)
        packet_source = Path(sample["asset_path"])
        picker.append(
            {
                "id": sample["sample_id"],
                "label": f"{sample['patient']['diagnosis']} packet {sample['packet_id']}",
                "patientId": sample["patient"]["patient_id"],
                "patientName": sample["patient"]["name"],
                "previewUrl": public_path,
                "filename": packet_source.name,
                "packetFilename": packet_source.name,
                "contentType": "application/pdf",
                "sourceContentType": "application/pdf",
                "previewContentType": "image/png",
                "expectedFields": sample["fields"],
                "reviewRequired": sample["expected_agent_output"]["reviewRequired"],
                "packetId": sample["packet_id"],
                "patientsInFile": sample["patient_count_in_file"],
                "batchPatientIds": sample["packet_patient_ids"],
            }
        )

    unique_patients = {sample["patient"]["patient_id"] for sample in samples}
    review_count = sum(
        1 for sample in samples if sample["expected_agent_output"]["reviewRequired"]
    )
    field_total = max(1, sum(len(sample["fields"]) for sample in samples))
    avg_confidence = round(
        sum(
            float(field["confidence"])
            for sample in samples
            for field in sample["fields"]
        )
        / field_total,
        2,
    )
    packet_count = len(packets)
    return {
        "demoPlatform": demo_platform,
        "syntheticPickerCount": len(picker),
        "syntheticPicker": picker,
        "patientsPerFile": patients_per_file,
        "sourcePacketCount": packet_count,
        "dashboardSeed": {
            "patients": len(unique_patients),
            "sessions": len(samples),
            "highRiskEstimate": review_count,
            "pendingReviewEstimate": review_count,
            "pendingVerifications": review_count,
            "sourceImages": len(samples),
            "sourcePackets": packet_count,
            "sourceDocuments": packet_count,
            "patientsPerFile": patients_per_file,
            "pendingReviews": review_count,
            "imageExtractionsToday": len(samples),
            "agentRuns": len(samples),
            "agentRuns24h": len(samples),
            "storageObjects": packet_count,
            "storedAssets": packet_count,
            "jsonRecords": len(samples),
            "vectorRecords": len(samples) * 4,
            "averageConfidence": avg_confidence,
            "completeness": 94,
            "auditEvents": len(samples) * 4,
            "failedExtractions": 0,
            "openAiAlerts": review_count,
            "syncRate": 100,
        },
        "storageSeed": {
            "cloudObjects": packet_count,
            "jsonDocuments": len(samples),
            "relationalRows": sum(len(sample["fields"]) for sample in samples),
            "vectorRecords": len(samples) * 4,
            "auditEvents": len(samples) * 4,
            "failedRecords": 0,
        },
        "agentMonitoringSeed": [
            {
                "pipeline": "extraction",
                "agent": "quality_assessor_agent",
                "runs": len(samples),
                "avgConfidence": min(0.99, avg_confidence + 0.02),
                "failureRate": 0.0,
                "reviewRate": round(review_count / max(1, len(samples)), 2),
                "avgDurationMs": 760,
            },
            {
                "pipeline": "extraction",
                "agent": "pdf_packet_parser_agent",
                "runs": packet_count,
                "avgConfidence": avg_confidence,
                "failureRate": 0.0,
                "reviewRate": round(review_count / max(1, len(samples)), 2),
                "avgDurationMs": 1360,
            },
            {
                "pipeline": "extraction",
                "agent": "vision_analyzer_agent",
                "runs": len(samples),
                "avgConfidence": max(0.72, avg_confidence - 0.03),
                "failureRate": 0.0,
                "reviewRate": round(review_count / max(1, len(samples)), 2),
                "avgDurationMs": 1610,
            },
            {
                "pipeline": "extraction",
                "agent": "clinical_review_gate_agent",
                "runs": review_count,
                "avgConfidence": 0.9,
                "failureRate": 0.0,
                "reviewRate": 1.0 if review_count else 0.0,
                "avgDurationMs": 460,
            },
        ],
    }


def generate(
    output: Path,
    count: int,
    seed: int,
    template_path: Path | None = None,
    demo_platform: str = "primary",
    frontend_public: Path | None = None,
    patients_per_file: int = DEFAULT_PATIENTS_PER_FILE,
    patient_prefix: str = "PT-D",
) -> dict[str, Any]:
    """Generate extraction showcase files and return manifest."""

    rng = random.Random(seed)
    output.mkdir(parents=True, exist_ok=True)
    samples = []
    providers = core.build_providers(seed, demo_platform)

    if patients_per_file <= 0:
        raise ValueError("patients_per_file must be positive")

    if template_path:
        with open(template_path, "r", encoding="utf-8") as f:
            template_data = json.load(f)
        if not isinstance(template_data, list):
            template_data = [template_data]
        for index, item in enumerate(template_data, 1):
            if (
                isinstance(item, dict)
                and "patient" in item
                and item["patient"].get("patient_id")
            ):
                samples.append(_sample_from_template(item, index))
    else:
        for index in range(1, count + 1):
            samples.append(
                build_sample(
                    index,
                    rng,
                    demo_platform,
                    patient_prefix,
                    DEFAULT_ANCHOR_DATE,
                    seed,
                    providers,
                )
            )

    packets = _attach_packet_artifacts(
        output, samples, demo_platform, patients_per_file
    )
    frontend_contract = _write_frontend_catalog(
        samples, packets, demo_platform, frontend_public, patients_per_file
    )
    manifest = {
        "module": "image_extraction",
        "demo_platform": demo_platform,
        "sample_count": len(samples),
        "packet_count": len(packets),
        "patients_per_file": patients_per_file,
        "upload_contract": {
            "demoMode": "synthetic_picker",
            "liveRoute": "/api/assets",
            "contentType": "application/pdf",
            "contentTypes": ["application/pdf", "image/png"],
            "followupRoute": "/api/runs/extraction",
        },
        "frontend_contract": frontend_contract,
        "packets": packets,
        "samples": samples,
    }
    (output / "app_manifest.json").write_text(
        json.dumps(frontend_contract, indent=2), encoding="utf-8"
    )
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return manifest


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(
        description="Generate enterprise extraction showcase packets."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--count", type=int, default=48)
    parser.add_argument("--seed", type=int, default=240624)
    parser.add_argument("--template", type=Path, default=None)
    parser.add_argument("--demo-platform", default="primary")
    parser.add_argument("--frontend-public", type=Path, default=DEFAULT_FRONTEND_PUBLIC)
    parser.add_argument(
        "--patients-per-file", type=int, default=DEFAULT_PATIENTS_PER_FILE
    )
    parser.add_argument("--patient-prefix", default="PT-D")
    args = parser.parse_args()
    manifest = generate(
        args.output,
        args.count,
        args.seed,
        args.template,
        args.demo_platform,
        args.frontend_public,
        args.patients_per_file,
        args.patient_prefix,
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "sample_count": manifest["sample_count"],
                "packet_count": manifest["packet_count"],
                "patients_per_file": manifest["patients_per_file"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
