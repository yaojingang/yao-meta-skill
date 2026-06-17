#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

from yao_cli_helpers import (
    BENCHMARK_FIXTURE_DIR,
    ROOT,
    assert_cli_module_contracts,
    assert_created_skill_reports,
    assert_creation_report_view,
    assert_help_surface,
    refresh_root_report_consistency_inputs,
    run,
    run_with_env,
)


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_cli"
    if tmp_root.exists():
        subprocess.run(["rm", "-rf", str(tmp_root)], check=True)
    tmp_root.mkdir(parents=True, exist_ok=True)
    remote_version = tmp_root / "remote-version.txt"
    remote_version.write_text("9.9.9\n", encoding="utf-8")
    assert_cli_module_contracts()
    assert_help_surface()

    init_result = run("init", "cli-demo-skill", "--description", "CLI demo skill.", "--output-dir", str(tmp_root))
    assert init_result["ok"], init_result
    created = Path(init_result["payload"]["root"])
    assert (created / "SKILL.md").exists(), created
    assert (created / "README.md").exists(), created
    assert_created_skill_reports(created)
    assert "Honest Boundaries" in (created / "SKILL.md").read_text(encoding="utf-8"), created
    assert_creation_report_view(init_result["payload"]["report_view"])
    init_skill_ir = init_result["payload"]["skill_ir"]
    assert init_skill_ir["name"] == "cli-demo-skill", init_skill_ir
    assert init_skill_ir["trigger_samples"] >= 1, init_skill_ir

    telemetry_log = tmp_root / "cli-telemetry-events.jsonl"
    telemetry_env = {
        "YAO_CLI_TELEMETRY": "1",
        "YAO_CLI_TELEMETRY_EVENTS": str(telemetry_log),
    }
    telemetry_ok = run_with_env(telemetry_env, "validate", str(created))
    assert telemetry_ok["ok"], telemetry_ok
    telemetry_fail = run_with_env(
        telemetry_env,
        "output-exec",
        "--runner-command",
        json.dumps([sys.executable, str(ROOT / "scripts" / "local_output_eval_runner.py")]),
        "--provider-runner",
        "openai",
    )
    assert not telemetry_fail["ok"], telemetry_fail
    telemetry_events = [json.loads(line) for line in telemetry_log.read_text(encoding="utf-8").splitlines()]
    assert len(telemetry_events) == 2, telemetry_events
    assert telemetry_events[0]["event"] == "script_run", telemetry_events
    assert telemetry_events[0]["source"] == "yao_cli", telemetry_events
    assert telemetry_events[0]["command"] == "validate", telemetry_events
    assert telemetry_events[0]["outcome"] == "accepted", telemetry_events
    assert telemetry_events[0]["failure_type"] == "none", telemetry_events
    assert telemetry_events[1]["command"] == "output-exec", telemetry_events
    assert telemetry_events[1]["outcome"] == "failed", telemetry_events
    assert telemetry_events[1]["failure_type"] == "script_error", telemetry_events

    skill_os2_audit_result = run(
        "skill-os2-audit",
        str(ROOT),
        "--output-json",
        str(tmp_root / "skill_os2_audit.json"),
        "--output-md",
        str(tmp_root / "skill_os2_audit.md"),
        "--generated-at",
        "2026-06-13",
    )
    assert skill_os2_audit_result["ok"], skill_os2_audit_result
    assert skill_os2_audit_result["payload"]["summary"]["decision"] == "continue-iteration", skill_os2_audit_result
    assert skill_os2_audit_result["payload"]["summary"]["world_class_ready"] is False, skill_os2_audit_result

    skill_os2_coverage_result = run(
        "skill-os2-coverage",
        str(ROOT),
        "--output-json",
        str(tmp_root / "skill_os2_coverage.json"),
        "--output-md",
        str(tmp_root / "skill_os2_coverage.md"),
        "--generated-at",
        "2026-06-14",
    )
    assert skill_os2_coverage_result["ok"], skill_os2_coverage_result
    assert skill_os2_coverage_result["payload"]["summary"]["local_blueprint_ready"] is True, skill_os2_coverage_result
    assert skill_os2_coverage_result["payload"]["summary"]["public_world_class_ready"] is False, skill_os2_coverage_result

    python_compat_result = run(
        "python-compat",
        str(ROOT),
        "--output-json",
        str(tmp_root / "python_compatibility.json"),
        "--output-md",
        str(tmp_root / "python_compatibility.md"),
        "--generated-at",
        "2026-06-14",
    )
    assert python_compat_result["ok"], python_compat_result
    assert python_compat_result["payload"]["summary"]["target_python"] == "3.11", python_compat_result
    assert python_compat_result["payload"]["summary"]["issue_count"] == 0, python_compat_result
    assert python_compat_result["payload"]["summary"]["file_count"] >= 50, python_compat_result

    architecture_result = run(
        "architecture-audit",
        str(ROOT),
        "--output-json",
        str(tmp_root / "architecture_maintainability.json"),
        "--output-md",
        str(tmp_root / "architecture_maintainability.md"),
        "--generated-at",
        "2026-06-14",
    )
    assert architecture_result["ok"], architecture_result
    assert architecture_result["payload"]["summary"]["hotspot_count"] == 0, architecture_result
    assert architecture_result["payload"]["summary"]["watchlist_count"] == 0, architecture_result
    assert architecture_result["payload"]["summary"]["blocker_count"] == 0, architecture_result
    assert architecture_result["payload"]["summary"]["command_handler_count"] >= 60, architecture_result
    assert architecture_result["payload"]["summary"]["entrypoint_command_handler_count"] < 30, architecture_result
    refresh_root_report_consistency_inputs(run, ROOT)

    evidence_consistency_result = run(
        "evidence-consistency", str(ROOT),
        "--output-json", str(tmp_root / "evidence_consistency.json"),
        "--output-md", str(tmp_root / "evidence_consistency.md"),
        "--generated-at", "2026-06-15",
    )
    assert evidence_consistency_result["ok"], evidence_consistency_result
    assert evidence_consistency_result["payload"]["summary"]["decision"] == "consistent", evidence_consistency_result

    quickstart_result = run(
        "quickstart",
        "--output-dir",
        str(tmp_root),
        "--github-fixture-dir",
        str(BENCHMARK_FIXTURE_DIR),
        "--no-update-check",
        input_text=(
            "quickstart-skill\n"
            "Turn messy release notes into a reusable release brief skill.\n"
            "release notes, changelog snippets\n"
            "A reusable markdown release brief.\n"
            "looks right\n"
            "It should not publish blog posts or send email.\n"
            "consistency, portability\n"
            "production\n"
            "production\n"
            "\n"
            "privacy and naming\n"
        ),
    )
    assert quickstart_result["ok"], quickstart_result
    quickstart_root = Path(quickstart_result["payload"]["root"])
    quickstart_reports = [
        "review-viewer.html", "skill-interpretation.html", "skill-interpretation.json", "review-studio.html",
        "github-benchmark-scan.md", "intent-confidence.md", "reference-synthesis.md",
        "artifact-design-profile.md", "prompt-quality-profile.md", "system-model.md", "compiled_targets.md",
        "compiled_targets.json", "adoption_drift_report.md", "review_waivers.md", "review_annotations.md",
    ]
    assert all((quickstart_root / "reports" / path).exists() for path in quickstart_reports), quickstart_root
    assert quickstart_result["payload"]["archetype"] == "production", quickstart_result
    assert quickstart_result["payload"]["guidance"]["experience_note"], quickstart_result
    assert quickstart_result["payload"]["guidance"]["problem_diagnosis"]["candidates"], quickstart_result
    assert quickstart_result["payload"]["intent_confidence"]["score"] >= 70, quickstart_result
    assert quickstart_result["payload"]["recommendation"]["summary"], quickstart_result
    assert quickstart_result["payload"]["reference_mode"]["mode"] == "silent", quickstart_result
    quickstart_report_view = quickstart_result["payload"]["report_view"]
    assert quickstart_report_view["html_report"].endswith("reports/skill-overview.html"), quickstart_report_view
    assert quickstart_report_view["interpretation_report"].endswith("reports/skill-interpretation.html"), quickstart_report_view
    assert Path(quickstart_report_view["html_report"]).exists(), quickstart_report_view
    assert Path(quickstart_report_view["interpretation_report"]).exists(), quickstart_report_view
    assert Path(quickstart_report_view["review_studio"]).exists(), quickstart_report_view
    assert "Skill 已创建完成" in quickstart_report_view["message"], quickstart_report_view
    assert "默认使用中文简体" in quickstart_report_view["message"], quickstart_report_view
    assert quickstart_result["payload"]["guidance"]["next_steps"][0].startswith("Open reports/skill-interpretation.html"), quickstart_result
    assert quickstart_result["payload"]["guidance"]["next_steps"][1].startswith("Open reports/skill-overview.html"), quickstart_result
    assert "reports/review-studio.html" in quickstart_result["payload"]["guidance"]["next_steps"][3], quickstart_result
    assert "interpretation report" in quickstart_result["payload"]["guidance"]["next_steps"][0], quickstart_result
    evidence_artifacts = quickstart_result["payload"]["reviewer_evidence"]["artifacts"]
    assert evidence_artifacts["reference_synthesis"].endswith("reports/reference-synthesis.md"), quickstart_result
    assert evidence_artifacts["prompt_quality_profile"].endswith("reports/prompt-quality-profile.md"), quickstart_result
    assert evidence_artifacts["system_model"].endswith("reports/system-model.md"), quickstart_result
    assert evidence_artifacts["skill_interpretation"].endswith("reports/skill-interpretation.html"), quickstart_result
    assert evidence_artifacts["review_studio"].endswith("reports/review-studio.html"), quickstart_result
    assert "uncertainty_or_conflict" not in quickstart_result["payload"], quickstart_result
    quickstart_manifest = json.loads((quickstart_root / "manifest.json").read_text(encoding="utf-8"))
    assert quickstart_manifest["status"] == "active", quickstart_manifest
    assert quickstart_manifest["lifecycle_stage"] == "production", quickstart_manifest
    quickstart_validate_result = run("validate", str(quickstart_root), "--require-manifest")
    assert quickstart_validate_result["ok"], quickstart_validate_result

    quickstart_conflict_result = run(
        "quickstart",
        "--output-dir",
        str(tmp_root),
        "--github-fixture-dir",
        str(BENCHMARK_FIXTURE_DIR),
        "--no-update-check",
        input_text=(
            "quickstart-conflict-skill\n"
            "Turn repeated release notes into a governed release command skill.\n"
            "release notes, changelog snippets\n"
            "A governed release packet.\n"
            "looks right\n"
            "It should not publish blog posts or send email.\n"
            "auditability, portability\n"
            "governed\n"
            "governed\n"
            "Minimal vibe helper::taste::Keep the first pass fast, minimal, and lightweight.::Do not add review, governance, or approval steps.\n"
            "privacy and naming\n"
        ),
    )
    assert quickstart_conflict_result["ok"], quickstart_conflict_result
    assert quickstart_conflict_result["payload"]["reference_mode"]["mode"] == "explicit", quickstart_conflict_result
    assert quickstart_conflict_result["payload"]["uncertainty_or_conflict"]["conflicts"], quickstart_conflict_result

    validate_result = run("validate", str(created))
    assert validate_result["ok"], validate_result
    assert len(validate_result["payload"]["steps"]) == 4, validate_result

    skill_report_result = run("skill-report", str(created))
    assert skill_report_result["ok"], skill_report_result
    assert skill_report_result["payload"]["artifacts"]["html"].endswith("reports/skill-overview.html"), skill_report_result

    skill_interpretation_result = run("skill-interpretation", str(created))
    assert skill_interpretation_result["ok"], skill_interpretation_result
    assert skill_interpretation_result["payload"]["artifacts"]["html"].endswith(
        "reports/skill-interpretation.html"
    ), skill_interpretation_result
    assert skill_interpretation_result["payload"]["summary"]["report_kind"] == "skill-interpretation", skill_interpretation_result
    assert skill_interpretation_result["payload"]["summary"]["default_language"] == "zh-CN", skill_interpretation_result

    review_viewer_result = run("review-viewer", str(created))
    assert review_viewer_result["ok"], review_viewer_result
    assert review_viewer_result["payload"]["artifacts"]["html"].endswith("reports/review-viewer.html"), review_viewer_result

    review_studio_result = run("review-studio", str(created))
    assert review_studio_result["ok"], review_studio_result
    assert review_studio_result["payload"]["artifacts"]["html"].endswith("reports/review-studio.html"), review_studio_result
    assert review_studio_result["payload"]["summary"]["gate_count"] == 16, review_studio_result
    created_world_class_gate = next(item for item in review_studio_result["payload"]["gates"] if item["key"] == "world-class-evidence")
    assert created_world_class_gate["status"] == "pass", created_world_class_gate
    assert "optional" in created_world_class_gate["detail"], created_world_class_gate
    created_architecture_gate = next(
        item for item in review_studio_result["payload"]["gates"] if item["key"] == "architecture-maintainability"
    )
    assert created_architecture_gate["status"] == "pass", created_architecture_gate
    assert "optional" in created_architecture_gate["detail"], created_architecture_gate

    review_waivers_result = run(
        "review-waivers",
        str(created),
        "--add-waiver",
        "--gate-key",
        "trust-report",
        "--reviewer",
        "Yao Team",
        "--reason",
        "Trust warning accepted for this CLI demo with bounded release follow-up.",
        "--expires-at",
        "2026-09-30",
        "--generated-at",
        "2026-06-13",
    )
    assert review_waivers_result["ok"], review_waivers_result
    assert review_waivers_result["payload"]["summary"]["active_count"] == 1, review_waivers_result
    assert "trust-report" in review_waivers_result["payload"]["summary"]["covered_gate_keys"], review_waivers_result

    review_annotations_result = run(
        "review-annotations",
        str(created),
        "--add-annotation",
        "--annotation-id",
        "ann-cli-trigger",
        "--gate-key",
        "trigger-lab",
        "--target-path",
        "SKILL.md",
        "--line",
        "1",
        "--severity",
        "note",
        "--reviewer",
        "Yao QA",
        "--created-at",
        "2026-06-13",
        "--body",
        "Check trigger wording before reuse.",
    )
    assert review_annotations_result["ok"], review_annotations_result
    assert review_annotations_result["payload"]["summary"]["annotation_count"] == 1, review_annotations_result
    assert (created / "reports" / "review_annotations.md").exists(), review_annotations_result

    registry_result = run(
        "registry-audit",
        str(ROOT),
        "--registry-dir",
        str(tmp_root / "registry"),
        "--output-json",
        str(tmp_root / "registry_audit.json"),
        "--output-md",
        str(tmp_root / "registry_audit.md"),
        "--generated-at",
        "2026-06-13",
    )
    assert registry_result["ok"], registry_result
    assert registry_result["payload"]["package"]["name"] == "yao-meta-skill", registry_result
    assert registry_result["payload"]["package"]["checksums"]["package_sha256"], registry_result

    reference_scan_result = run(
        "reference-scan",
        str(created),
        "--external-reference",
        "World Class Method::method::Borrow the smallest repeatable evaluation loop.::Do not copy heavy ceremony.",
        "--user-reference",
        "Product I Admire::taste::Learn the calm structure and clarity of output.::Do not copy wording.",
        "--local-constraint",
        "Local Naming::structure::Keep folder naming aligned with the local library.::Do not inherit private references.",
    )
    assert reference_scan_result["ok"], reference_scan_result
    assert reference_scan_result["payload"]["artifacts"]["markdown"].endswith("reports/reference-scan.md"), reference_scan_result
    assert len(reference_scan_result["payload"]["summary"]["user_references"]) == 1, reference_scan_result

    github_benchmark_result = run(
        "github-benchmark-scan",
        str(created),
        "--query",
        "workflow evaluation portability",
        "--fixture-dir",
        str(BENCHMARK_FIXTURE_DIR),
    )
    assert github_benchmark_result["ok"], github_benchmark_result
    assert len(github_benchmark_result["payload"]["repositories"]) == 3, github_benchmark_result

    intent_confidence_result = run("intent-confidence", str(created))
    assert intent_confidence_result["ok"], intent_confidence_result
    assert intent_confidence_result["payload"]["summary"]["score"] >= 0, intent_confidence_result

    intent_result = run("intent-dialogue", str(created))
    assert intent_result["ok"], intent_result
    assert intent_result["payload"]["artifacts"]["markdown"].endswith("reports/intent-dialogue.md"), intent_result

    reference_synthesis_result = run("reference-synthesis", str(created))
    assert reference_synthesis_result["ok"], reference_synthesis_result
    assert reference_synthesis_result["payload"]["artifacts"]["markdown"].endswith("reports/reference-synthesis.md"), reference_synthesis_result

    output_risk_result = run("output-risk-profile", str(created))
    assert output_risk_result["ok"], output_risk_result
    assert output_risk_result["payload"]["artifacts"]["markdown"].endswith("reports/output-risk-profile.md"), output_risk_result
    assert output_risk_result["payload"]["summary"]["risk_families"], output_risk_result

    artifact_design_result = run("artifact-design-profile", str(created))
    assert artifact_design_result["ok"], artifact_design_result
    assert artifact_design_result["payload"]["artifacts"]["markdown"].endswith("reports/artifact-design-profile.md"), artifact_design_result
    assert artifact_design_result["payload"]["summary"]["quality_gates"], artifact_design_result

    prompt_quality_result = run("prompt-quality-profile", str(created))
    assert prompt_quality_result["ok"], prompt_quality_result
    assert prompt_quality_result["payload"]["artifacts"]["markdown"].endswith("reports/prompt-quality-profile.md"), prompt_quality_result
    assert prompt_quality_result["payload"]["summary"]["quality_matrix"], prompt_quality_result

    system_model_result = run("system-model", str(created))
    assert system_model_result["ok"], system_model_result
    assert system_model_result["payload"]["artifacts"]["markdown"].endswith("reports/system-model.md"), system_model_result
    assert system_model_result["payload"]["summary"]["stability"]["score"] >= 0, system_model_result

    directions_result = run("iteration-directions", str(created))
    assert directions_result["ok"], directions_result
    assert directions_result["payload"]["artifacts"]["markdown"].endswith("reports/iteration-directions.md"), directions_result

    skill_ir_result = run("skill-ir", str(created))
    assert skill_ir_result["ok"], skill_ir_result
    assert skill_ir_result["payload"]["artifacts"]["json"].endswith("reports/skill-ir.json"), skill_ir_result
    created_skill_ir = json.loads((created / "reports" / "skill-ir.json").read_text(encoding="utf-8"))
    assert created_skill_ir["schema_version"] == "2.0.0", created_skill_ir
    assert created_skill_ir["trigger_surface"]["description"], created_skill_ir

    compile_result = run("compile-skill", str(created), "--target", "openai", "--target", "claude", "--target", "generic", "--target", "vscode")
    assert compile_result["ok"], compile_result
    assert compile_result["payload"]["summary"]["target_count"] == 4, compile_result
    assert compile_result["payload"]["summary"]["block_count"] == 0, compile_result
    assert compile_result["payload"]["artifacts"]["markdown"].endswith("reports/compiled_targets.md"), compile_result

    output_eval_result = run(
        "output-eval",
        "--cases",
        str(ROOT / "evals" / "output" / "cases.jsonl"),
        "--output-json",
        str(created / "reports" / "output_quality_scorecard.json"),
        "--output-md",
        str(created / "reports" / "output_quality_scorecard.md"),
        "--blind-pack-json",
        str(created / "reports" / "output_blind_review_pack.json"),
        "--blind-pack-md",
        str(created / "reports" / "output_blind_review_pack.md"),
        "--blind-answer-key-json",
        str(created / "reports" / "output_blind_answer_key.json"),
    )
    assert output_eval_result["ok"], output_eval_result
    assert output_eval_result["payload"]["summary"]["with_skill_pass_rate"] > output_eval_result["payload"]["summary"]["baseline_pass_rate"], output_eval_result
    assert output_eval_result["payload"]["summary"]["blind_pair_count"] == 5, output_eval_result
    assert (created / "reports" / "output_blind_review_pack.md").exists(), output_eval_result
    assert (created / "reports" / "output_blind_answer_key.json").exists(), output_eval_result

    output_exec_result = run(
        "output-exec",
        "--cases",
        str(ROOT / "evals" / "output" / "cases.jsonl"),
        "--output-json",
        str(created / "reports" / "output_execution_runs.json"),
        "--output-md",
        str(created / "reports" / "output_execution_runs.md"),
    )
    assert output_exec_result["ok"], output_exec_result
    assert output_exec_result["payload"]["summary"]["variant_run_count"] == 10, output_exec_result
    assert output_exec_result["payload"]["summary"]["recorded_fixture_count"] == 10, output_exec_result
    assert (created / "reports" / "output_execution_runs.md").exists(), output_exec_result

    output_exec_conflict = run(
        "output-exec",
        "--runner-command",
        json.dumps([sys.executable, str(ROOT / "scripts" / "local_output_eval_runner.py")]),
        "--provider-runner",
        "openai",
    )
    assert not output_exec_conflict["ok"], output_exec_conflict
    assert "Use either --runner-command or --provider-runner" in output_exec_conflict["payload"]["failures"][0], output_exec_conflict

    output_review_result = run(
        "output-review",
        "--blind-pack",
        str(created / "reports" / "output_blind_review_pack.json"),
        "--answer-key",
        str(created / "reports" / "output_blind_answer_key.json"),
        "--decisions",
        str(created / "reports" / "output_review_decisions.json"),
        "--output-json",
        str(created / "reports" / "output_review_adjudication.json"),
        "--output-md",
        str(created / "reports" / "output_review_adjudication.md"),
    )
    assert output_review_result["ok"], output_review_result
    assert output_review_result["payload"]["summary"]["judgment_count"] == 0, output_review_result
    assert output_review_result["payload"]["summary"]["pending_count"] == 5, output_review_result
    assert output_review_result["payload"]["summary"]["reviewer_checklist_count"] == 5, output_review_result
    assert output_review_result["payload"]["summary"]["reviewer_checklist_pending_count"] == 5, output_review_result
    assert all(not item["answer_key_visible"] for item in output_review_result["payload"]["reviewer_checklist"]), output_review_result
    assert (created / "reports" / "output_review_adjudication.md").exists(), output_review_result

    conformance_result = run("conformance", str(created))
    assert conformance_result["ok"], conformance_result
    assert conformance_result["payload"]["summary"]["target_count"] == 5, conformance_result
    assert conformance_result["payload"]["artifacts"]["markdown"].endswith("reports/conformance_matrix.md"), conformance_result

    trust_result = run("trust", str(created))
    assert trust_result["ok"], trust_result
    assert trust_result["payload"]["summary"]["secret_findings"] == 0, trust_result
    assert trust_result["payload"]["artifacts"]["markdown"].endswith("reports/security_trust_report.md"), trust_result

    atlas_result = run(
        "skill-atlas",
        "--workspace-root",
        str(tmp_root),
        "--output-dir",
        str(tmp_root / "skill_atlas"),
        "--report-html",
        str(tmp_root / "skill_atlas.html"),
        "--report-json",
        str(tmp_root / "skill_atlas.json"),
        "--today",
        "2026-06-13",
    )
    assert atlas_result["ok"], atlas_result
    assert atlas_result["payload"]["summary"]["skill_count"] >= 2, atlas_result
    assert atlas_result["payload"]["artifacts"]["report_html"].endswith("skill_atlas.html"), atlas_result

    feedback_result = run(
        "feedback",
        str(created),
        "--note",
        "Keep the first version light and tighten exclusions before adding scripts.",
        "--rating",
        "4",
        "--category",
        "boundary",
        "--recommended-action",
        "tighten-trigger",
    )
    assert feedback_result["ok"], feedback_result
    assert feedback_result["payload"]["feedback"]["summary"]["count"] == 1, feedback_result

    adoption_drift_result = run(
        "adoption-drift",
        str(created),
        "--record-event",
        "skill_activation",
        "--activation-type",
        "explicit",
        "--outcome",
        "accepted",
        "--timestamp",
        "2026-06-13T10:00:00Z",
    )
    assert adoption_drift_result["ok"], adoption_drift_result
    assert adoption_drift_result["payload"]["summary"]["event_count"] == 1, adoption_drift_result
    assert adoption_drift_result["payload"]["artifacts"]["markdown"].endswith(
        "reports/adoption_drift_report.md"
    ), adoption_drift_result

    optimize_result = run("optimize-description", "--target", "root")
    assert optimize_result["ok"], optimize_result
    assert optimize_result["payload"]["winner"]["label"] == "Current", optimize_result

    baseline_compare_result = run("baseline-compare")
    assert baseline_compare_result["ok"], baseline_compare_result
    assert baseline_compare_result["payload"]["summary"]["target_count"] == 3, baseline_compare_result

    promote_result = run("promote-check")
    assert promote_result["ok"], promote_result
    assert promote_result["payload"]["summary"]["blocked"] == 0, promote_result
    review_result = run("review", "--target", "root")
    assert review_result["ok"], review_result
    assert review_result["payload"]["artifacts"]["review_md"].endswith("reports/iteration_bundles/yao-meta-skill/review.md")

    snapshot_result = run("release-snapshot", "--target", "root", "--label", "cli-smoke")
    assert snapshot_result["ok"], snapshot_result
    assert snapshot_result["payload"]["artifacts"]["snapshot_json"].endswith("cli-smoke.json"), snapshot_result

    flow_result = run("workspace-flow", "--target", "root", "--label", "cli-flow")
    assert flow_result["ok"], flow_result
    assert flow_result["payload"]["artifacts"][0]["snapshot"]["artifacts"]["snapshot_md"].endswith("cli-flow.md"), flow_result

    report_result = run("report")
    assert report_result["ok"], report_result
    assert "iteration_ledger" in report_result["payload"]["artifacts"], report_result
    assert "portability_score" in report_result["payload"]["artifacts"], report_result
    assert "python_compatibility" in report_result["payload"]["artifacts"], report_result
    assert "architecture_maintainability" in report_result["payload"]["artifacts"], report_result
    assert "artifact_design_profile" in report_result["payload"]["artifacts"], report_result
    assert "prompt_quality_profile" in report_result["payload"]["artifacts"], report_result
    assert "compiled_targets" in report_result["payload"]["artifacts"], report_result
    assert "output_execution" in report_result["payload"]["artifacts"], report_result
    assert "output_review_kit" in report_result["payload"]["artifacts"], report_result
    assert "output_review_adjudication" in report_result["payload"]["artifacts"], report_result
    assert "adoption_drift" in report_result["payload"]["artifacts"], report_result
    assert "review_annotations" in report_result["payload"]["artifacts"], report_result
    assert "world_class_evidence_plan" in report_result["payload"]["artifacts"], report_result
    assert "world_class_evidence_ledger" in report_result["payload"]["artifacts"], report_result
    assert "world_class_evidence_intake" in report_result["payload"]["artifacts"], report_result
    assert "world_class_claim_guard" in report_result["payload"]["artifacts"], report_result
    assert "benchmark_reproducibility" in report_result["payload"]["artifacts"], report_result
    assert "evidence_consistency" in report_result["payload"]["artifacts"], report_result
    assert all(key in report_result["payload"]["artifacts"] for key in ("skill_os2_audit", "skill_os2_coverage")), report_result
    assert any(step["command"].startswith("render_skill_os2_audit.py ") and step["ok"] for step in report_result["payload"]["steps"]), report_result
    assert "weekly_curator" in report_result["payload"]["artifacts"], report_result
    assert report_result["payload"]["artifacts"]["skill_overview"] == "reports/skill-overview.json", report_result
    assert report_result["payload"]["artifacts"]["skill_interpretation"] == "reports/skill-interpretation.json", report_result
    assert report_result["payload"]["artifacts"]["skill_interpretation_html"] == "reports/skill-interpretation.html", report_result
    assert (report_result["payload"]["artifacts"]["review_studio"], report_result["payload"]["artifacts"]["review_studio_html"]) == ("reports/review-studio.json", "reports/review-studio.html"), report_result
    assert report_result["payload"]["artifacts"]["review_viewer"] == "reports/review-viewer.json", report_result
    assert report_result["payload"]["artifacts"]["review_viewer_html"] == "reports/review-viewer.html", report_result
    report_output_execution = json.loads((ROOT / "reports" / "output_execution_runs.json").read_text(encoding="utf-8"))
    assert report_output_execution["summary"]["command_executed_count"] == 10, report_output_execution
    assert report_output_execution["summary"]["recorded_fixture_count"] == 0, report_output_execution
    if report_output_execution["summary"]["model_executed_count"] > 0:
        assert report_output_execution["summary"]["token_observed_count"] == 10, report_output_execution
        assert report_output_execution["summary"]["token_estimated_count"] == 0, report_output_execution
    else:
        assert report_output_execution["summary"]["model_executed_count"] == 0, report_output_execution

    package_dir = tmp_root / "dist"
    package_result = run("package", ".", "--platform", "generic", "--output-dir", str(package_dir))
    assert package_result["ok"], package_result
    assert (package_dir / "targets" / "generic" / "adapter.json").exists(), package_dir
    generic_adapter = json.loads((package_dir / "targets" / "generic" / "adapter.json").read_text(encoding="utf-8"))
    assert generic_adapter["compiler"]["name"] == "yao-skill-ir-compiler", generic_adapter
    assert generic_adapter["compiled_contract"]["target"] == "generic", generic_adapter

    package_zip_dir = tmp_root / "dist-zip"
    package_zip_result = run(
        "package",
        ".",
        "--platform",
        "openai",
        "--platform",
        "claude",
        "--platform",
        "generic",
        "--platform",
        "vscode",
        "--expectations",
        str(ROOT / "evals" / "packaging_expectations.json"),
        "--output-dir",
        str(package_zip_dir),
        "--zip",
    )
    assert package_zip_result["ok"], package_zip_result
    package_verify_result = run(
        "package-verify",
        ".",
        "--package-dir",
        str(package_zip_dir),
        "--expectations",
        str(ROOT / "evals" / "packaging_expectations.json"),
        "--registry-json",
        str(ROOT / "reports" / "registry_audit.json"),
        "--output-json",
        str(tmp_root / "package_verification.json"),
        "--output-md",
        str(tmp_root / "package_verification.md"),
        "--require-zip",
        "--generated-at",
        "2026-06-13",
    )
    assert package_verify_result["ok"], package_verify_result
    assert package_verify_result["payload"]["summary"]["adapter_count"] == 4, package_verify_result
    assert package_verify_result["payload"]["summary"]["archive_sha256"], package_verify_result

    install_simulate_result = run(
        "install-simulate",
        ".",
        "--package-dir",
        str(package_zip_dir),
        "--install-root",
        str(tmp_root / "install-root"),
        "--output-json",
        str(tmp_root / "install_simulation.json"),
        "--output-md",
        str(tmp_root / "install_simulation.md"),
        "--generated-at",
        "2026-06-13",
    )
    assert install_simulate_result["ok"], install_simulate_result
    assert install_simulate_result["payload"]["summary"]["archive_extracted"], install_simulate_result
    assert install_simulate_result["payload"]["summary"]["adapter_count"] == 4, install_simulate_result

    runtime_permissions_result = run(
        "runtime-permissions",
        ".",
        "--package-dir",
        str(package_zip_dir),
        "--install-simulation-json",
        str(tmp_root / "install_simulation.json"),
        "--output-json",
        str(tmp_root / "runtime_permission_probes_with_install.json"),
        "--output-md",
        str(tmp_root / "runtime_permission_probes.md"),
    )
    assert runtime_permissions_result["ok"], runtime_permissions_result
    runtime_install_summary = runtime_permissions_result["payload"]["summary"]
    assert runtime_install_summary["metadata_fallback_count"] == 4, runtime_install_summary
    assert runtime_install_summary["native_enforcement_count"] == 0, runtime_install_summary
    assert runtime_install_summary["installer_enforcement_pass_count"] == 4, runtime_install_summary
    assert runtime_install_summary["installer_permission_failure_count"] == 0, runtime_install_summary

    upgrade_result = run(
        "upgrade-check",
        ".",
        "--previous-package-json",
        str(ROOT / "registry" / "examples" / "yao-meta-skill-1.0.0.json"),
        "--current-package-json",
        str(ROOT / "reports" / "registry_audit.json"),
        "--output-json",
        str(tmp_root / "upgrade_check.json"),
        "--output-md",
        str(tmp_root / "upgrade_check.md"),
        "--generated-at",
        "2026-06-13",
    )
    assert upgrade_result["ok"], upgrade_result
    assert upgrade_result["payload"]["summary"]["recommended_bump"] == "minor", upgrade_result

    update_result = run(
        "check-update",
        "--force",
        "--no-cache",
        "--version-url",
        remote_version.as_uri(),
        "--manifest-url",
        remote_version.as_uri(),
    )
    assert not update_result["ok"], update_result
    assert update_result["returncode"] == 2, update_result
    assert "Update URL scheme is not allowed: file" in update_result["payload"]["error"], update_result

    test_result = run("test", "--target", "promotion-check")
    assert test_result["ok"], test_result

    print(json.dumps({"ok": True}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
