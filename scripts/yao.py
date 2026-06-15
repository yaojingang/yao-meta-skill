#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path

from yao_cli_config import (
    baseline_compare_args,
    local_output_runner_command,
    resolve_promotion_target,
    resolve_target,
)
from yao_cli_adaptation_commands import (
    command_adapt_apply,
    command_adapt_propose,
    command_adapt_scan,
    command_daily_skillops,
    command_weekly_curator,
)
from yao_cli_create_commands import command_init, command_quickstart
from yao_cli_distribution_commands import (
    command_compile_skill,
    command_conformance,
    command_install_simulate,
    command_package,
    command_package_verify,
    command_registry_audit,
    command_runtime_permissions,
    command_skill_atlas,
    command_skill_ir,
    command_trust,
    command_upgrade_check,
)
from yao_cli_output_commands import (
    command_output_eval,
    command_output_execution,
    command_output_review,
    command_output_review_import,
    command_output_review_kit,
)
from yao_cli_parser import build_parser as build_cli_parser
from yao_cli_report_commands import (
    command_artifact_design_profile,
    command_benchmark_reproducibility,
    command_evidence_consistency,
    command_github_benchmark_scan,
    command_intent_confidence,
    command_intent_dialogue,
    command_iteration_directions,
    command_output_risk_profile,
    command_prompt_quality_profile,
    command_reference_scan,
    command_reference_synthesis,
    command_report,
    command_review_studio,
    command_review_viewer,
    command_skill_os2_audit,
    command_skill_os2_coverage,
    command_skill_interpretation,
    command_skill_report,
    command_system_model,
    command_world_class_claim_guard,
    command_world_class_evidence,
    command_world_class_intake,
    command_world_class_ledger,
    command_world_class_preflight,
    command_world_class_runbook,
    command_world_class_submission_kit,
    command_world_class_submission_review,
)
from yao_cli_runtime import ROOT, run_adoption_drift_if_source_exists, run_script
from yao_cli_telemetry import add_telemetry_args, maybe_record_cli_event


def command_validate(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    runs = [
        run_script("validate_skill.py", [skill_dir]),
        run_script("lint_skill.py", [skill_dir]),
        run_script("governance_check.py", [skill_dir, *(["--require-manifest"] if args.require_manifest else [])]),
        run_script("resource_boundary_check.py", [skill_dir]),
    ]
    report = {
        "ok": all(item["ok"] for item in runs),
        "skill_dir": skill_dir,
        "steps": [
            {
                "command": item["command"],
                "ok": item["ok"],
                "returncode": item["returncode"],
                "payload": item["payload"],
            }
            for item in runs
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def optimize_args_for_target(target_name: str, write: bool) -> list[str]:
    target = resolve_target(target_name)
    cmd = [
        "--description-file",
        str(target["description_file"]),
        "--baseline-description-file",
        str(target["baseline_description_file"]),
        "--semantic-config",
        str(target["semantic_config"]),
        "--dev-cases",
        str(target["dev_cases"]),
        "--holdout-cases",
        str(target["holdout_cases"]),
        "--blind-holdout-cases",
        str(target["blind_holdout_cases"]),
        "--adversarial-cases",
        str(target["adversarial_cases"]),
        "--title",
        target["title"],
    ]
    if write:
        cmd.extend(["--output-json", str(target["output_json"]), "--output-md", str(target["output_md"])])
    return cmd


def command_optimize_description(args: argparse.Namespace) -> int:
    if args.target == "all":
        result = run_script("run_description_optimization_suite.py", [])
    else:
        result = run_script("optimize_description.py", optimize_args_for_target(args.target, args.write))
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_promote_check(args: argparse.Namespace) -> int:
    result = run_script("promotion_checker.py", [])
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_python_compat(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    for path in args.path:
        cmd.extend(["--path", path])
    if args.target_python:
        cmd.extend(["--target-python", args.target_python])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    result = run_script("python_compat_check.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_architecture_audit(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.warn_lines is not None:
        cmd.extend(["--warn-lines", str(args.warn_lines)])
    if args.block_lines is not None:
        cmd.extend(["--block-lines", str(args.block_lines)])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    result = run_script("render_architecture_maintainability.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_feedback(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.note:
        cmd.extend(["--note", args.note])
    cmd.extend(["--rating", str(args.rating), "--category", args.category, "--recommended-action", args.recommended_action])
    result = run_script("collect_feedback.py", cmd)
    viewer = run_script("render_review_viewer.py", [skill_dir])
    report = {
        "ok": result["ok"] and viewer["ok"],
        "feedback": result["payload"] if result["payload"] is not None else result,
        "review_viewer": viewer["payload"] if viewer["payload"] is not None else viewer,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def command_adoption_drift(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.events_jsonl:
        cmd.extend(["--events-jsonl", args.events_jsonl])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    if args.record_event:
        cmd.extend(["--record-event", args.record_event])
        cmd.extend(["--activation-type", args.activation_type])
        cmd.extend(["--outcome", args.outcome])
        cmd.extend(["--failure-type", args.failure_type])
        cmd.extend(["--source", args.source])
        cmd.extend(["--command", args.telemetry_command])
        if args.timestamp:
            cmd.extend(["--timestamp", args.timestamp])
        if args.skill_name:
            cmd.extend(["--skill-name", args.skill_name])
        if args.version:
            cmd.extend(["--version", args.version])
    result = run_script("render_adoption_drift_report.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_telemetry_import(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir, "--input-jsonl", args.input_jsonl]
    if args.events_jsonl:
        cmd.extend(["--events-jsonl", args.events_jsonl])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    if args.source:
        cmd.extend(["--source", args.source])
    if args.telemetry_command:
        cmd.extend(["--command", args.telemetry_command])
    if args.dry_run:
        cmd.append("--dry-run")
    result = run_script("import_telemetry_events.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_telemetry_emit(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [
        skill_dir,
        "--event",
        args.event,
        "--activation-type",
        args.activation_type,
        "--outcome",
        args.outcome,
        "--failure-type",
        args.failure_type,
        "--source",
        args.source,
        "--command",
        args.telemetry_command,
    ]
    if args.output_jsonl:
        cmd.extend(["--output-jsonl", args.output_jsonl])
    if args.timestamp:
        cmd.extend(["--timestamp", args.timestamp])
    if args.skill_name:
        cmd.extend(["--skill-name", args.skill_name])
    if args.version:
        cmd.extend(["--version", args.version])
    if args.dry_run:
        cmd.append("--dry-run")
    result = run_script("emit_telemetry_event.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_telemetry_hooks(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.output_jsonl:
        cmd.extend(["--output-jsonl", args.output_jsonl])
    result = run_script("render_telemetry_hook_recipes.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_review_waivers(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.waivers_json:
        cmd.extend(["--waivers-json", args.waivers_json])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    if args.add_waiver:
        required = {
            "--gate-key": args.gate_key,
            "--reviewer": args.reviewer,
            "--reason": args.reason,
            "--expires-at": args.expires_at,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            print(json.dumps({"ok": False, "failures": [f"Missing required fields for --add-waiver: {', '.join(missing)}"]}, ensure_ascii=False, indent=2))
            return 2
        cmd.append("--add-waiver")
        cmd.extend(["--gate-key", args.gate_key])
        cmd.extend(["--decision", args.decision])
        cmd.extend(["--reviewer", args.reviewer])
        cmd.extend(["--reason", args.reason])
        cmd.extend(["--expires-at", args.expires_at])
        if args.created_at:
            cmd.extend(["--created-at", args.created_at])
        if args.evidence:
            cmd.extend(["--evidence", args.evidence])
        if args.scope:
            cmd.extend(["--scope", args.scope])
    result = run_script("render_review_waivers.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_review_annotations(args: argparse.Namespace) -> int:
    skill_dir = str(Path(args.skill_dir).resolve())
    cmd = [skill_dir]
    if args.annotations_json:
        cmd.extend(["--annotations-json", args.annotations_json])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.write_template:
        cmd.append("--write-template")
    if args.add_annotation:
        cmd.append("--add-annotation")
    if args.annotation_id:
        cmd.extend(["--annotation-id", args.annotation_id])
    if args.gate_key:
        cmd.extend(["--gate-key", args.gate_key])
    if args.target_path:
        cmd.extend(["--target-path", args.target_path])
    if args.line is not None:
        cmd.extend(["--line", str(args.line)])
    if args.severity:
        cmd.extend(["--severity", args.severity])
    if args.status:
        cmd.extend(["--status", args.status])
    if args.reviewer:
        cmd.extend(["--reviewer", args.reviewer])
    if args.created_at:
        cmd.extend(["--created-at", args.created_at])
    if args.body:
        cmd.extend(["--body", args.body])
    if args.suggested_action:
        cmd.extend(["--suggested-action", args.suggested_action])
    if args.evidence:
        cmd.extend(["--evidence", args.evidence])
    result = run_script("render_review_annotations.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_baseline_compare(args: argparse.Namespace) -> int:
    result = run_script("render_baseline_compare.py", baseline_compare_args())
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_review(args: argparse.Namespace) -> int:
    target_name = resolve_promotion_target(args.target)
    bundle_dir = ROOT / "reports" / "iteration_bundles" / target_name
    report = {
        "ok": (bundle_dir / "bundle.json").exists() and (bundle_dir / "review.md").exists(),
        "target": target_name,
        "artifacts": {
            "bundle_json": str((bundle_dir / "bundle.json").relative_to(ROOT)),
            "bundle_md": str((bundle_dir / "bundle.md").relative_to(ROOT)),
            "review_md": str((bundle_dir / "review.md").relative_to(ROOT)),
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def command_release_snapshot(args: argparse.Namespace) -> int:
    target_name = resolve_promotion_target(args.target)
    result = run_script(
        "create_iteration_snapshot.py",
        [
            "--target",
            target_name,
            "--label",
            args.label,
        ],
    )
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_workspace_flow(args: argparse.Namespace) -> int:
    selected_targets = (
        ["root", "team-frontend-review", "governed-incident-command"]
        if args.target == "all"
        else [args.target]
    )
    steps = []
    snapshot_artifacts = []

    for target in selected_targets:
        steps.append(
            {
                "phase": "optimize-description",
                "target": target,
                "result": run_script("optimize_description.py", optimize_args_for_target(target, True)),
            }
        )

    steps.extend(
        [
            {"phase": "route-scorecard", "result": run_script("build_confusion_matrix.py", [])},
            {"phase": "promotion-check", "result": run_script("promotion_checker.py", [])},
            {"phase": "report-refresh", "result": run_script("render_eval_dashboard.py", [])},
            {"phase": "report-refresh", "result": run_script("render_description_drift_history.py", [])},
            {"phase": "report-refresh", "result": run_script("render_iteration_ledger.py", [])},
            {"phase": "report-refresh", "result": run_script("render_baseline_compare.py", baseline_compare_args())},
            {"phase": "report-refresh", "result": run_script("render_regression_history.py", [])},
            {"phase": "report-refresh", "result": run_script("render_context_reports.py", [])},
            {"phase": "report-refresh", "result": run_script("render_portability_report.py", [])},
            {"phase": "report-refresh", "result": run_script("python_compat_check.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_architecture_maintainability.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("compile_skill.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_adoption_drift_if_source_exists()},
            {"phase": "report-refresh", "result": run_script("render_telemetry_hook_recipes.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_review_waivers.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_review_annotations.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_world_class_evidence_plan.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_world_class_evidence_ledger.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_world_class_evidence_intake.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_world_class_submission_review.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_world_class_operator_runbook.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_world_class_claim_guard.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_skill_os2_coverage.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_benchmark_reproducibility.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_skill_overview.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_review_viewer.py", [str(ROOT)])},
        ]
    )

    for target in selected_targets:
        review_target = resolve_promotion_target(target)
        review_info = {
            "bundle_json": f"reports/iteration_bundles/{review_target}/bundle.json",
            "bundle_md": f"reports/iteration_bundles/{review_target}/bundle.md",
            "review_md": f"reports/iteration_bundles/{review_target}/review.md",
        }
        snapshot = run_script(
            "create_iteration_snapshot.py",
            [
                "--target",
                review_target,
                "--label",
                args.label,
            ],
        )
        snapshot_artifacts.append(
            {
                "target": review_target,
                "review": review_info,
                "snapshot": snapshot["payload"] if snapshot["payload"] is not None else snapshot,
            }
        )
        steps.append({"phase": "release-snapshot", "target": review_target, "result": snapshot})

    report = {
        "ok": all(step["result"]["ok"] for step in steps),
        "target": args.target,
        "label": args.label,
        "steps": [
            {
                "phase": step["phase"],
                **({"target": step["target"]} if "target" in step else {}),
                "command": step["result"]["command"],
                "ok": step["result"]["ok"],
                "returncode": step["result"]["returncode"],
            }
            for step in steps
        ],
        "artifacts": snapshot_artifacts,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def command_test(args: argparse.Namespace) -> int:
    proc = subprocess.run(
        ["make", args.target],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    report = {
        "ok": proc.returncode == 0,
        "target": args.target,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def command_check_update(args: argparse.Namespace) -> int:
    cmd = []
    if args.force:
        cmd.append("--force")
    if args.no_cache:
        cmd.append("--no-cache")
    if args.version_url:
        cmd.extend(["--version-url", args.version_url])
    if args.manifest_url:
        cmd.extend(["--manifest-url", args.manifest_url])
    if args.timeout is not None:
        cmd.extend(["--timeout", str(args.timeout)])
    if args.allow_custom_update_url:
        cmd.append("--allow-custom-update-url")
    result = run_script("check_update.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = build_cli_parser({name: value for name, value in globals().items() if name.startswith("command_")})
    add_telemetry_args(parser)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    returncode = 2
    try:
        returncode = args.func(args)
    finally:
        maybe_record_cli_event(ROOT, args, returncode)
    raise SystemExit(returncode)


if __name__ == "__main__":
    main()
