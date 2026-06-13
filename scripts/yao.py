#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path

from yao_cli_config import (
    baseline_compare_args,
    local_output_runner_command,
    provider_output_runner_command,
    resolve_promotion_target,
    resolve_target,
)
from yao_cli_create_commands import command_init, command_quickstart
from yao_cli_parser import build_parser as build_cli_parser
from yao_cli_report_commands import (
    command_artifact_design_profile,
    command_benchmark_reproducibility,
    command_github_benchmark_scan,
    command_intent_confidence,
    command_intent_dialogue,
    command_iteration_directions,
    command_output_risk_profile,
    command_prompt_quality_profile,
    command_reference_scan,
    command_reference_synthesis,
    command_review_studio,
    command_review_viewer,
    command_skill_os2_audit,
    command_skill_os2_coverage,
    command_skill_report,
    command_system_model,
    command_world_class_claim_guard,
    command_world_class_evidence,
    command_world_class_intake,
    command_world_class_ledger,
    command_world_class_submission_kit,
)
from yao_cli_runtime import ROOT, run_script
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


def command_report(args: argparse.Namespace) -> int:
    steps = []
    if args.refresh_optimization:
        steps.append(run_script("run_description_optimization_suite.py", []))
    steps.extend(
        [
            run_script("build_confusion_matrix.py", []),
            run_script("promotion_checker.py", []),
            run_script("render_eval_dashboard.py", []),
            run_script("render_intent_confidence.py", [str(ROOT)]),
            run_script("render_description_drift_history.py", []),
            run_script("render_iteration_ledger.py", []),
            run_script("render_baseline_compare.py", baseline_compare_args()),
            run_script("render_regression_history.py", []),
            run_script("render_context_reports.py", []),
            run_script("render_portability_report.py", []),
            run_script("python_compat_check.py", [str(ROOT)]),
            run_script("render_architecture_maintainability.py", [str(ROOT)]),
            run_script("render_reference_synthesis.py", [str(ROOT)]),
            run_script("render_artifact_design_profile.py", [str(ROOT)]),
            run_script("render_prompt_quality_profile.py", [str(ROOT)]),
            run_script("render_system_model.py", [str(ROOT)]),
            run_script("compile_skill.py", [str(ROOT)]),
            run_script("run_output_eval.py", []),
            run_script("run_output_execution.py", ["--runner-command", local_output_runner_command()]),
            run_script("adjudicate_output_review.py", []),
            run_script("render_adoption_drift_report.py", [str(ROOT)]),
            run_script("render_telemetry_hook_recipes.py", [str(ROOT)]),
            run_script("render_review_waivers.py", [str(ROOT)]),
            run_script("render_review_annotations.py", [str(ROOT)]),
            run_script("render_world_class_evidence_plan.py", [str(ROOT)]),
            run_script("render_world_class_evidence_ledger.py", [str(ROOT)]),
            run_script("render_world_class_evidence_intake.py", [str(ROOT)]),
            run_script("render_world_class_claim_guard.py", [str(ROOT)]),
            run_script("render_benchmark_reproducibility.py", [str(ROOT)]),
            run_script("render_skill_os2_coverage.py", [str(ROOT)]),
        ]
    )
    report = {
        "ok": all(step["ok"] for step in steps),
        "steps": [{"command": step["command"], "ok": step["ok"], "returncode": step["returncode"]} for step in steps],
        "artifacts": {
            "eval_results": "reports/eval_suite.json",
            "route_scorecard": "reports/route_scorecard.json",
            "promotion_decisions": "reports/promotion_decisions.json",
            "intent_confidence": "reports/intent-confidence.json",
            "iteration_ledger": "reports/iteration_ledger.md",
            "baseline_compare": "reports/baseline-compare.json",
            "regression_history": "reports/regression_history.md",
            "context_budget": "reports/context_budget.json",
            "portability_score": "reports/portability_score.json",
            "python_compatibility": "reports/python_compatibility.json",
            "architecture_maintainability": "reports/architecture_maintainability.json",
            "reference_synthesis": "reports/reference-synthesis.json",
            "artifact_design_profile": "reports/artifact-design-profile.json",
            "prompt_quality_profile": "reports/prompt-quality-profile.json",
            "system_model": "reports/system-model.json",
            "compiled_targets": "reports/compiled_targets.json",
            "output_execution": "reports/output_execution_runs.json",
            "output_review_adjudication": "reports/output_review_adjudication.json",
            "adoption_drift": "reports/adoption_drift_report.json",
            "telemetry_hooks": "reports/telemetry_hook_recipes.json",
            "review_waivers": "reports/review_waivers.json",
            "review_annotations": "reports/review_annotations.json",
            "world_class_evidence_plan": "reports/world_class_evidence_plan.json",
            "world_class_evidence_ledger": "reports/world_class_evidence_ledger.json",
            "world_class_evidence_intake": "reports/world_class_evidence_intake.json",
            "world_class_claim_guard": "reports/world_class_claim_guard.json",
            "benchmark_reproducibility": "reports/benchmark_reproducibility.json",
            "skill_os2_coverage": "reports/skill_os2_coverage.json",
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


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


def command_skill_ir(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.validate_only:
        cmd.append("--validate-only")
    result = run_script("export_skill_ir.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_compile_skill(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    for target in args.target or []:
        cmd.extend(["--target", target])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    result = run_script("compile_skill.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_output_eval(args: argparse.Namespace) -> int:
    cmd = []
    if args.cases:
        cmd.extend(["--cases", args.cases])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.blind_pack_json:
        cmd.extend(["--blind-pack-json", args.blind_pack_json])
    if args.blind_pack_md:
        cmd.extend(["--blind-pack-md", args.blind_pack_md])
    if args.blind_answer_key_json:
        cmd.extend(["--blind-answer-key-json", args.blind_answer_key_json])
    result = run_script("run_output_eval.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_output_execution(args: argparse.Namespace) -> int:
    cmd = []
    if args.cases:
        cmd.extend(["--cases", args.cases])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.runner_command and args.provider_runner:
        payload = {
            "schema_version": "1.0",
            "ok": False,
            "failures": ["Use either --runner-command or --provider-runner, not both."],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 2
    if args.provider_runner:
        cmd.extend(
            [
                "--runner-command",
                provider_output_runner_command(
                    args.provider_runner,
                    model=args.provider_model,
                    base_url=args.provider_base_url,
                    api_key_env=args.api_key_env,
                    allow_insecure_localhost=args.allow_insecure_localhost,
                    allow_custom_base_url=args.allow_custom_base_url,
                ),
            ]
        )
    elif args.runner_command:
        cmd.extend(["--runner-command", args.runner_command])
    if args.timeout_seconds is not None:
        cmd.extend(["--timeout-seconds", str(args.timeout_seconds)])
    result = run_script("run_output_execution.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_output_review(args: argparse.Namespace) -> int:
    cmd = []
    if args.blind_pack:
        cmd.extend(["--blind-pack", args.blind_pack])
    if args.answer_key:
        cmd.extend(["--answer-key", args.answer_key])
    if args.decisions:
        cmd.extend(["--decisions", args.decisions])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.write_template:
        cmd.append("--write-template")
    result = run_script("adjudicate_output_review.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_conformance(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    for target in args.target or []:
        cmd.extend(["--target", target])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    result = run_script("run_conformance_suite.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_runtime_permissions(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.package_dir:
        cmd.extend(["--package-dir", args.package_dir])
    for target in args.target or []:
        cmd.extend(["--target", target])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    result = run_script("probe_runtime_permissions.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_trust(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    result = run_script("trust_check.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_skill_atlas(args: argparse.Namespace) -> int:
    cmd = ["--workspace-root", str(Path(args.workspace_root).resolve())]
    if args.output_dir:
        cmd.extend(["--output-dir", args.output_dir])
    if args.report_html:
        cmd.extend(["--report-html", args.report_html])
    if args.report_json:
        cmd.extend(["--report-json", args.report_json])
    if args.overlap_threshold is not None:
        cmd.extend(["--overlap-threshold", str(args.overlap_threshold)])
    if args.today:
        cmd.extend(["--today", args.today])
    result = run_script("build_skill_atlas.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_registry_audit(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.registry_dir:
        cmd.extend(["--registry-dir", args.registry_dir])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    result = run_script("registry_audit.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_package_verify(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.package_dir:
        cmd.extend(["--package-dir", args.package_dir])
    if args.expectations:
        cmd.extend(["--expectations", args.expectations])
    if args.registry_json:
        cmd.extend(["--registry-json", args.registry_json])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.require_zip:
        cmd.append("--require-zip")
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    result = run_script("verify_package.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_install_simulate(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    if args.package_dir:
        cmd.extend(["--package-dir", args.package_dir])
    if args.install_root:
        cmd.extend(["--install-root", args.install_root])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    result = run_script("simulate_install.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def command_upgrade_check(args: argparse.Namespace) -> int:
    cmd = [str(Path(args.skill_dir).resolve())]
    cmd.extend(["--previous-package-json", args.previous_package_json])
    if args.current_package_json:
        cmd.extend(["--current-package-json", args.current_package_json])
    if args.output_json:
        cmd.extend(["--output-json", args.output_json])
    if args.output_md:
        cmd.extend(["--output-md", args.output_md])
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    result = run_script("upgrade_check.py", cmd)
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
            {"phase": "report-refresh", "result": run_script("render_adoption_drift_report.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_telemetry_hook_recipes.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_review_waivers.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_review_annotations.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_world_class_evidence_plan.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_world_class_evidence_ledger.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_world_class_evidence_intake.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_world_class_claim_guard.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_benchmark_reproducibility.py", [str(ROOT)])},
            {"phase": "report-refresh", "result": run_script("render_skill_os2_coverage.py", [str(ROOT)])},
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


def command_package(args: argparse.Namespace) -> int:
    cmd = [
        str(Path(args.skill_dir).resolve()),
        "--output-dir",
        args.output_dir,
    ]
    for platform in args.platform or ["generic"]:
        cmd.extend(["--platform", platform])
    if args.expectations:
        cmd.extend(["--expectations", args.expectations])
    if args.zip:
        cmd.append("--zip")
    result = run_script("cross_packager.py", cmd)
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


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
