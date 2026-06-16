#!/usr/bin/env python3
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from evidence_consistency_release import CLEAN_LOCK_REPORT_COMMANDS, SOURCE_REFRESH_REPORT_COMMANDS

SCRIPT = ROOT / "scripts" / "render_evidence_consistency.py"
TMP = ROOT / "tests" / "tmp_evidence_consistency"
REPORT_FILES = [
    "AGENTS.md",
    "reports/benchmark_reproducibility.json",
    "reports/skill-overview.json",
    "reports/skill-overview.html",
    "reports/skill-interpretation.json",
    "reports/skill-interpretation.html",
    "reports/adoption_drift_report.json",
    "reports/world_class_evidence_ledger.json",
    "reports/world_class_evidence_plan.json",
    "reports/world_class_evidence_intake.json",
    "reports/world_class_evidence_preflight.json",
    "reports/world_class_evidence_preflight.html",
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
    "skill-ir/examples/yao-meta-skill.json",
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
        "render_context_reports.py",
        "render_skill_os2_coverage.py",
        "render_world_class_evidence_plan.py",
        "render_world_class_evidence_ledger.py",
        "render_world_class_evidence_intake.py",
        "render_world_class_preflight.py",
        "render_world_class_submission_review.py",
        "render_world_class_operator_runbook.py",
        "render_world_class_claim_guard.py",
        "render_benchmark_reproducibility.py",
        "render_skill_overview.py",
        "render_skill_interpretation.py",
        "render_review_viewer.py",
        "render_review_studio.py",
    ]
    for script_name in script_names:
        command = [sys.executable, str(ROOT / "scripts" / script_name)]
        if script_name != "render_context_reports.py":
            command.append(str(ROOT))
        subprocess.run(
            command,
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
    for command in SOURCE_REFRESH_REPORT_COMMANDS:
        assert command in source_refresh, command
    for command in CLEAN_LOCK_REPORT_COMMANDS:
        assert command in clean_lock, command


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
    assert payload["summary"]["check_count"] >= 31, payload
    checks = {item["key"]: item for item in payload["checks"]}
    assert checks["release-evidence-flow-covers-first-class-reports"]["status"] == "pass", checks[
        "release-evidence-flow-covers-first-class-reports"
    ]
    assert checks["review-studio-context-budget-mirror"]["status"] == "pass", checks[
        "review-studio-context-budget-mirror"
    ]
    assert checks["skill-ir-evidence-path-contract"]["status"] == "pass", checks[
        "skill-ir-evidence-path-contract"
    ]
    assert checks["skill-ir-evidence-path-contract"]["actual"]["review_studio_evidence_path"] == (
        "skill-ir/examples/yao-meta-skill.json"
    ), checks["skill-ir-evidence-path-contract"]
    assert checks["overview-benchmark-summary"]["status"] == "pass", checks["overview-benchmark-summary"]
    assert checks["interpretation-adoption-summary"]["status"] == "pass", checks["interpretation-adoption-summary"]
    assert checks["coverage-world-class-boundary"]["status"] == "pass", checks["coverage-world-class-boundary"]
    assert checks["preflight-world-class-boundary"]["status"] == "pass", checks["preflight-world-class-boundary"]
    assert checks["preflight-submission-kit-handoff"]["status"] == "pass", checks[
        "preflight-submission-kit-handoff"
    ]
    preflight_handoff = checks["preflight-submission-kit-handoff"]["actual"]
    assert preflight_handoff["artifact_role_source"] == "world-class-submission-kit", preflight_handoff
    assert preflight_handoff["artifact_role_counts_as_evidence"] is False, preflight_handoff
    assert preflight_handoff["submission_ref_role_present"] is True, preflight_handoff
    assert preflight_handoff["supporting_evidence_role_present"] is True, preflight_handoff
    assert preflight_handoff["submission_ref_copy_to_artifact_refs"] is True, preflight_handoff
    assert preflight_handoff["supporting_evidence_copy_to_artifact_refs"] is False, preflight_handoff
    assert checks["review-studio-preflight-artifact-role-handoff"]["status"] == "pass", checks[
        "review-studio-preflight-artifact-role-handoff"
    ]
    assert checks["world-class-phase-queue-consistency"]["status"] == "pass", checks[
        "world-class-phase-queue-consistency"
    ]
    phase_queue_actual = checks["world-class-phase-queue-consistency"]["actual"]
    assert phase_queue_actual["summary"]["phase_queue_count"] == 2, phase_queue_actual
    assert phase_queue_actual["summary"]["phase_queue_row_count"] >= 13, phase_queue_actual
    assert phase_queue_actual["summary"] == phase_queue_actual["operator_runbook_summary"], phase_queue_actual
    assert phase_queue_actual["top_level_phase_queue"] == phase_queue_actual[
        "operator_runbook_top_level_phase_queue"
    ], phase_queue_actual
    assert phase_queue_actual["phase_queue_counts_as_completion"] is False, phase_queue_actual
    assert set(phase_queue_actual["item_phase_queues"]) == {
        "provider-holdout",
        "human-adjudication",
        "native-permission-enforcement",
        "native-client-telemetry",
    }, phase_queue_actual
    assert phase_queue_actual["operator_runbook_phase_queues"] == phase_queue_actual["item_phase_queues"], (
        phase_queue_actual
    )
    assert phase_queue_actual["review_studio_phase_queues"] == phase_queue_actual["item_phase_queues"], (
        phase_queue_actual
    )
    role_handoff = checks["review-studio-preflight-artifact-role-handoff"]["actual"]
    assert role_handoff["provider-holdout"]["role_source"] == "world-class-submission-kit", role_handoff
    assert role_handoff["provider-holdout"]["submission_ref_total_count"] == 1, role_handoff
    assert role_handoff["provider-holdout"]["submission_ref_copy_to_artifact_refs"] is True, role_handoff
    assert role_handoff["provider-holdout"]["supporting_evidence_copy_to_artifact_refs"] is False, role_handoff
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

    skill_ir_drift_root = TMP / "skill-ir-drift-skill"
    copy_reports(skill_ir_drift_root)
    studio_path = skill_ir_drift_root / "reports" / "review-studio.json"
    studio = json.loads(studio_path.read_text(encoding="utf-8"))
    studio["evidence_paths"]["skill_ir"] = "reports/skill-ir.json"
    studio_path.write_text(json.dumps(studio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    skill_ir_drift_proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(skill_ir_drift_root),
            "--output-json",
            str(TMP / "skill_ir_drift.json"),
            "--output-md",
            str(TMP / "skill_ir_drift.md"),
            "--generated-at",
            "2026-06-15",
        ]
    )
    assert skill_ir_drift_proc.returncode == 2, skill_ir_drift_proc.stdout
    skill_ir_drift_payload = json.loads(skill_ir_drift_proc.stdout)
    skill_ir_drift_checks = {item["key"]: item for item in skill_ir_drift_payload["checks"]}
    assert skill_ir_drift_checks["skill-ir-evidence-path-contract"]["status"] == "fail", (
        skill_ir_drift_checks["skill-ir-evidence-path-contract"]
    )

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

    preflight_drift_root = TMP / "preflight-drift-skill"
    copy_reports(preflight_drift_root)
    preflight_path = preflight_drift_root / "reports" / "world_class_evidence_preflight.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["summary"]["credential_value_exposed"] = True
    preflight_path.write_text(json.dumps(preflight, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_drift_proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(preflight_drift_root),
            "--output-json",
            str(TMP / "preflight_drift.json"),
            "--output-md",
            str(TMP / "preflight_drift.md"),
            "--generated-at",
            "2026-06-15",
        ]
    )
    assert preflight_drift_proc.returncode == 2, preflight_drift_proc.stdout
    preflight_drift_payload = json.loads(preflight_drift_proc.stdout)
    preflight_drift_checks = {item["key"]: item for item in preflight_drift_payload["checks"]}
    assert preflight_drift_checks["preflight-world-class-boundary"]["status"] == "fail", (
        preflight_drift_checks["preflight-world-class-boundary"]
    )

    preflight_handoff_drift_root = TMP / "preflight-handoff-drift-skill"
    copy_reports(preflight_handoff_drift_root)
    preflight_handoff_path = preflight_handoff_drift_root / "reports" / "world_class_evidence_preflight.json"
    preflight_handoff = json.loads(preflight_handoff_path.read_text(encoding="utf-8"))
    preflight_handoff["submissions"]["drafts_count_as_evidence"] = True
    preflight_handoff["submissions"]["commands"].pop("prepare_submission", None)
    preflight_handoff_path.write_text(json.dumps(preflight_handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    preflight_handoff_drift_proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(preflight_handoff_drift_root),
            "--output-json",
            str(TMP / "preflight_handoff_drift.json"),
            "--output-md",
            str(TMP / "preflight_handoff_drift.md"),
            "--generated-at",
            "2026-06-15",
        ]
    )
    assert preflight_handoff_drift_proc.returncode == 2, preflight_handoff_drift_proc.stdout
    preflight_handoff_drift_payload = json.loads(preflight_handoff_drift_proc.stdout)
    preflight_handoff_drift_checks = {item["key"]: item for item in preflight_handoff_drift_payload["checks"]}
    assert preflight_handoff_drift_checks["preflight-submission-kit-handoff"]["status"] == "fail", (
        preflight_handoff_drift_checks["preflight-submission-kit-handoff"]
    )

    phase_queue_drift_root = TMP / "phase-queue-drift-skill"
    copy_reports(phase_queue_drift_root)
    phase_queue_path = phase_queue_drift_root / "reports" / "world_class_evidence_preflight.json"
    phase_queue_payload = json.loads(phase_queue_path.read_text(encoding="utf-8"))
    phase_queue_payload["summary"]["phase_queue_row_count"] = 1
    phase_queue_payload["phase_queue"][0]["counts_as_completion"] = True
    phase_queue_payload["items"][0]["phase_queue"][0]["row_count"] = 999
    phase_queue_path.write_text(json.dumps(phase_queue_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    operator_phase_queue_path = phase_queue_drift_root / "reports" / "world_class_operator_runbook.json"
    operator_phase_queue_payload = json.loads(operator_phase_queue_path.read_text(encoding="utf-8"))
    operator_phase_queue_payload["summary"]["phase_queue_count"] = 99
    operator_phase_queue_payload["phase_queue"][0]["row_count"] = 999
    operator_phase_queue_payload["items"][0]["phase_queue"][0]["row_count"] = 999
    operator_phase_queue_path.write_text(
        json.dumps(operator_phase_queue_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    phase_queue_drift_proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(phase_queue_drift_root),
            "--output-json",
            str(TMP / "phase_queue_drift.json"),
            "--output-md",
            str(TMP / "phase_queue_drift.md"),
            "--generated-at",
            "2026-06-15",
        ]
    )
    assert phase_queue_drift_proc.returncode == 2, phase_queue_drift_proc.stdout
    phase_queue_drift_payload = json.loads(phase_queue_drift_proc.stdout)
    phase_queue_drift_checks = {item["key"]: item for item in phase_queue_drift_payload["checks"]}
    assert phase_queue_drift_checks["world-class-phase-queue-consistency"]["status"] == "fail", (
        phase_queue_drift_checks["world-class-phase-queue-consistency"]
    )

    release_flow_drift_root = TMP / "release-flow-drift-skill"
    copy_reports(release_flow_drift_root)
    agents_path = release_flow_drift_root / "AGENTS.md"
    agents_text = agents_path.read_text(encoding="utf-8")
    agents_path.write_text(
        agents_text.replace("python3 scripts/render_skill_interpretation.py .\n", "", 1),
        encoding="utf-8",
    )
    release_flow_drift_proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(release_flow_drift_root),
            "--output-json",
            str(TMP / "release_flow_drift.json"),
            "--output-md",
            str(TMP / "release_flow_drift.md"),
            "--generated-at",
            "2026-06-15",
        ]
    )
    assert release_flow_drift_proc.returncode == 2, release_flow_drift_proc.stdout
    release_flow_drift_payload = json.loads(release_flow_drift_proc.stdout)
    release_flow_drift_checks = {item["key"]: item for item in release_flow_drift_payload["checks"]}
    assert release_flow_drift_checks["release-evidence-flow-covers-first-class-reports"]["status"] == "fail", (
        release_flow_drift_checks["release-evidence-flow-covers-first-class-reports"]
    )

    context_drift_root = TMP / "context-drift-skill"
    copy_reports(context_drift_root)
    context_path = context_drift_root / "reports" / "context_budget.json"
    context_payload = json.loads(context_path.read_text(encoding="utf-8"))
    context_payload["warnings"] = ["Deferred resource footprint is high: stale test warning."]
    context_payload["stats"]["deferred_resource_tokens"] = 1
    context_payload["stats"]["deferred_resource_governance"]["status"] = "pass"
    context_path.write_text(json.dumps(context_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    context_drift_proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(context_drift_root),
            "--output-json",
            str(TMP / "context_drift.json"),
            "--output-md",
            str(TMP / "context_drift.md"),
            "--generated-at",
            "2026-06-15",
        ]
    )
    assert context_drift_proc.returncode == 2, context_drift_proc.stdout
    context_drift_payload = json.loads(context_drift_proc.stdout)
    context_drift_checks = {item["key"]: item for item in context_drift_payload["checks"]}
    assert context_drift_checks["review-studio-context-budget-mirror"]["status"] == "fail", (
        context_drift_checks["review-studio-context-budget-mirror"]
    )

    benchmark_flow_drift_root = TMP / "benchmark-flow-drift-skill"
    copy_reports(benchmark_flow_drift_root)
    agents_path = benchmark_flow_drift_root / "AGENTS.md"
    agents_text = agents_path.read_text(encoding="utf-8")
    clean_lock_header = "For final release evidence"
    benchmark_command = 'python3 scripts/render_benchmark_reproducibility.py . --generated-at "$GENERATED_AT"\n'
    prefix, suffix = agents_text.split(clean_lock_header, 1)
    agents_path.write_text(
        prefix + clean_lock_header + suffix.replace(benchmark_command, "", 1),
        encoding="utf-8",
    )
    benchmark_flow_drift_proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(benchmark_flow_drift_root),
            "--output-json",
            str(TMP / "benchmark_flow_drift.json"),
            "--output-md",
            str(TMP / "benchmark_flow_drift.md"),
            "--generated-at",
            "2026-06-15",
        ]
    )
    assert benchmark_flow_drift_proc.returncode == 2, benchmark_flow_drift_proc.stdout
    benchmark_flow_drift_payload = json.loads(benchmark_flow_drift_proc.stdout)
    benchmark_flow_drift_checks = {item["key"]: item for item in benchmark_flow_drift_payload["checks"]}
    assert benchmark_flow_drift_checks["release-evidence-flow-covers-first-class-reports"]["status"] == "fail", (
        benchmark_flow_drift_checks["release-evidence-flow-covers-first-class-reports"]
    )

    stale_clean_lock_root = TMP / "stale-clean-lock-skill"
    copy_reports(stale_clean_lock_root)
    benchmark_path = stale_clean_lock_root / "reports" / "benchmark_reproducibility.json"
    benchmark = json.loads(benchmark_path.read_text(encoding="utf-8"))
    benchmark["git_status"]["dirty"] = True
    benchmark["git_status"]["changed_file_count"] = 3
    benchmark["git_status"]["source_dirty"] = True
    benchmark["git_status"]["source_changed_file_count"] = 1
    benchmark["git_status"]["generated_dirty"] = True
    benchmark["git_status"]["generated_changed_file_count"] = 2
    benchmark["summary"]["release_lock_ready"] = False
    benchmark["summary"]["working_tree_dirty"] = True
    benchmark["summary"]["changed_file_count"] = 3
    benchmark["summary"]["source_tree_dirty"] = True
    benchmark["summary"]["source_changed_file_count"] = 1
    benchmark["summary"]["generated_tree_dirty"] = True
    benchmark["summary"]["generated_changed_file_count"] = 2
    benchmark["release_lock"]["ready"] = False
    benchmark["release_lock"]["reason"] = "source files were dirty at generation time"
    benchmark_path.write_text(json.dumps(benchmark, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for report_name in ["skill-overview", "skill-interpretation"]:
        report_path = stale_clean_lock_root / "reports" / f"{report_name}.json"
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["benchmark_reproducibility"]["summary"]["release_lock_ready"] = False
        report["benchmark_reproducibility"]["summary"]["working_tree_dirty"] = True
        report["benchmark_reproducibility"]["summary"]["changed_file_count"] = 3
        report["benchmark_reproducibility"]["summary"]["source_tree_dirty"] = True
        report["benchmark_reproducibility"]["summary"]["source_changed_file_count"] = 1
        report["benchmark_reproducibility"]["summary"]["generated_tree_dirty"] = True
        report["benchmark_reproducibility"]["summary"]["generated_changed_file_count"] = 2
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=stale_clean_lock_root, capture_output=True, text=True, check=True)
    subprocess.run(["git", "add", "."], cwd=stale_clean_lock_root, capture_output=True, text=True, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Yao Test", "-c", "user.email=yao-test@example.com", "commit", "-m", "seed"],
        cwd=stale_clean_lock_root,
        capture_output=True,
        text=True,
        check=True,
    )
    stale_clean_lock_proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(stale_clean_lock_root),
            "--output-json",
            str(TMP / "stale_clean_lock.json"),
            "--output-md",
            str(TMP / "stale_clean_lock.md"),
            "--generated-at",
            "2026-06-15",
        ]
    )
    assert stale_clean_lock_proc.returncode == 2, stale_clean_lock_proc.stdout
    stale_clean_lock_payload = json.loads(stale_clean_lock_proc.stdout)
    stale_clean_lock_checks = {item["key"]: item for item in stale_clean_lock_payload["checks"]}
    assert stale_clean_lock_checks["benchmark-release-lock-self-consistency"]["status"] == "pass", (
        stale_clean_lock_checks["benchmark-release-lock-self-consistency"]
    )
    assert stale_clean_lock_checks["benchmark-clean-worktree-release-lock"]["status"] == "fail", (
        stale_clean_lock_checks["benchmark-clean-worktree-release-lock"]
    )

    generated_only_lock_root = TMP / "generated-only-lock-skill"
    copy_reports(generated_only_lock_root)
    generated_benchmark_path = generated_only_lock_root / "reports" / "benchmark_reproducibility.json"
    generated_benchmark = json.loads(generated_benchmark_path.read_text(encoding="utf-8"))
    generated_benchmark["git_status"]["dirty"] = True
    generated_benchmark["git_status"]["changed_file_count"] = 4
    generated_benchmark["git_status"]["source_dirty"] = False
    generated_benchmark["git_status"]["source_changed_file_count"] = 0
    generated_benchmark["git_status"]["generated_dirty"] = True
    generated_benchmark["git_status"]["generated_changed_file_count"] = 4
    generated_benchmark["summary"]["release_lock_ready"] = True
    generated_benchmark["summary"]["working_tree_dirty"] = True
    generated_benchmark["summary"]["changed_file_count"] = 4
    generated_benchmark["summary"]["source_tree_dirty"] = False
    generated_benchmark["summary"]["source_changed_file_count"] = 0
    generated_benchmark["summary"]["generated_tree_dirty"] = True
    generated_benchmark["summary"]["generated_changed_file_count"] = 4
    generated_benchmark["release_lock"]["ready"] = True
    generated_benchmark["release_lock"]["reason"] = "only generated evidence artifacts were dirty at generation time"
    generated_benchmark_path.write_text(
        json.dumps(generated_benchmark, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    generated_only_proc = run(
        [
            sys.executable,
            str(SCRIPT),
            str(generated_only_lock_root),
            "--output-json",
            str(TMP / "generated_only_lock.json"),
            "--output-md",
            str(TMP / "generated_only_lock.md"),
            "--generated-at",
            "2026-06-15",
        ]
    )
    generated_only_payload = json.loads(generated_only_proc.stdout)
    generated_only_checks = {item["key"]: item for item in generated_only_payload["checks"]}
    assert generated_only_checks["benchmark-release-lock-self-consistency"]["status"] == "pass", (
        generated_only_checks["benchmark-release-lock-self-consistency"]
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
