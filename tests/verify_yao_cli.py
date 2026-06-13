#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "yao.py"
BENCHMARK_FIXTURE_DIR = ROOT / "tests" / "fixtures" / "github_benchmark_scan"
sys.path.insert(0, str(ROOT / "scripts"))
import yao as yao_cli_module  # noqa: E402
import yao_cli_config  # noqa: E402
import yao_cli_parser  # noqa: E402
import yao_cli_report_commands  # noqa: E402
import yao_cli_runtime  # noqa: E402


def run(*args: str, input_text: str | None = None) -> dict:
    env = dict(os.environ)
    env["YAO_CLI_TELEMETRY"] = "0"
    env.pop("YAO_CLI_TELEMETRY_EVENTS", None)
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        input=input_text,
        env=env,
    )
    payload = json.loads(proc.stdout)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "payload": payload,
        "stderr": proc.stderr,
    }


def run_with_env(extra_env: dict[str, str], *args: str) -> dict:
    env = dict(os.environ)
    env.update(extra_env)
    proc = subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(proc.stdout)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "payload": payload,
        "stderr": proc.stderr,
    }


def main() -> None:
    tmp_root = ROOT / "tests" / "tmp_cli"
    if tmp_root.exists():
        subprocess.run(["rm", "-rf", str(tmp_root)], check=True)
    tmp_root.mkdir(parents=True, exist_ok=True)
    remote_version = tmp_root / "remote-version.txt"
    remote_version.write_text("9.9.9\n", encoding="utf-8")
    assert yao_cli_config.resolve_target("root")["title"] == "Root Description Optimization"
    assert yao_cli_config.resolve_promotion_target("root") == "yao-meta-skill"
    assert yao_cli_config.infer_archetype("Standardize team review workflow.", "")[0] == "production"
    assert yao_cli_config.infer_archetype("Govern release policy.", "")[0] == "governed"
    assert "--entry" in yao_cli_config.baseline_compare_args()
    assert "scripts/provider_output_eval_runner.py" in yao_cli_config.provider_output_runner_command("openai")
    assert "--allow-custom-base-url" in yao_cli_config.provider_output_runner_command("openai", allow_custom_base_url=True)
    assert yao_cli_parser.SCRIPT_INTERFACE == "internal-module"
    assert yao_cli_runtime.SCRIPT_INTERFACE == "internal-module"
    assert yao_cli_report_commands.SCRIPT_INTERFACE == "internal-module"
    assert callable(yao_cli_module.command_review_studio)
    parser_help = yao_cli_module.build_parser().format_help()
    assert "quickstart" in parser_help, parser_help
    assert "review-studio" in parser_help, parser_help
    assert "python-compat" in parser_help, parser_help
    assert "architecture-audit" in parser_help, parser_help
    assert "skill-os2-audit" in parser_help, parser_help
    assert "skill-os2-coverage" in parser_help, parser_help
    assert "world-class-evidence" in parser_help, parser_help
    assert "world-class-ledger" in parser_help, parser_help
    assert "world-class-intake" in parser_help, parser_help
    assert "world-class-claim-guard" in parser_help, parser_help
    assert "benchmark-reproducibility" in parser_help, parser_help
    assert "telemetry-import" in parser_help, parser_help
    assert "telemetry-emit" in parser_help, parser_help
    assert "telemetry-hooks" in parser_help, parser_help
    assert "--record-cli-telemetry" in parser_help, parser_help

    init_result = run("init", "cli-demo-skill", "--description", "CLI demo skill.", "--output-dir", str(tmp_root))
    assert init_result["ok"], init_result
    created = Path(init_result["payload"]["root"])
    assert (created / "SKILL.md").exists(), created
    assert (created / "README.md").exists(), created
    assert (created / "reports" / "intent-dialogue.md").exists(), created
    assert (created / "reports" / "intent-confidence.md").exists(), created
    assert (created / "reports" / "skill-overview.html").exists(), created
    assert (created / "reports" / "review-studio.html").exists(), created
    assert (created / "reports" / "review-studio.json").exists(), created
    assert (created / "reports" / "review-viewer.html").exists(), created
    assert (created / "reports" / "reference-scan.md").exists(), created
    assert (created / "reports" / "reference-synthesis.md").exists(), created
    assert (created / "reports" / "output-risk-profile.md").exists(), created
    assert (created / "reports" / "artifact-design-profile.md").exists(), created
    assert (created / "reports" / "prompt-quality-profile.md").exists(), created
    assert (created / "reports" / "system-model.md").exists(), created
    assert (created / "reports" / "skill-ir.json").exists(), created
    assert (created / "reports" / "compiled_targets.md").exists(), created
    assert (created / "reports" / "compiled_targets.json").exists(), created
    assert (created / "reports" / "iteration-directions.md").exists(), created
    assert (created / "reports" / "adoption_drift_report.md").exists(), created
    assert (created / "reports" / "adoption_drift_report.json").exists(), created
    assert (created / "reports" / "review_waivers.md").exists(), created
    assert (created / "reports" / "review_waivers.json").exists(), created
    assert (created / "reports" / "review_annotations.md").exists(), created
    assert (created / "reports" / "review_annotations.json").exists(), created
    assert "Honest Boundaries" in (created / "SKILL.md").read_text(encoding="utf-8"), created
    init_report_view = init_result["payload"]["report_view"]
    assert init_report_view["html_report"].endswith("reports/skill-overview.html"), init_report_view
    assert Path(init_report_view["html_report"]).exists(), init_report_view
    assert init_report_view["review_studio"].endswith("reports/review-studio.html"), init_report_view
    assert Path(init_report_view["review_studio"]).exists(), init_report_view
    assert "Skill 已创建完成" in init_report_view["message"], init_report_view
    assert "Review Studio 2.0" in init_report_view["message"], init_report_view
    assert "目标编译" in init_report_view["message"], init_report_view
    assert "reports/compiled_targets.md" in init_report_view["message"], init_report_view
    assert "概述、指标、原理、触发边界、输入输出、目标编译、质量评估、风险治理、包体资产和升级路线" in init_report_view["message"], init_report_view
    assert "默认使用中文简体" in init_report_view["message"], init_report_view
    assert "切换英文版" in init_report_view["message"], init_report_view
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
    assert architecture_result["payload"]["summary"]["blocker_count"] == 0, architecture_result
    assert 30 <= architecture_result["payload"]["summary"]["command_handler_count"] < 50, architecture_result

    world_class_evidence_result = run(
        "world-class-evidence",
        str(ROOT),
        "--output-json",
        str(tmp_root / "world_class_evidence_plan.json"),
        "--output-md",
        str(tmp_root / "world_class_evidence_plan.md"),
        "--generated-at",
        "2026-06-13",
    )
    assert world_class_evidence_result["ok"], world_class_evidence_result
    assert world_class_evidence_result["payload"]["summary"]["decision"] == "collect-external-evidence", world_class_evidence_result
    assert world_class_evidence_result["payload"]["summary"]["ready_to_claim_world_class"] is False, world_class_evidence_result

    world_class_ledger_result = run(
        "world-class-ledger",
        str(ROOT),
        "--output-json",
        str(tmp_root / "world_class_evidence_ledger.json"),
        "--output-md",
        str(tmp_root / "world_class_evidence_ledger.md"),
        "--generated-at",
        "2026-06-13",
    )
    assert world_class_ledger_result["ok"], world_class_ledger_result
    assert world_class_ledger_result["payload"]["summary"]["pending_count"] == 4, world_class_ledger_result

    world_class_intake_result = run(
        "world-class-intake",
        str(ROOT),
        "--output-json",
        str(tmp_root / "world_class_evidence_intake.json"),
        "--output-md",
        str(tmp_root / "world_class_evidence_intake.md"),
        "--generated-at",
        "2026-06-14",
    )
    assert world_class_intake_result["ok"], world_class_intake_result
    assert world_class_intake_result["payload"]["summary"]["decision"] == "awaiting-submissions", world_class_intake_result
    assert world_class_intake_result["payload"]["summary"]["template_pass_count"] == 4, world_class_intake_result
    assert world_class_intake_result["payload"]["summary"]["ready_to_claim_world_class"] is False, world_class_intake_result
    assert world_class_ledger_result["payload"]["summary"]["ready_to_claim_world_class"] is False, world_class_ledger_result

    world_class_claim_guard_result = run(
        "world-class-claim-guard",
        str(ROOT),
        "--output-json",
        str(tmp_root / "world_class_claim_guard.json"),
        "--output-md",
        str(tmp_root / "world_class_claim_guard.md"),
        "--generated-at",
        "2026-06-14",
    )
    assert world_class_claim_guard_result["ok"], world_class_claim_guard_result
    assert world_class_claim_guard_result["payload"]["summary"]["decision"] == "claim-guard-pass-evidence-pending", world_class_claim_guard_result
    assert world_class_claim_guard_result["payload"]["summary"]["violation_count"] == 0, world_class_claim_guard_result
    assert world_class_claim_guard_result["payload"]["summary"]["ledger_pending_count"] == 4, world_class_claim_guard_result

    benchmark_reproducibility_result = run(
        "benchmark-reproducibility",
        str(ROOT),
        "--output-json",
        str(tmp_root / "benchmark_reproducibility.json"),
        "--output-md",
        str(tmp_root / "benchmark_reproducibility.md"),
        "--generated-at",
        "2026-06-13",
    )
    assert benchmark_reproducibility_result["ok"], benchmark_reproducibility_result
    assert benchmark_reproducibility_result["payload"]["summary"]["reproducibility_ready"] is True, benchmark_reproducibility_result
    assert benchmark_reproducibility_result["payload"]["summary"]["world_class_ready"] is False, benchmark_reproducibility_result

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
    assert (quickstart_root / "reports" / "review-viewer.html").exists(), quickstart_root
    assert (quickstart_root / "reports" / "review-studio.html").exists(), quickstart_root
    assert (quickstart_root / "reports" / "github-benchmark-scan.md").exists(), quickstart_root
    assert (quickstart_root / "reports" / "intent-confidence.md").exists(), quickstart_root
    assert (quickstart_root / "reports" / "reference-synthesis.md").exists(), quickstart_root
    assert (quickstart_root / "reports" / "artifact-design-profile.md").exists(), quickstart_root
    assert (quickstart_root / "reports" / "prompt-quality-profile.md").exists(), quickstart_root
    assert (quickstart_root / "reports" / "system-model.md").exists(), quickstart_root
    assert (quickstart_root / "reports" / "compiled_targets.md").exists(), quickstart_root
    assert (quickstart_root / "reports" / "compiled_targets.json").exists(), quickstart_root
    assert (quickstart_root / "reports" / "adoption_drift_report.md").exists(), quickstart_root
    assert (quickstart_root / "reports" / "review_waivers.md").exists(), quickstart_root
    assert (quickstart_root / "reports" / "review_annotations.md").exists(), quickstart_root
    assert quickstart_result["payload"]["archetype"] == "production", quickstart_result
    assert quickstart_result["payload"]["guidance"]["experience_note"], quickstart_result
    assert quickstart_result["payload"]["guidance"]["problem_diagnosis"]["candidates"], quickstart_result
    assert quickstart_result["payload"]["intent_confidence"]["score"] >= 70, quickstart_result
    assert quickstart_result["payload"]["recommendation"]["summary"], quickstart_result
    assert quickstart_result["payload"]["reference_mode"]["mode"] == "silent", quickstart_result
    quickstart_report_view = quickstart_result["payload"]["report_view"]
    assert quickstart_report_view["html_report"].endswith("reports/skill-overview.html"), quickstart_report_view
    assert Path(quickstart_report_view["html_report"]).exists(), quickstart_report_view
    assert Path(quickstart_report_view["review_studio"]).exists(), quickstart_report_view
    assert "Skill 已创建完成" in quickstart_report_view["message"], quickstart_report_view
    assert "默认使用中文简体" in quickstart_report_view["message"], quickstart_report_view
    assert quickstart_result["payload"]["guidance"]["next_steps"][0].startswith("Open reports/skill-overview.html"), quickstart_result
    assert "reports/review-studio.html" in quickstart_result["payload"]["guidance"]["next_steps"][2], quickstart_result
    assert "audit report" in quickstart_result["payload"]["guidance"]["next_steps"][0], quickstart_result
    assert quickstart_result["payload"]["reviewer_evidence"]["artifacts"]["reference_synthesis"].endswith(
        "reports/reference-synthesis.md"
    ), quickstart_result
    assert quickstart_result["payload"]["reviewer_evidence"]["artifacts"]["prompt_quality_profile"].endswith(
        "reports/prompt-quality-profile.md"
    ), quickstart_result
    assert quickstart_result["payload"]["reviewer_evidence"]["artifacts"]["system_model"].endswith(
        "reports/system-model.md"
    ), quickstart_result
    assert quickstart_result["payload"]["reviewer_evidence"]["artifacts"]["review_studio"].endswith(
        "reports/review-studio.html"
    ), quickstart_result
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
    assert "output_review_adjudication" in report_result["payload"]["artifacts"], report_result
    assert "adoption_drift" in report_result["payload"]["artifacts"], report_result
    assert "review_annotations" in report_result["payload"]["artifacts"], report_result
    assert "world_class_evidence_plan" in report_result["payload"]["artifacts"], report_result
    assert "world_class_evidence_ledger" in report_result["payload"]["artifacts"], report_result
    assert "world_class_evidence_intake" in report_result["payload"]["artifacts"], report_result
    assert "world_class_claim_guard" in report_result["payload"]["artifacts"], report_result
    assert "benchmark_reproducibility" in report_result["payload"]["artifacts"], report_result
    assert "skill_os2_coverage" in report_result["payload"]["artifacts"], report_result
    report_output_execution = json.loads((ROOT / "reports" / "output_execution_runs.json").read_text(encoding="utf-8"))
    assert report_output_execution["summary"]["command_executed_count"] == 10, report_output_execution
    assert report_output_execution["summary"]["recorded_fixture_count"] == 0, report_output_execution
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

    runtime_permissions_result = run(
        "runtime-permissions",
        ".",
        "--package-dir",
        str(package_zip_dir),
        "--output-json",
        str(tmp_root / "runtime_permission_probes.json"),
        "--output-md",
        str(tmp_root / "runtime_permission_probes.md"),
    )
    assert runtime_permissions_result["ok"], runtime_permissions_result
    assert runtime_permissions_result["payload"]["summary"]["metadata_fallback_count"] == 4, runtime_permissions_result
    assert runtime_permissions_result["payload"]["summary"]["native_enforcement_count"] == 0, runtime_permissions_result

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
