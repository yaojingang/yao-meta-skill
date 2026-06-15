#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "render_evidence_consistency.py"
TMP = ROOT / "tests" / "tmp_evidence_consistency"
REPORT_FILES = [
    "reports/benchmark_reproducibility.json",
    "reports/skill-overview.json",
    "reports/skill-overview.html",
    "reports/skill-interpretation.json",
    "reports/skill-interpretation.html",
    "reports/adoption_drift_report.json",
    "reports/world_class_evidence_ledger.json",
    "reports/world_class_evidence_plan.json",
    "reports/world_class_evidence_intake.json",
    "reports/world_class_submission_review.json",
    "reports/world_class_operator_runbook.json",
    "reports/skill_os2_coverage.json",
    "reports/review-studio.json",
    "reports/package_verification.json",
    "reports/install_simulation.json",
    "reports/security_trust_report.json",
    "reports/context_budget.json",
    "reports/world_class_claim_guard.json",
    "reports/skill-os-2-review.md",
    "scripts/ci_test.py",
]


def run(cmd: list[str], *, check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=check)


def copy_reports(dst: Path) -> None:
    for relative in REPORT_FILES:
        source = ROOT / relative
        target = dst / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def refresh_embedded_reports() -> None:
    script_names = [
        "render_benchmark_reproducibility.py",
        "render_skill_os2_coverage.py",
        "render_world_class_evidence_plan.py",
        "render_world_class_evidence_ledger.py",
        "render_world_class_evidence_intake.py",
        "render_world_class_submission_review.py",
        "render_world_class_operator_runbook.py",
        "render_world_class_claim_guard.py",
        "render_skill_overview.py",
        "render_skill_interpretation.py",
    ]
    for script_name in script_names:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script_name), str(ROOT)],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )


def assert_world_class_roadmap_matches_ledger() -> None:
    ledger = json.loads((ROOT / "reports" / "world_class_evidence_ledger.json").read_text(encoding="utf-8"))
    summary = ledger["summary"]
    pending_count = int(summary["pending_count"])
    external_pending_count = int(summary["external_pending_count"])
    human_pending_count = int(summary["human_pending_count"])
    expected_total = f"{pending_count} 项待补证据"
    expected_breakdown = f"外部 {external_pending_count} 项、人工 {human_pending_count} 项"

    for report_name in ["skill-overview", "skill-interpretation"]:
        report_path = ROOT / "reports" / f"{report_name}.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        serialized = json.dumps(report, ensure_ascii=False)
        assert "继续补齐剩余 2 项外部/人工证据" not in serialized, report_name
        assert report["world_class_readiness"]["pending_count"] == pending_count, report["world_class_readiness"]
        assert report["world_class_readiness"]["external_pending_count"] == external_pending_count, report[
            "world_class_readiness"
        ]
        assert report["world_class_readiness"]["human_pending_count"] == human_pending_count, report[
            "world_class_readiness"
        ]
        actions = "\n".join(report["iteration_roadmap"]["items"][0]["actions"])
        if pending_count > 2:
            assert expected_total in actions, actions
            assert expected_breakdown in actions, actions


def assert_release_evidence_instructions_cover_first_class_reports() -> None:
    agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    source_refresh_header = "After source changes that affect scripts"
    clean_lock_header = "For final release evidence"
    assert source_refresh_header in agents_text, agents_text
    assert clean_lock_header in agents_text, agents_text

    source_refresh = agents_text.split(source_refresh_header, 1)[1].split(clean_lock_header, 1)[0]
    clean_lock = agents_text.split(clean_lock_header, 1)[1].split("If `reports/benchmark_reproducibility.json`", 1)[0]
    for block in [source_refresh, clean_lock]:
        assert "python3 scripts/render_skill_interpretation.py ." in block, block
        assert "python3 scripts/render_evidence_consistency.py . --generated-at \"$GENERATED_AT\"" in block, block


def main() -> None:
    shutil.rmtree(TMP, ignore_errors=True)
    TMP.mkdir(parents=True, exist_ok=True)
    refresh_embedded_reports()
    assert_world_class_roadmap_matches_ledger()
    assert_release_evidence_instructions_cover_first_class_reports()
    output_json = TMP / "evidence_consistency.json"
    output_md = TMP / "evidence_consistency.md"
    proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(ROOT),
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
            "--generated-at",
            "2026-06-15",
        ],
        check=True,
    )
    payload = json.loads(proc.stdout)
    assert payload["schema_version"] == "1.0", payload
    assert payload["ok"] is True, payload
    assert payload["summary"]["decision"] == "consistent", payload
    assert payload["summary"]["fail_count"] == 0, payload
    assert payload["summary"]["check_count"] >= 29, payload
    checks = {item["key"]: item for item in payload["checks"]}
    assert checks["overview-benchmark-summary"]["status"] == "pass", checks["overview-benchmark-summary"]
    assert checks["interpretation-adoption-summary"]["status"] == "pass", checks["interpretation-adoption-summary"]
    assert checks["coverage-world-class-boundary"]["status"] == "pass", checks["coverage-world-class-boundary"]
    assert checks["review-studio-no-overclaim"]["status"] == "pass", checks["review-studio-no-overclaim"]
    assert checks["claim-guard-package-runtime-surface"]["status"] == "pass", checks[
        "claim-guard-package-runtime-surface"
    ]
    assert checks["world-class-evidence-workflow-coverage"]["status"] == "pass", checks[
        "world-class-evidence-workflow-coverage"
    ]
    assert checks["skill-os-2-review-current-evidence"]["status"] == "pass", checks[
        "skill-os-2-review-current-evidence"
    ]
    markdown = output_md.read_text(encoding="utf-8")
    assert "Evidence Consistency" in markdown, markdown
    assert "decision: `consistent`" in markdown, markdown
    assert "does not create provider, human, native-client, or permission-enforcement evidence" in markdown, markdown

    drift_root = TMP / "drift-skill"
    copy_reports(drift_root)
    overview_path = drift_root / "reports" / "skill-overview.json"
    overview = json.loads(overview_path.read_text(encoding="utf-8"))
    overview["adoption_drift"]["summary"]["adoption_sample_count"] += 1
    overview_path.write_text(json.dumps(overview, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    drift_proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(drift_root),
            "--output-json",
            str(TMP / "drift.json"),
            "--output-md",
            str(TMP / "drift.md"),
            "--generated-at",
            "2026-06-15",
        ]
    )
    assert drift_proc.returncode == 2, drift_proc.stdout
    drift_payload = json.loads(drift_proc.stdout)
    drift_checks = {item["key"]: item for item in drift_payload["checks"]}
    assert drift_payload["ok"] is False, drift_payload
    assert drift_payload["summary"]["decision"] == "evidence-drift-detected", drift_payload
    assert drift_checks["overview-adoption-summary"]["status"] == "fail", drift_checks["overview-adoption-summary"]
    assert drift_checks["interpretation-adoption-summary"]["status"] == "pass", drift_checks["interpretation-adoption-summary"]

    claim_guard_drift_root = TMP / "claim-guard-drift-skill"
    copy_reports(claim_guard_drift_root)
    claim_guard_path = claim_guard_drift_root / "reports" / "world_class_claim_guard.json"
    claim_guard = json.loads(claim_guard_path.read_text(encoding="utf-8"))
    claim_guard["summary"]["package_claim_surface_count"] = 0
    claim_guard["scanned_surfaces"] = [
        item for item in claim_guard["scanned_surfaces"] if item.get("path") != "dist/manifest.json"
    ]
    claim_guard_path.write_text(json.dumps(claim_guard, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    claim_guard_drift_proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(claim_guard_drift_root),
            "--output-json",
            str(TMP / "claim_guard_drift.json"),
            "--output-md",
            str(TMP / "claim_guard_drift.md"),
            "--generated-at",
            "2026-06-15",
        ]
    )
    assert claim_guard_drift_proc.returncode == 2, claim_guard_drift_proc.stdout
    claim_guard_drift_payload = json.loads(claim_guard_drift_proc.stdout)
    claim_guard_drift_checks = {item["key"]: item for item in claim_guard_drift_payload["checks"]}
    assert claim_guard_drift_checks["claim-guard-package-runtime-surface"]["status"] == "fail", (
        claim_guard_drift_checks["claim-guard-package-runtime-surface"]
    )

    workflow_drift_root = TMP / "workflow-drift-skill"
    copy_reports(workflow_drift_root)
    studio_path = workflow_drift_root / "reports" / "review-studio.json"
    studio = json.loads(studio_path.read_text(encoding="utf-8"))
    for action in studio["review_actions"]:
        if action.get("gate_key") == "world-class-evidence":
            action["evidence_steps"] = [
                item for item in action["evidence_steps"] if item.get("key") != "native-client-telemetry"
            ]
    studio_path.write_text(json.dumps(studio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    workflow_drift_proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(workflow_drift_root),
            "--output-json",
            str(TMP / "workflow_drift.json"),
            "--output-md",
            str(TMP / "workflow_drift.md"),
            "--generated-at",
            "2026-06-15",
        ]
    )
    assert workflow_drift_proc.returncode == 2, workflow_drift_proc.stdout
    workflow_drift_payload = json.loads(workflow_drift_proc.stdout)
    workflow_drift_checks = {item["key"]: item for item in workflow_drift_payload["checks"]}
    assert workflow_drift_checks["world-class-evidence-workflow-coverage"]["status"] == "fail", (
        workflow_drift_checks["world-class-evidence-workflow-coverage"]
    )
    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
