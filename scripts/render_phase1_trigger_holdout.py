#!/usr/bin/env python3
"""Render the locked phase-one trigger and context gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from resource_boundary_check import analyze_skill
from trigger_eval import evaluate, extract_description, load_semantic_config


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Renders frozen phase-one trigger, regression, context, and metadata evidence."


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_report(skill_dir: Path, generated_at: str) -> dict[str, Any]:
    holdout_path = skill_dir / "evals" / "blind_holdout" / "trigger_cases_v2.json"
    lock_path = skill_dir / "evals" / "blind_holdout" / "trigger_cases_v2.lock.json"
    holdout = load_json(holdout_path)
    lock = load_json(lock_path)
    observed_hash = hashlib.sha256(holdout_path.read_bytes()).hexdigest()
    lock_valid = lock.get("sha256") == observed_hash and lock.get("case_count") == 30
    description = extract_description((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    config = load_semantic_config(skill_dir / "evals" / "semantic_config.json")
    holdout_report = evaluate(description, holdout, float(holdout["recommended_threshold"]), config)

    existing_false_positives = 0
    existing_false_negatives = 0
    existing_case_count = 0
    for suite in ("train", "dev", "holdout"):
        cases = load_json(skill_dir / "evals" / suite / "trigger_cases.json")
        result = evaluate(description, cases, float(cases["recommended_threshold"]), config)
        existing_false_positives += int(result["false_positives"])
        existing_false_negatives += int(result["false_negatives"])
        existing_case_count += sum(len(result["results"][bucket]) for bucket in result["results"])

    hard_negative_false_positives = sum(
        1 for item in holdout_report["results"]["should_not_trigger"] if item["predicted_trigger"]
    )
    context = analyze_skill(skill_dir)
    stats = context.get("stats", {})
    manifest = load_json(skill_dir / "manifest.json")
    thresholds = {
        "precision_min": 0.95,
        "recall_min": 0.90,
        "hard_negative_false_positive_max": 0,
        "existing_suite_case_count": 66,
        "existing_suite_regression_max": 0,
        "skill_body_tokens_max": 780,
        "initial_load_tokens_exclusive_max": 950,
    }
    checks = {
        "holdout_lock": lock_valid,
        "precision": float(holdout_report["precision"] or 0) >= thresholds["precision_min"],
        "recall": float(holdout_report["recall"] or 0) >= thresholds["recall_min"],
        "hard_negative_false_positives": hard_negative_false_positives == 0,
        "existing_suite": existing_case_count == 66 and existing_false_positives == 0 and existing_false_negatives == 0,
        "skill_body_tokens": int(stats.get("skill_body_tokens", 10**9)) <= 780,
        "initial_load_tokens": int(stats.get("estimated_initial_load_tokens", 10**9)) < 950,
        "release_metadata": (
            manifest.get("version") == "2.1.1"
            and manifest.get("updated_at") == "2026-11-09"
            and manifest.get("review_due") == "2026-11-15"
        ),
    }
    return {
        "schema_version": "1.0",
        "ok": all(checks.values()),
        "generated_at": generated_at,
        "summary": {
            "precision": holdout_report["precision"],
            "recall": holdout_report["recall"],
            "false_positives": holdout_report["false_positives"],
            "false_negatives": holdout_report["false_negatives"],
            "hard_negative_false_positives": hard_negative_false_positives,
            "existing_suite_case_count": existing_case_count,
            "existing_suite_false_positives": existing_false_positives,
            "existing_suite_false_negatives": existing_false_negatives,
            "skill_body_tokens": stats.get("skill_body_tokens"),
            "initial_load_tokens": stats.get("estimated_initial_load_tokens"),
            "decision": "pass" if all(checks.values()) else "blocked",
        },
        "thresholds": thresholds,
        "checks": checks,
        "frozen_holdout": {
            "path": holdout_path.relative_to(skill_dir).as_posix(),
            "sha256": observed_hash,
            "frozen_at": holdout.get("frozen_at"),
            "case_count": sum(len(holdout.get(bucket, [])) for bucket in ("should_trigger", "should_not_trigger", "near_neighbor")),
        },
        "misfires": holdout_report["misfires"],
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Phase 1 Trigger Holdout",
        "",
        f"- decision: `{summary['decision']}`",
        f"- frozen precision: `{summary['precision']}`",
        f"- frozen recall: `{summary['recall']}`",
        f"- hard-negative false positives: `{summary['hard_negative_false_positives']}`",
        f"- existing suite: `{summary['existing_suite_case_count']}` cases, `{summary['existing_suite_false_positives']}` FP, `{summary['existing_suite_false_negatives']}` FN",
        f"- context: SKILL `{summary['skill_body_tokens']}` tokens; initial `{summary['initial_load_tokens']}` tokens",
        f"- holdout SHA-256: `{report['frozen_holdout']['sha256']}`",
        "",
        "Embedding and cross-encoder challengers remain scheduled for Phase 2.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the frozen phase-one trigger and context gate.")
    parser.add_argument("skill_dir", help="Explicit Skill directory to evaluate")
    parser.add_argument("--output-json", default="reports/phase1_trigger_holdout.json")
    parser.add_argument("--output-md", default="reports/phase1_trigger_holdout.md")
    parser.add_argument("--generated-at", default="2026-08-12")
    args = parser.parse_args()
    skill_dir = Path(args.skill_dir).resolve()
    report = build_report(skill_dir, args.generated_at)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    if not output_json.is_absolute():
        output_json = skill_dir / output_json
    if not output_md.is_absolute():
        output_md = skill_dir / output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["ok"] else 2)


if __name__ == "__main__":
    main()
