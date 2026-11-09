#!/usr/bin/env python3
"""Frozen phase-one trigger boundary, context, and release metadata gates."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from resource_boundary_check import analyze_skill  # noqa: E402
from render_phase1_trigger_holdout import build_report  # noqa: E402
from trigger_eval import evaluate, extract_description, load_semantic_config  # noqa: E402


def main() -> None:
    holdout_path = ROOT / "evals" / "blind_holdout" / "trigger_cases_v2.json"
    lock_path = ROOT / "evals" / "blind_holdout" / "trigger_cases_v2.lock.json"
    holdout = json.loads(holdout_path.read_text(encoding="utf-8"))
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    assert holdout["frozen_at"] == "2026-08-12", holdout
    assert holdout["status"] == "frozen", holdout
    assert len(holdout["should_trigger"]) == 12, holdout
    assert len(holdout["should_not_trigger"]) == 12, holdout
    assert len(holdout["near_neighbor"]) == 6, holdout
    observed_hash = hashlib.sha256(holdout_path.read_bytes()).hexdigest()
    assert lock == {
        "schema_version": "1.0",
        "frozen_file": "evals/blind_holdout/trigger_cases_v2.json",
        "sha256": observed_hash,
        "case_count": 30,
        "frozen_at": "2026-08-12",
    }, lock

    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    description = extract_description(skill_text)
    config = load_semantic_config(ROOT / "evals" / "semantic_config.json")
    report = evaluate(description, holdout, holdout["recommended_threshold"], config)
    hard_negative_false_positives = sum(
        1 for item in report["results"]["should_not_trigger"] if item["predicted_trigger"]
    )
    assert report["precision"] >= 0.95, report
    assert report["recall"] >= 0.90, report
    assert hard_negative_false_positives == 0, report

    suite = subprocess.run(
        [sys.executable, "scripts/run_eval_suite.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    suite_payload = json.loads(suite.stdout)
    assert suite.returncode == 0, suite_payload
    assert suite_payload["summary"]["total_cases"] == 66, suite_payload
    assert suite_payload["summary"]["false_positives"] == 0, suite_payload
    assert suite_payload["summary"]["false_negatives"] == 0, suite_payload

    route = subprocess.run(
        [sys.executable, "tests/verify_route_confusion.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert route.returncode == 0, route.stdout or route.stderr

    context = analyze_skill(ROOT)
    stats = context["stats"]
    assert context["ok"], context
    assert stats["skill_body_tokens"] <= 780, stats
    assert stats["estimated_initial_load_tokens"] < 950, stats

    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["version"] == "2.1.1", manifest
    assert manifest["updated_at"] == "2026-11-09", manifest
    assert manifest["review_due"] == "2026-11-15", manifest
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "2.1.1"
    migration = (ROOT / "docs" / "migration-1.2.0.md").read_text(encoding="utf-8")
    assert "embedding" in migration.lower() and "phase 2" in migration.lower(), migration
    rendered = build_report(ROOT, "2026-08-12")
    assert rendered["ok"], rendered
    assert rendered["summary"]["decision"] == "pass", rendered

    print(
        json.dumps(
            {
                "ok": True,
                "frozen_holdout": {
                    "precision": report["precision"],
                    "recall": report["recall"],
                    "hard_negative_false_positives": hard_negative_false_positives,
                },
                "existing_suite_cases": 66,
                "skill_body_tokens": stats["skill_body_tokens"],
                "initial_load_tokens": stats["estimated_initial_load_tokens"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
