#!/usr/bin/env python3
"""Data preparation helpers for the compact review viewer."""

import json
import re
from pathlib import Path

from render_intent_confidence import render_intent_confidence
from render_intent_dialogue import render_intent_dialogue
from render_iteration_directions import render_iteration_directions
from render_artifact_design_profile import render_artifact_design_profile
from render_output_risk_profile import render_output_risk_profile
from render_prompt_quality_profile import render_prompt_quality_profile
from render_reference_scan import render_reference_scan
from render_reference_synthesis import render_reference_synthesis
from render_skill_overview import render_skill_overview


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_review_viewer.py to assemble Review Viewer data before HTML rendering."


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_feedback_summary(skill_dir: Path) -> dict:
    payload = load_json(skill_dir / "reports" / "feedback-log.json")
    return payload if isinstance(payload, dict) else {}


def load_baseline_summary(skill_dir: Path) -> dict:
    payload = load_json(skill_dir / "reports" / "baseline-compare.json")
    return payload if isinstance(payload, dict) else {}


def load_specific_compare(skill_dir: Path) -> dict:
    candidates = [
        skill_dir / "reports" / "description_optimization.json",
        skill_dir.parent / "optimization" / "reports" / "description_optimization.json",
    ]
    for path in candidates:
        payload = load_json(path)
        if isinstance(payload, dict) and payload:
            return payload
    return {}


def load_specific_promotion(skill_dir: Path) -> dict:
    payload = load_json(skill_dir / "reports" / "promotion_decisions.json")
    return payload if isinstance(payload, dict) else {}


def load_benchmark_summary(skill_dir: Path) -> dict:
    payload = load_json(skill_dir / "reports" / "github-benchmark-scan.json")
    return payload if isinstance(payload, dict) else {}


def load_reference_synthesis_summary(skill_dir: Path) -> dict:
    payload = load_json(skill_dir / "reports" / "reference-synthesis.json")
    return payload if isinstance(payload, dict) else {}


def load_output_risk_summary(skill_dir: Path) -> dict:
    payload = load_json(skill_dir / "reports" / "output-risk-profile.json")
    return payload if isinstance(payload, dict) else {}


def load_artifact_design_summary(skill_dir: Path) -> dict:
    payload = load_json(skill_dir / "reports" / "artifact-design-profile.json")
    return payload if isinstance(payload, dict) else {}


def load_prompt_quality_summary(skill_dir: Path) -> dict:
    payload = load_json(skill_dir / "reports" / "prompt-quality-profile.json")
    return payload if isinstance(payload, dict) else {}


def ensure_report_inputs(skill_dir: Path) -> dict:
    overview_json = skill_dir / "reports" / "skill-overview.json"
    intent_confidence_json = skill_dir / "reports" / "intent-confidence.json"
    intent_json = skill_dir / "reports" / "intent-dialogue.json"
    reference_json = skill_dir / "reports" / "reference-scan.json"
    reference_synthesis_json = skill_dir / "reports" / "reference-synthesis.json"
    output_risk_json = skill_dir / "reports" / "output-risk-profile.json"
    artifact_design_json = skill_dir / "reports" / "artifact-design-profile.json"
    prompt_quality_json = skill_dir / "reports" / "prompt-quality-profile.json"
    directions_json = skill_dir / "reports" / "iteration-directions.json"

    overview_payload = load_json(overview_json) if overview_json.exists() else {}
    intent_confidence_payload = load_json(intent_confidence_json) if intent_confidence_json.exists() else {}
    intent_payload = load_json(intent_json) if intent_json.exists() else {}
    reference_payload = load_json(reference_json) if reference_json.exists() else {}
    reference_synthesis_payload = load_json(reference_synthesis_json) if reference_synthesis_json.exists() else {}
    output_risk_payload = load_json(output_risk_json) if output_risk_json.exists() else {}
    artifact_design_payload = load_json(artifact_design_json) if artifact_design_json.exists() else {}
    prompt_quality_payload = load_json(prompt_quality_json) if prompt_quality_json.exists() else {}
    directions_payload = load_json(directions_json) if directions_json.exists() else {}

    intent_confidence = intent_confidence_payload or render_intent_confidence(skill_dir)["summary"]
    intent = intent_payload or render_intent_dialogue(skill_dir)["summary"]
    reference = reference_payload or render_reference_scan(skill_dir, [])["summary"]
    reference_synthesis = reference_synthesis_payload or render_reference_synthesis(skill_dir)["summary"]
    output_risk = output_risk_payload or render_output_risk_profile(skill_dir)["summary"]
    artifact_design = artifact_design_payload or render_artifact_design_profile(skill_dir)["summary"]
    prompt_quality = prompt_quality_payload or render_prompt_quality_profile(skill_dir)["summary"]
    iteration_payload = directions_payload or render_iteration_directions(skill_dir)
    iteration = iteration_payload.get("summary", {})
    overview = overview_payload or render_skill_overview(skill_dir)["summary"]
    feedback = load_feedback_summary(skill_dir)
    baseline = load_baseline_summary(skill_dir)
    compare = load_specific_compare(skill_dir)
    promotion = load_specific_promotion(skill_dir)
    benchmark = load_benchmark_summary(skill_dir)
    reference_synthesis = load_reference_synthesis_summary(skill_dir)
    output_risk = load_output_risk_summary(skill_dir) or output_risk
    artifact_design = load_artifact_design_summary(skill_dir) or artifact_design
    prompt_quality = load_prompt_quality_summary(skill_dir) or prompt_quality
    return {
        "overview": overview,
        "intent_confidence": intent_confidence,
        "intent": intent,
        "reference": reference,
        "iteration": iteration_payload,
        "feedback": feedback,
        "baseline": baseline,
        "compare": compare,
        "promotion": promotion,
        "benchmark": benchmark,
        "reference_synthesis": reference_synthesis,
        "output_risk": output_risk,
        "artifact_design": artifact_design,
        "prompt_quality": prompt_quality,
    }

def architecture_steps(overview: dict) -> list[dict]:
    logic = overview.get("logic_steps", [])[:3]
    usage = overview.get("usage_steps", [])[:2]
    return [
        {"label": "Inputs", "detail": "workflow, prompt, transcript, docs, or notes"},
        {"label": "Boundary", "detail": overview.get("description", "Define the recurring job and exclusions.")},
        {"label": "Logic", "detail": "; ".join(logic) if logic else "Understand, execute, and validate."},
        {"label": "Usage", "detail": "; ".join(usage) if usage else "Load the skill and follow the workflow."},
        {"label": "Next", "detail": "Review the top iteration directions before growing the package."},
    ]


def compare_rows(compare: dict) -> list[dict]:
    if not compare:
        return []
    rows = []
    items = [
        ("Baseline", compare.get("baseline", {})),
        ("Current", compare.get("current_candidate", {})),
        (compare.get("winner", {}).get("label", "Winner"), compare.get("winner", {})),
    ]
    for label, payload in items:
        if not payload:
            continue
        dev = payload.get("dev", {})
        holdout = payload.get("holdout", {})
        rows.append(
            {
                "label": label,
                "tokens": payload.get("estimated_tokens", 0),
                "dev_errors": dev.get("total_errors", 0),
                "holdout_errors": holdout.get("total_errors", 0),
                "strategy": payload.get("strategy", "existing"),
            }
        )
    return rows


def benchmark_cards(benchmark: dict) -> list[dict]:
    cards = []
    for repo in benchmark.get("repositories", [])[:3]:
        cards.append(
            {
                "name": repo.get("full_name", "Unknown repo"),
                "borrow": repo.get("borrow", [])[:2],
                "avoid": repo.get("avoid", [])[:1],
            }
        )
    return cards


def synthesis_cards(reference_synthesis: dict) -> list[dict]:
    cards = []
    for track in reference_synthesis.get("source_tracks", [])[:3]:
        cards.append(
            {
                "name": track.get("name", "Unknown track"),
                "borrow": [track.get("borrow", "")] if track.get("borrow") else [],
                "avoid": [track.get("avoid", "")] if track.get("avoid") else [],
            }
        )
    return cards


def split_sentences(text: str) -> list[str]:
    if not text:
        return []
    parts = [item.strip() for item in re.split(r"(?<=[.!?])\s+", " ".join(text.split())) if item.strip()]
    return parts


def metric_delta(current: int | float, baseline: int | float) -> str:
    delta = current - baseline
    if delta == 0:
        return "0"
    return f"{delta:+}"


def variant_diff_cards(compare: dict) -> list[dict]:
    baseline = compare.get("baseline", {})
    current = compare.get("current_candidate", {})
    winner = compare.get("winner", {})
    variants = [
        ("Baseline", baseline),
        ("Current", current),
        (f"Winner — {winner.get('label', 'Winner')}", winner),
    ]
    baseline_sentences = split_sentences(baseline.get("description", ""))
    baseline_set = set(baseline_sentences)
    baseline_dev = baseline.get("dev", {}).get("total_errors", 0)
    baseline_holdout = baseline.get("holdout", {}).get("total_errors", 0)
    cards = []
    seen = set()
    for label, payload in variants:
        if not payload:
            continue
        unique_key = (payload.get("description"), payload.get("strategy"), label)
        if unique_key in seen:
            continue
        seen.add(unique_key)
        description = payload.get("description", "")
        sentences = split_sentences(description)
        sentence_set = set(sentences)
        added = [item for item in sentences if item not in baseline_set][:3]
        removed = [item for item in baseline_sentences if item not in sentence_set][:2]
        dev_errors = payload.get("dev", {}).get("total_errors", 0)
        holdout_errors = payload.get("holdout", {}).get("total_errors", 0)
        cards.append(
            {
                "label": label,
                "strategy": payload.get("strategy", "existing"),
                "description": description,
                "tokens": payload.get("estimated_tokens", 0),
                "dev_errors": dev_errors,
                "holdout_errors": holdout_errors,
                "token_delta": metric_delta(payload.get("estimated_tokens", 0), baseline.get("estimated_tokens", 0)),
                "dev_delta": metric_delta(dev_errors, baseline_dev),
                "holdout_delta": metric_delta(holdout_errors, baseline_holdout),
                "added": added if label != "Baseline" else baseline_sentences[:3],
                "removed": removed,
            }
        )
    return cards


def evidence_readiness(report: dict) -> dict:
    intent_confidence = report.get("intent_confidence", {})
    reference_synthesis = report.get("reference_synthesis", {})
    output_risk = report.get("output_risk", {})
    artifact_design = report.get("artifact_design", {})
    prompt_quality = report.get("prompt_quality", {})
    benchmark = report.get("benchmark", {})
    synthesis = reference_synthesis.get("synthesis", {}) if isinstance(reference_synthesis, dict) else {}
    pattern_gate = synthesis.get("pattern_gate", {}) if isinstance(synthesis, dict) else {}
    accepted_patterns = pattern_gate.get("accepted", []) if isinstance(pattern_gate, dict) else []
    conflicts = synthesis.get("conflicts", []) if isinstance(synthesis, dict) else []
    checks = [
        {
            "label": "Intent clarity",
            "status": "ready" if intent_confidence.get("gate_passed") else "needs review",
            "detail": f"{intent_confidence.get('score', 0)}/100 intent confidence.",
        },
        {
            "label": "Benchmark coverage",
            "status": "ready" if len(benchmark.get("repositories", [])) >= 2 else "needs evidence",
            "detail": f"{len(benchmark.get('repositories', []))} GitHub benchmark repositories attached.",
        },
        {
            "label": "Pattern gate",
            "status": "ready" if accepted_patterns else "needs review",
            "detail": pattern_gate.get("summary", "No pattern gate summary attached."),
        },
        {
            "label": "Conflict handling",
            "status": "ready" if not conflicts else "decision needed",
            "detail": "No material conflicts detected." if not conflicts else conflicts[0].get("summary", "Conflict detected."),
        },
        {
            "label": "Output risk profile",
            "status": "ready" if output_risk.get("risk_families") else "needs review",
            "detail": f"{len(output_risk.get('risk_families', []))} output risk families attached.",
        },
        {
            "label": "Artifact design profile",
            "status": "ready" if artifact_design.get("primary_artifact") else "needs review",
            "detail": artifact_design.get("primary_artifact", {}).get("direction", "No artifact design profile attached."),
        },
        {
            "label": "Prompt quality profile",
            "status": "ready" if prompt_quality.get("quality_matrix") else "needs review",
            "detail": f"{prompt_quality.get('overall_quality_score', 0)}/100 prompt-facing quality score.",
        },
    ]
    ready_count = sum(1 for item in checks if item["status"] == "ready")
    return {
        "score": int(ready_count / len(checks) * 100),
        "checks": checks,
        "reviewer_note": "Use this section to decide whether the package is ready to deepen or should stay in discovery.",
    }
