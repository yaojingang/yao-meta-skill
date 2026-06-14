"""Report and evidence command handlers for the Yao CLI."""

import argparse
import json
from pathlib import Path

from yao_cli_runtime import run_script


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


def command_skill_report(args: argparse.Namespace) -> int:
    return render_skill_report_command(args, "render_skill_overview.py", markdown=False)


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
