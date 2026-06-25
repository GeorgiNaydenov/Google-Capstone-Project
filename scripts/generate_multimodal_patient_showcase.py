"""Generate multimodal patient bundles for the Q&A agent.

Each bundle contains one dense patient record, many comparator patients,
evidence citations, Plotly visualization specs, Matplotlib chart images, and
ready-to-run Q&A prompts.
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


DEFAULT_OUTPUT = Path("showcase_data/multimodal")
DIAGNOSES = (
    "Metastatic NSCLC",
    "Heart failure with reduced EF",
    "Type 2 diabetes with retinopathy",
    "Chronic kidney disease stage 4",
    "Crohn disease flare",
)
METRICS = ("tumor_size_cm", "cea_ng_ml", "bnp_pg_ml", "egfr", "hba1c_pct", "crp_mg_l")
MODALITIES = ("CT chest", "CT abdomen", "MRI brain", "X-Ray chest", "Fundoscopy", "Clinical photo")
CLINICIANS = ("Dr. Sarah Miller", "Dr. Elena Park", "Dr. James Patel", "Dr. Priya Rao")


def _trend(start: float, drift: float, count: int, rng: random.Random, minimum: float = 0.1) -> list[float]:
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
        "allergies": rng.sample(("Penicillin", "Sulfonamides", "Iodine contrast", "NSAIDs", "None"), 2),
        "medications": [
            {"name": "Pembrolizumab", "dose": "200 mg IV q3w", "status": "active"},
            {"name": "Furosemide", "dose": "40 mg daily", "status": "active"},
            {"name": "Metformin", "dose": "1000 mg BID", "status": "active"},
            {"name": "Atorvastatin", "dose": "40 mg daily", "status": "active"},
        ],
    }


def _timeline(patient_id: str, rng: random.Random, event_count: int) -> list[dict[str, Any]]:
    """Build dated clinical events across notes, labs, images, and decisions."""

    today = date(2026, 6, 24)
    events = []
    for index in range(event_count):
        day = today - timedelta(days=event_count - index)
        source_type = rng.choice(("clinical_note", "lab", "image", "medication", "care_plan"))
        events.append(
            {
                "event_id": f"EV-{patient_id}-{index + 1:04d}",
                "date": day.isoformat(),
                "source_type": source_type,
                "title": f"{source_type.replace('_', ' ').title()} event {index + 1}",
                "summary": f"Synthetic {source_type} evidence contributes to longitudinal answer synthesis.",
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
    series = {name: _trend(base, drift, days, rng, 0.1) for name, (base, drift) in seeds.items()}
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
                    "flag": "high" if value > series[metric][max(0, day_index - 30)] * 1.1 else "normal",
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
                "visual_findings": rng.sample(("growth", "stable", "effusion", "edema", "lesion", "artifact"), 3),
            }
        )
    return images


def _notes(patient_id: str, rng: random.Random, count: int) -> list[dict[str, Any]]:
    """Create vector-searchable note chunks."""

    notes = []
    for index in range(1, count + 1):
        topic = rng.choice(("progression", "medication adherence", "lab worsening", "symptom change", "care plan", "imaging comparison"))
        notes.append(
            {
                "note_id": f"NOTE-{patient_id}-{index:03d}",
                "date": (date(2026, 6, 24) - timedelta(days=index * 5)).isoformat(),
                "author": rng.choice(CLINICIANS),
                "note_type": rng.choice(("Progress Note", "Consult", "Radiology Summary", "Care Plan")),
                "text": f"Longitudinal {topic} evidence for {patient_id}. This note links symptoms, imaging, structured labs, and clinician plan.",
                "vector_chunk_id": f"VEC-{patient_id}-{index:03d}",
                "keywords": [topic, "longitudinal", "multimodal"],
            }
        )
    return notes


def _comparators(bundle_index: int, count: int, rng: random.Random) -> list[dict[str, Any]]:
    """Create surrounding cohort rows for population-aware answers."""

    rows = []
    for index in range(1, count + 1):
        rows.append(
            {
                "patient_id": f"PT-C{bundle_index:02d}-{index:04d}",
                "age": rng.randint(18, 90),
                "risk_level": rng.choices(("high", "needs_review", "stable"), weights=(16, 29, 55))[0],
                "primary_diagnosis": rng.choice(DIAGNOSES),
                "latest_confidence": round(rng.uniform(0.67, 0.99), 2),
                "open_tasks": rng.randint(0, 5),
                "evidence_count": rng.randint(8, 72),
            }
        )
    return rows


def _plotly_specs(patient_id: str, labs: list[dict[str, Any]], images: list[dict[str, Any]], comparators: list[dict[str, Any]]) -> dict[str, Any]:
    """Build Plotly-ready chart specifications."""

    recent = [row for row in labs if row["metric"] in {"tumor_size_cm", "cea_ng_ml", "egfr"}]
    modality_counts: dict[str, int] = {}
    for image in images:
        modality_counts[image["modality"]] = modality_counts.get(image["modality"], 0) + 1
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
                    "x": [row["date"] for row in recent if row["metric"] == metric],
                    "y": [row["value"] for row in recent if row["metric"] == metric],
                }
                for metric in ("tumor_size_cm", "cea_ng_ml", "egfr")
            ],
            "layout": {"title": f"{patient_id} longitudinal metric trends"},
        },
        "image_modalities": {
            "data": [{"type": "bar", "x": list(modality_counts), "y": list(modality_counts.values())}],
            "layout": {"title": "Image evidence by modality"},
        },
        "comparator_risk": {
            "data": [{"type": "pie", "labels": list(risk_counts), "values": list(risk_counts.values())}],
            "layout": {"title": "Comparator cohort risk mix"},
        },
    }


def _write_charts(bundle_dir: Path, patient_id: str, labs: list[dict[str, Any]], comparators: list[dict[str, Any]]) -> list[str]:
    """Render Matplotlib visualizations for the bundle."""

    chart_dir = bundle_dir / "charts"
    chart_dir.mkdir(exist_ok=True)
    chart_paths = []
    trend_path = chart_dir / "metric_trends.png"
    plt.figure(figsize=(10, 5))
    for metric in ("tumor_size_cm", "cea_ng_ml", "egfr"):
        rows = [row for row in labs if row["metric"] == metric][::10]
        plt.plot([row["date"] for row in rows], [row["value"] for row in rows], label=metric)
    plt.xticks(rotation=35, ha="right")
    plt.title(f"{patient_id} multimodal trend summary")
    plt.legend()
    plt.tight_layout()
    plt.savefig(trend_path)
    plt.close()
    chart_paths.append(str(trend_path))

    risk_path = chart_dir / "comparator_risk.png"
    counts = {risk: len([row for row in comparators if row["risk_level"] == risk]) for risk in ("high", "needs_review", "stable")}
    plt.figure(figsize=(6, 4))
    plt.bar(list(counts), list(counts.values()), color=("#dc2626", "#f59e0b", "#16a34a"))
    plt.title("Comparator cohort risk")
    plt.tight_layout()
    plt.savefig(risk_path)
    plt.close()
    chart_paths.append(str(risk_path))
    return chart_paths


def build_bundle(bundle_index: int, output: Path, rng: random.Random, days: int, comparators: int) -> dict[str, Any]:
    """Build one complete multimodal Q&A bundle."""

    patient_id = f"PT-M{bundle_index:04d}"
    bundle_dir = output / patient_id
    bundle_dir.mkdir(parents=True, exist_ok=True)
    patient = _patient(patient_id, rng)
    labs = _labs(patient_id, rng, days)
    images = _images(patient_id, rng, 18)
    notes = _notes(patient_id, rng, 72)
    timeline = _timeline(patient_id, rng, 160)
    comparator_rows = _comparators(bundle_index, comparators, rng)
    plotly = _plotly_specs(patient_id, labs, images, comparator_rows)
    chart_paths = _write_charts(bundle_dir, patient_id, labs, comparator_rows)
    citations = [
        {"citation_id": note["vector_chunk_id"], "source_id": note["note_id"], "kind": "text", "excerpt": note["text"]}
        for note in notes[:20]
    ] + [
        {"citation_id": image["image_id"], "source_id": image["gcs_uri"], "kind": "image", "excerpt": image["description"]}
        for image in images[:8]
    ]
    prompts = [
        {
            "question": "What changed across the last 90 days and which evidence supports it?",
            "expected_sources": ["metric_trends", "clinical_notes", "image_modalities"],
            "expected_output": "Narrative answer with cited trend, note, and image evidence.",
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
            "notes": len(notes),
            "timeline": len(timeline),
            "comparators": len(comparator_rows),
            "citations": len(citations),
        },
        "labs": labs,
        "images": images,
        "notes": notes,
        "timeline": timeline,
        "comparator_cohort": comparator_rows,
        "citations": citations,
        "plotly": plotly,
        "matplotlib_pngs": chart_paths,
        "qa_prompts": prompts,
        "backend_contract": {"route": "/api/runs/qa", "requiredBody": {"patientId": patient_id, "question": "...", "source_types": ["text", "image", "lab"]}},
    }
    (bundle_dir / "bundle.json").write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    (bundle_dir / "qa_prompts.json").write_text(json.dumps(prompts, indent=2), encoding="utf-8")
    (bundle_dir / "plotly_specs.json").write_text(json.dumps(plotly, indent=2), encoding="utf-8")
    return {"patient_id": patient_id, "path": str(bundle_dir / "bundle.json"), "row_counts": bundle["row_counts"]}


def generate(output: Path, bundle_count: int, days: int, comparators: int, seed: int) -> dict[str, Any]:
    """Generate all multimodal bundles."""

    rng = random.Random(seed)
    output.mkdir(parents=True, exist_ok=True)
    bundles = [build_bundle(index, output, rng, days, comparators) for index in range(1, bundle_count + 1)]
    manifest = {
        "module": "multimodal_patient_qa",
        "bundle_count": len(bundles),
        "bundles": bundles,
        "frontend_contract": {
            "views": ["Patient profile", "Multimodal patient Q&A", "Evidence citations", "Chart builder"],
            "needs": ["dense patient detail", "source viewer", "multiple Plotly panels", "citation table"],
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Generate multimodal patient Q&A showcase bundles.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--bundle-count", type=int, default=12)
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--comparators", type=int, default=420)
    parser.add_argument("--seed", type=int, default=240624)
    args = parser.parse_args()
    manifest = generate(args.output, args.bundle_count, args.days, args.comparators, args.seed)
    print(json.dumps({"output": str(args.output), "bundle_count": manifest["bundle_count"]}, indent=2))


if __name__ == "__main__":
    main()
