"""Generate synthetic extraction assets for the image extraction agent.

The output is a folder of PNG clinical-note images plus JSON ground truth.
Each image combines handwritten-style notes, structured tables, and a small
clinical visualization so the extraction workflow has dense multimodal input.
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


DEFAULT_OUTPUT = Path("showcase_data/extraction")
DIAGNOSES = (
    "Metastatic NSCLC",
    "Heart failure with reduced EF",
    "Type 2 diabetes with retinopathy",
    "Chronic kidney disease stage 4",
    "Crohn disease flare",
    "Aortic stenosis",
)
CLINICIANS = ("Dr. Sarah Miller", "Dr. Elena Park", "Dr. James Patel", "Dr. Priya Rao")
FIELDS = (
    ("tumor_size_cm", "cm", 2.1, 6.8),
    ("ejection_fraction_pct", "%", 25, 55),
    ("hba1c_pct", "%", 6.4, 10.8),
    ("egfr", "mL/min", 18, 88),
    ("bnp", "pg/mL", 90, 1450),
    ("crp", "mg/L", 1.2, 42.0),
)


def _font(size: int) -> ImageFont.ImageFont:
    """Load a readable font with a platform-safe fallback."""

    for name in ("arial.ttf", "segoeui.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _patient(index: int, rng: random.Random) -> dict[str, Any]:
    """Build deterministic synthetic patient metadata."""

    return {
        "patient_id": f"PT-X{index:04d}",
        "mrn": f"MRN-X{rng.randint(100000, 999999)}",
        "name": f"Showcase Patient {index:03d}",
        "age": rng.randint(28, 84),
        "sex": rng.choice(("Female", "Male")),
        "diagnosis": rng.choice(DIAGNOSES),
        "clinician": rng.choice(CLINICIANS),
    }


def _series(base: float, points: int, rng: random.Random) -> list[float]:
    """Create a noisy clinical trend series for the embedded chart."""

    values = []
    current = base
    for _ in range(points):
        current += rng.uniform(-0.9, 1.4)
        values.append(round(max(0.1, current), 1))
    return values


def _draw_chart(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], values: list[float]) -> None:
    """Draw a compact trend visualization inside the source image."""

    left, top, right, bottom = box
    draw.rectangle(box, outline="#90a4b8", width=2, fill="#f7fafc")
    draw.text((left + 12, top + 8), "Attached trend visualization", fill="#0f172a", font=_font(18))
    chart_left, chart_top, chart_right, chart_bottom = left + 40, top + 48, right - 24, bottom - 26
    draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill="#64748b", width=2)
    draw.line((chart_left, chart_top, chart_left, chart_bottom), fill="#64748b", width=2)
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
    draw.text((chart_left, chart_bottom + 4), f"low {low}", fill="#475569", font=_font(13))
    draw.text((chart_right - 70, chart_bottom + 4), f"high {high}", fill="#475569", font=_font(13))


def _draw_sample(sample: dict[str, Any], path: Path) -> None:
    """Render one clinical source image."""

    image = Image.new("RGB", (1500, 1100), "#f8fafc")
    draw = ImageDraw.Draw(image)
    title_font = _font(34)
    body_font = _font(22)
    small_font = _font(18)
    mono_font = _font(19)

    draw.rectangle((0, 0, 1500, 92), fill="#0f172a")
    draw.text((36, 24), "Nexus Clinical Intake Sheet", fill="white", font=title_font)
    draw.text((1050, 32), "SYNTHETIC DEMO DATA", fill="#bfdbfe", font=body_font)

    patient = sample["patient"]
    y = 125
    lines = [
        f"Patient: {patient['name']}   ID: {patient['patient_id']}   MRN: {patient['mrn']}",
        f"Age/Sex: {patient['age']} / {patient['sex']}   Clinician: {patient['clinician']}",
        f"Diagnosis: {patient['diagnosis']}   Encounter: {sample['encounter_date']}",
    ]
    for line in lines:
        draw.text((48, y), line, fill="#0f172a", font=body_font)
        y += 38

    draw.rounded_rectangle((42, 255, 865, 735), radius=12, outline="#cbd5e1", width=2, fill="#ffffff")
    draw.text((70, 282), "Clinician notes / OCR target", fill="#1e3a8a", font=body_font)
    note_lines = sample["note"].splitlines()
    for index, line in enumerate(note_lines[:12]):
        draw.text((75 + (index % 2) * 5, 330 + index * 29), line, fill="#1f2937", font=small_font)

    draw.rounded_rectangle((910, 255, 1450, 735), radius=12, outline="#cbd5e1", width=2, fill="#ffffff")
    draw.text((940, 282), "Structured measurements", fill="#1e3a8a", font=body_font)
    draw.line((930, 322, 1425, 322), fill="#94a3b8", width=2)
    draw.text((940, 336), "field", fill="#475569", font=mono_font)
    draw.text((1210, 336), "value", fill="#475569", font=mono_font)
    for index, field in enumerate(sample["fields"]):
        row_y = 380 + index * 50
        draw.text((940, row_y), field["field_name"], fill="#0f172a", font=mono_font)
        draw.text((1210, row_y), f"{field['value']} {field['unit']}", fill="#0f172a", font=mono_font)
        draw.text((1360, row_y), str(field["confidence"]), fill="#64748b", font=mono_font)

    _draw_chart(draw, (42, 780, 1450, 1040), sample["trend_values"])
    image.save(path)


def build_sample(index: int, rng: random.Random) -> dict[str, Any]:
    """Create one extraction sample with expected structured output."""

    patient = _patient(index, rng)
    encounter = date(2026, 6, 24) - timedelta(days=index)
    selected = rng.sample(FIELDS, 4)
    fields = []
    for name, unit, low, high in selected:
        value = round(rng.uniform(low, high), 1)
        fields.append(
            {
                "field_name": name,
                "value": value,
                "unit": unit,
                "confidence": round(rng.uniform(0.72, 0.98), 2),
                "needs_review": value > (low + high) / 2 and rng.random() > 0.45,
            }
        )
    trend_values = _series(float(fields[0]["value"]), 8, rng)
    flagged = [field["field_name"] for field in fields if field["needs_review"]]
    note = "\n".join(
        [
            "HPI: interval symptoms reviewed with care team.",
            f"Main condition remains {patient['diagnosis']}.",
            f"Latest extracted value: {fields[0]['field_name']} = {fields[0]['value']} {fields[0]['unit']}.",
            f"Trend attached: {trend_values[0]} -> {trend_values[-1]} across 8 points.",
            f"Medication reconciliation: {rng.choice(('complete', 'conflict found', 'pending pharmacy callback'))}.",
            f"Review flags: {', '.join(flagged) if flagged else 'none above threshold'}.",
            "Plan: compare source image, table values, and trend before persistence.",
        ]
    )
    return {
        "sample_id": f"EXT-{index:04d}",
        "patient": patient,
        "encounter_date": encounter.isoformat(),
        "note": note,
        "fields": fields,
        "trend_values": trend_values,
        "expected_agent_output": {
            "documentType": "Clinical intake sheet with embedded trend chart",
            "patientMatch": patient["patient_id"],
            "finding": note,
            "extractedFields": fields,
            "visualization": {"type": "line", "points": trend_values},
            "reviewRequired": any(field["needs_review"] for field in fields),
        },
    }


def generate(output: Path, count: int, seed: int) -> dict[str, Any]:
    """Generate extraction showcase files and return manifest."""

    rng = random.Random(seed)
    output.mkdir(parents=True, exist_ok=True)
    image_dir = output / "images"
    image_dir.mkdir(exist_ok=True)
    samples = []
    for index in range(1, count + 1):
        sample = build_sample(index, rng)
        image_path = image_dir / f"{sample['sample_id']}.png"
        _draw_sample(sample, image_path)
        sample["asset_path"] = str(image_path)
        samples.append(sample)

    manifest = {
        "module": "image_extraction",
        "sample_count": len(samples),
        "upload_contract": {
            "route": "/api/assets",
            "contentType": "image/png",
            "followupRoute": "/api/runs/extraction",
        },
        "samples": samples,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Generate image extraction showcase assets.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--count", type=int, default=48)
    parser.add_argument("--seed", type=int, default=240624)
    args = parser.parse_args()
    manifest = generate(args.output, args.count, args.seed)
    print(json.dumps({"output": str(args.output), "sample_count": manifest["sample_count"]}, indent=2))


if __name__ == "__main__":
    main()
