#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "build_skill_atlas.py"


def write_skill(
    root: Path,
    name: str,
    description: str,
    manifest: dict,
    shared_reference: bool = False,
) -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"""---
name: {name}
description: {description}
---

# {name}

## Workflow

1. Understand the request.
2. Produce the requested artifact.
3. Review the output.
""",
        encoding="utf-8",
    )
    (skill_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if shared_reference:
        references = skill_dir / "references"
        references.mkdir(parents=True, exist_ok=True)
        (references / "release-method.md").write_text("# Release Method\n", encoding="utf-8")
    return skill_dir


def write_adoption_report(skill_dir: Path, risk_band: str = "medium") -> None:
    reports = skill_dir / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "adoption_drift_report.json").write_text(
        json.dumps(
            {
                "ok": True,
                "summary": {
                    "event_count": 4,
                    "adoption_sample_count": 3,
                    "activation_count": 2,
                    "accepted_count": 1,
                    "edited_count": 0,
                    "rejected_count": 1,
                    "missed_count": 1,
                    "failed_count": 1,
                    "adoption_rate": 33.3,
                    "missed_trigger_count": 1,
                    "wrong_trigger_count": 0,
                    "bad_output_count": 1,
                    "script_error_count": 1,
                    "missing_resource_count": 0,
                    "review_overdue_count": 0,
                    "risk_band": risk_band,
                },
                "next_iteration_candidates": [
                    {
                        "signal": "bad output",
                        "recommendation": "Convert the failed output shape into an Output Eval assertion.",
                    }
                ],
                "failures": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_skill_atlas"
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True, exist_ok=True)

    alpha = write_skill(
        tmp_root,
        "alpha-release-skill",
        "Use when turning release notes and changelog snippets into a reusable release brief for teams.",
        {
            "name": "alpha-release-skill",
            "owner": "Release Team",
            "maturity_tier": "production",
            "review_cadence": "monthly",
            "updated_at": "2025-01-01",
            "target_platforms": ["openai", "generic"],
        },
        shared_reference=True,
    )
    beta = write_skill(
        tmp_root,
        "beta-release-skill",
        "Use when turning changelog notes and release snippets into reusable release briefs for team review.",
        {
            "name": "beta-release-skill",
            "maturity_tier": "production",
            "updated_at": "2026-06-01",
            "target_platforms": ["openai"],
        },
        shared_reference=True,
    )
    write_adoption_report(beta, risk_band="high")
    write_skill(
        tmp_root,
        "gamma-doc-skill",
        "Use when cleaning messy documentation notes into a concise internal knowledge-base article.",
        {
            "name": "gamma-doc-skill",
            "owner": "Docs Team",
            "maturity_tier": "scaffold",
            "review_cadence": "quarterly",
            "updated_at": "2026-05-01",
            "target_platforms": ["generic"],
        },
    )
    evals = tmp_root / "evals"
    evals.mkdir()
    (evals / "failure-cases.md").write_text(
        "- no_route: repeated pricing approval prompts are missed by the current library.\n",
        encoding="utf-8",
    )
    policy_dir = tmp_root / "skill_atlas"
    policy_dir.mkdir()
    (policy_dir / "policy.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "scope_rules": [
                    {
                        "path_prefix": "beta-release-skill",
                        "scope": "example",
                        "actionable": False,
                        "reason": "fixture used to verify scoped portfolio warnings",
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    for private_root in [
        tmp_root / ".yao" / "backups",
        alpha / ".yao" / "runs" / "candidate" / "source",
        tmp_root / ".yao" / "releases" / "candidate",
    ]:
        write_skill(private_root, alpha.name, "Private validation copy.", {"name": alpha.name})

    output_dir = tmp_root / "atlas"
    report_html = tmp_root / "skill_atlas.html"
    report_json = tmp_root / "skill_atlas.json"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--workspace-root",
            str(tmp_root),
            "--output-dir",
            str(output_dir),
            "--report-html",
            str(report_html),
            "--report-json",
            str(report_json),
            "--today",
            "2026-06-13",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    payload = json.loads(proc.stdout)
    summary = payload["summary"]
    assert summary["skill_count"] == 3, summary
    assert summary["actionable_skill_count"] == 2, summary
    assert summary["route_collision_count"] >= 1, summary
    assert summary["actionable_route_collision_count"] <= summary["route_collision_count"], summary
    assert summary["owner_gap_count"] >= 1, summary
    assert summary["stale_count"] >= 1, summary
    assert summary["shared_resource_count"] >= 1, summary
    assert summary["no_route_opportunity_count"] >= 2, summary
    assert summary["drift_signal_count"] == 2, summary
    assert summary["actionable_drift_signal_count"] == 1, summary
    assert summary["telemetry_report_count"] == 1, summary
    assert (output_dir / "catalog.json").exists(), output_dir
    assert (output_dir / "route_overlap_matrix.csv").exists(), output_dir
    assert (output_dir / "dependency_graph.json").exists(), output_dir
    assert (output_dir / "stale_skills.json").exists(), output_dir
    assert (output_dir / "owner_review_gaps.json").exists(), output_dir
    assert (output_dir / "drift_signals.json").exists(), output_dir
    no_route_path = output_dir / "no_route_opportunities.json"
    assert no_route_path.exists(), output_dir
    html = report_html.read_text(encoding="utf-8")
    assert "Skill Atlas" in html, html[:1000]
    assert "Route Collisions" in html, html[:3000]
    assert "Actionable Issues" in html, html[:3000]
    assert "Drift Signals" in html, html[:3000]
    assert "No-Route Opportunities" in html, html[:3000]
    assert "Missed-trigger telemetry" in html, html
    catalog = json.loads((output_dir / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["summary"]["skill_count"] == 3, catalog
    assert all(".yao" not in Path(item["path"]).parts for item in catalog["skills"]), catalog
    alpha_catalog = next(item for item in catalog["skills"] if item["name"] == alpha.name)
    assert alpha_catalog["telemetry"]["risk_band"] == "missing", alpha_catalog
    drift = json.loads((output_dir / "drift_signals.json").read_text(encoding="utf-8"))
    assert any(item["name"] == alpha.name and item["signal_types"] == ["no telemetry"] for item in drift), drift
    assert any(item["name"] == beta.name and "bad output" in item["signal_types"] and not item["actionable"] for item in drift), drift
    no_route = json.loads(no_route_path.read_text(encoding="utf-8"))
    assert {item["source_type"] for item in no_route} >= {"failure-case", "telemetry"}, no_route
    telemetry_opportunity = next(item for item in no_route if item["source_type"] == "telemetry")
    assert telemetry_opportunity["skill"] == beta.name, telemetry_opportunity
    assert telemetry_opportunity["signal"] == "missed trigger", telemetry_opportunity
    assert telemetry_opportunity["missed_trigger_count"] == 1, telemetry_opportunity
    assert telemetry_opportunity["actionable"] is False, telemetry_opportunity
    assert "metadata-only telemetry" in telemetry_opportunity["privacy_contract"], telemetry_opportunity
    assert "raw prompt" in telemetry_opportunity["privacy_contract"], telemetry_opportunity
    assert payload["scope_policy"]["present"], payload["scope_policy"]

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
