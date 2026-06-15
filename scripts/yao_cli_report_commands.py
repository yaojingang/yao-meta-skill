"""Report and evidence command handlers for the Yao CLI."""

import argparse
import json
from pathlib import Path

from yao_cli_config import baseline_compare_args, local_output_runner_command
from yao_cli_runtime import ROOT, run_script


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by yao.py to keep report and evidence command handlers out of the CLI orchestrator."


def emit_result(result: dict) -> int:
    print(json.dumps(result["payload"] if result["payload"] is not None else result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


def resolved_skill_dir(args: argparse.Namespace) -> str:
    return str(Path(args.skill_dir).resolve())


def append_outputs(cmd: list[str], args: argparse.Namespace, *, markdown: bool = True, generated_at: bool = False) -> None:
    if getattr(args, "output_html", None):
        cmd.extend(["--output-html", args.output_html])
    if getattr(args, "output_json", None):
        cmd.extend(["--output-json", args.output_json])
    if markdown and getattr(args, "output_md", None):
        cmd.extend(["--output-md", args.output_md])
    if generated_at and getattr(args, "generated_at", None):
        cmd.extend(["--generated-at", args.generated_at])


def render_skill_report_command(args: argparse.Namespace, script_name: str, *, markdown: bool = True, generated_at: bool = False) -> int:
    cmd = [resolved_skill_dir(args)]
    append_outputs(cmd, args, markdown=markdown, generated_at=generated_at)
    return emit_result(run_script(script_name, cmd))


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
            run_script("prepare_output_review_kit.py", []),
            run_script("adjudicate_output_review.py", []),
            run_script("render_adoption_drift_report.py", [str(ROOT)]),
            run_script("render_telemetry_hook_recipes.py", [str(ROOT)]),
            run_script("render_review_waivers.py", [str(ROOT)]),
            run_script("render_review_annotations.py", [str(ROOT)]),
            run_script("render_world_class_evidence_plan.py", [str(ROOT)]),
            run_script("render_world_class_evidence_ledger.py", [str(ROOT)]),
            run_script("render_world_class_evidence_intake.py", [str(ROOT)]),
            run_script("render_world_class_submission_review.py", [str(ROOT)]),
            run_script("render_world_class_operator_runbook.py", [str(ROOT)]),
            run_script("render_world_class_claim_guard.py", [str(ROOT)]),
            run_script("render_skill_os2_coverage.py", [str(ROOT)]),
            run_script("render_benchmark_reproducibility.py", [str(ROOT)]),
            run_script("render_skill_overview.py", [str(ROOT)]),
            run_script("render_skill_interpretation.py", [str(ROOT)]),
            run_script("render_evidence_consistency.py", [str(ROOT)]),
            run_script("render_review_viewer.py", [str(ROOT)]),
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
            "output_review_kit": "reports/output_review_kit.json",
            "output_review_kit_html": "reports/output_review_kit.html",
            "output_review_adjudication": "reports/output_review_adjudication.json",
            "adoption_drift": "reports/adoption_drift_report.json",
            "telemetry_hooks": "reports/telemetry_hook_recipes.json",
            "review_waivers": "reports/review_waivers.json",
            "review_annotations": "reports/review_annotations.json",
            "world_class_evidence_plan": "reports/world_class_evidence_plan.json",
            "world_class_evidence_ledger": "reports/world_class_evidence_ledger.json",
            "world_class_evidence_intake": "reports/world_class_evidence_intake.json",
            "world_class_submission_review": "reports/world_class_submission_review.json",
            "world_class_operator_runbook": "reports/world_class_operator_runbook.json",
            "world_class_claim_guard": "reports/world_class_claim_guard.json",
            "skill_os2_coverage": "reports/skill_os2_coverage.json",
            "benchmark_reproducibility": "reports/benchmark_reproducibility.json",
            "skill_overview": "reports/skill-overview.json",
            "skill_interpretation": "reports/skill-interpretation.json",
            "skill_interpretation_html": "reports/skill-interpretation.html",
            "evidence_consistency": "reports/evidence_consistency.json",
            "review_viewer": "reports/review-viewer.json",
            "review_viewer_html": "reports/review-viewer.html",
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 2


def command_skill_report(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_skill_overview.py", markdown=False)


def command_skill_interpretation(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_skill_interpretation.py", markdown=False)


def command_review_viewer(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_review_viewer.py", markdown=False)


def command_review_studio(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_review_studio.py", markdown=False)


def command_skill_os2_audit(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_skill_os2_audit.py", generated_at=True)


def command_skill_os2_coverage(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_skill_os2_coverage.py", generated_at=True)


def command_world_class_evidence(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_world_class_evidence_plan.py", generated_at=True)


def command_world_class_ledger(args: argparse.Namespace) -> int:
    cmd = [resolved_skill_dir(args)]
    if getattr(args, "submissions_dir", None):
        cmd.extend(["--submissions-dir", args.submissions_dir])
    append_outputs(cmd, args, generated_at=True)
    return emit_result(run_script("render_world_class_evidence_ledger.py", cmd))


def command_world_class_intake(args: argparse.Namespace) -> int:
    cmd = [resolved_skill_dir(args)]
    if args.submissions_dir:
        cmd.extend(["--submissions-dir", args.submissions_dir])
    append_outputs(cmd, args, generated_at=True)
    return emit_result(run_script("render_world_class_evidence_intake.py", cmd))


def command_world_class_submission_kit(args: argparse.Namespace) -> int:
    cmd = [resolved_skill_dir(args)]
    if args.output_dir:
        cmd.extend(["--output-dir", args.output_dir])
    for key in args.evidence_key:
        cmd.extend(["--evidence-key", key])
    if args.overwrite:
        cmd.append("--overwrite")
    if args.generated_at:
        cmd.extend(["--generated-at", args.generated_at])
    if args.output_html:
        cmd.extend(["--output-html", args.output_html])
    return emit_result(run_script("prepare_world_class_submission_kit.py", cmd))


def command_world_class_submission_review(args: argparse.Namespace) -> int:
    cmd = [resolved_skill_dir(args)]
    if args.submissions_dir:
        cmd.extend(["--submissions-dir", args.submissions_dir])
    append_outputs(cmd, args, generated_at=True)
    return emit_result(run_script("render_world_class_submission_review.py", cmd))


def command_world_class_runbook(args: argparse.Namespace) -> int:
    cmd = [resolved_skill_dir(args)]
    if args.submissions_dir:
        cmd.extend(["--submissions-dir", args.submissions_dir])
    append_outputs(cmd, args, generated_at=True)
    return emit_result(run_script("render_world_class_operator_runbook.py", cmd))


def command_world_class_claim_guard(args: argparse.Namespace) -> int:
    cmd = [resolved_skill_dir(args)]
    for surface in args.claim_surface:
        cmd.extend(["--claim-surface", surface])
    append_outputs(cmd, args, generated_at=True)
    return emit_result(run_script("render_world_class_claim_guard.py", cmd))


def command_benchmark_reproducibility(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_benchmark_reproducibility.py", generated_at=True)


def command_evidence_consistency(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_evidence_consistency.py", generated_at=True)


def command_reference_scan(args: argparse.Namespace) -> int:
    cmd = [resolved_skill_dir(args)]
    for reference in args.external_reference:
        cmd.extend(["--external-reference", reference])
    for reference in args.user_reference:
        cmd.extend(["--user-reference", reference])
    for constraint in args.local_constraint:
        cmd.extend(["--local-constraint", constraint])
    for reference in args.reference:
        cmd.extend(["--reference", reference])
    append_outputs(cmd, args)
    return emit_result(run_script("render_reference_scan.py", cmd))


def command_github_benchmark_scan(args: argparse.Namespace) -> int:
    cmd = [resolved_skill_dir(args), "--query", args.query, "--top-n", str(args.top_n)]
    if args.fixture_dir:
        cmd.extend(["--fixture-dir", args.fixture_dir])
    append_outputs(cmd, args)
    return emit_result(run_script("github_benchmark_scan.py", cmd))


def command_intent_confidence(args: argparse.Namespace) -> int:
    cmd = [resolved_skill_dir(args)]
    if args.context_json:
        cmd.extend(["--context-json", args.context_json])
    append_outputs(cmd, args)
    return emit_result(run_script("render_intent_confidence.py", cmd))


def command_intent_dialogue(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_intent_dialogue.py")


def command_reference_synthesis(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_reference_synthesis.py")


def command_output_risk_profile(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_output_risk_profile.py")


def command_artifact_design_profile(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_artifact_design_profile.py")


def command_prompt_quality_profile(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_prompt_quality_profile.py")


def command_system_model(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_system_model.py")


def command_iteration_directions(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_iteration_directions.py")
