#!/usr/bin/env python3
"""Argparse surface for the Yao CLI."""

import argparse
from collections.abc import Callable


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by yao.py to keep CLI parser declarations separate from command orchestration."


def _handler(command_handlers: dict[str, Callable[[argparse.Namespace], int]], name: str) -> Callable[[argparse.Namespace], int]:
    if name not in command_handlers:
        raise KeyError(f"Missing CLI command handler: {name}")
    return command_handlers[name]


def build_parser(command_handlers: dict[str, Callable[[argparse.Namespace], int]]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified authoring CLI for yao-meta-skill.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_cmd = subparsers.add_parser("init", help="Initialize a minimal skill package.")
    init_cmd.add_argument("name")
    init_cmd.add_argument("--description", default="Describe what the skill does and when to use it.")
    init_cmd.add_argument("--title")
    init_cmd.add_argument("--output-dir", default=".")
    init_cmd.add_argument("--mode", choices=["scaffold", "production", "library", "governed"], default="scaffold")
    init_cmd.add_argument("--archetype", choices=["scaffold", "production", "library", "governed"], default="scaffold")
    init_cmd.add_argument("--external-reference", action="append", default=[])
    init_cmd.add_argument("--user-reference", action="append", default=[])
    init_cmd.add_argument("--local-constraint", action="append", default=[])
    init_cmd.add_argument("--github-query")
    init_cmd.add_argument("--github-top-n", type=int, default=3)
    init_cmd.add_argument("--github-fixture-dir")
    init_cmd.add_argument("--intent-job")
    init_cmd.add_argument("--intent-real-input", action="append", default=[])
    init_cmd.add_argument("--intent-primary-output")
    init_cmd.add_argument("--intent-exclusion", action="append", default=[])
    init_cmd.add_argument("--intent-constraint", action="append", default=[])
    init_cmd.add_argument("--intent-standard", action="append", default=[])
    init_cmd.add_argument("--intent-correction")
    init_cmd.set_defaults(func=_handler(command_handlers, "command_init"))

    quickstart_cmd = subparsers.add_parser(
        "quickstart",
        help="Interactive fast path for creating a scaffold-first skill package.",
    )
    quickstart_cmd.add_argument("--name")
    quickstart_cmd.add_argument("--job")
    quickstart_cmd.add_argument("--real-input", action="append", default=[])
    quickstart_cmd.add_argument("--primary-output")
    quickstart_cmd.add_argument("--description")
    quickstart_cmd.add_argument("--title")
    quickstart_cmd.add_argument("--output-dir", default=".")
    quickstart_cmd.add_argument("--mode", choices=["scaffold", "production", "library", "governed"])
    quickstart_cmd.add_argument("--archetype", choices=["scaffold", "production", "library", "governed"])
    quickstart_cmd.add_argument("--external-reference", action="append", default=[])
    quickstart_cmd.add_argument("--user-reference", action="append", default=[])
    quickstart_cmd.add_argument("--local-constraint", action="append", default=[])
    quickstart_cmd.add_argument("--constraint", action="append", default=[])
    quickstart_cmd.add_argument("--github-query")
    quickstart_cmd.add_argument("--github-top-n", type=int, default=3)
    quickstart_cmd.add_argument("--github-fixture-dir")
    quickstart_cmd.add_argument("--no-update-check", action="store_true")
    quickstart_cmd.set_defaults(func=_handler(command_handlers, "command_quickstart"))

    validate_cmd = subparsers.add_parser("validate", help="Run validate, lint, governance, and resource checks.")
    validate_cmd.add_argument("skill_dir", nargs="?", default=".")
    validate_cmd.add_argument("--require-manifest", action="store_true")
    validate_cmd.set_defaults(func=_handler(command_handlers, "command_validate"))

    optimize_cmd = subparsers.add_parser("optimize-description", help="Optimize description candidates for a target.")
    optimize_cmd.add_argument(
        "--target",
        choices=["root", "team-frontend-review", "governed-incident-command", "all"],
        default="root",
    )
    optimize_cmd.add_argument("--write", action="store_true", help="Write default report artifacts for the target.")
    optimize_cmd.set_defaults(func=_handler(command_handlers, "command_optimize_description"))

    promote_cmd = subparsers.add_parser("promote-check", help="Apply promotion policy and build iteration bundles.")
    promote_cmd.set_defaults(func=_handler(command_handlers, "command_promote_check"))

    python_compat_cmd = subparsers.add_parser(
        "python-compat",
        help="Check Python source compatibility for the supported CI/runtime interpreter.",
    )
    python_compat_cmd.add_argument("skill_dir", nargs="?", default=".")
    python_compat_cmd.add_argument("--path", action="append", default=[])
    python_compat_cmd.add_argument("--target-python", default="3.11")
    python_compat_cmd.add_argument("--output-json")
    python_compat_cmd.add_argument("--output-md")
    python_compat_cmd.add_argument("--generated-at")
    python_compat_cmd.set_defaults(func=_handler(command_handlers, "command_python_compat"))

    architecture_audit_cmd = subparsers.add_parser(
        "architecture-audit",
        help="Render maintainability evidence for large Python files and CLI command surface.",
    )
    architecture_audit_cmd.add_argument("skill_dir", nargs="?", default=".")
    architecture_audit_cmd.add_argument("--output-json")
    architecture_audit_cmd.add_argument("--output-md")
    architecture_audit_cmd.add_argument("--warn-lines", type=int, default=900)
    architecture_audit_cmd.add_argument("--block-lines", type=int, default=1500)
    architecture_audit_cmd.add_argument("--generated-at")
    architecture_audit_cmd.set_defaults(func=_handler(command_handlers, "command_architecture_audit"))

    review_cmd = subparsers.add_parser("review", help="Locate the current bundle and human review stub for a target.")
    review_cmd.add_argument(
        "--target",
        choices=["root", "team-frontend-review", "governed-incident-command"],
        default="root",
    )
    review_cmd.set_defaults(func=_handler(command_handlers, "command_review"))

    snapshot_cmd = subparsers.add_parser("release-snapshot", help="Create a versioned snapshot from current promotion outputs.")
    snapshot_cmd.add_argument(
        "--target",
        choices=["root", "team-frontend-review", "governed-incident-command"],
        default="root",
    )
    snapshot_cmd.add_argument("--label", default="manual")
    snapshot_cmd.set_defaults(func=_handler(command_handlers, "command_release_snapshot"))

    flow_cmd = subparsers.add_parser(
        "workspace-flow",
        help="Run optimize, promotion, review refresh, and release snapshots as one authoring flow.",
    )
    flow_cmd.add_argument(
        "--target",
        choices=["root", "team-frontend-review", "governed-incident-command", "all"],
        default="root",
    )
    flow_cmd.add_argument("--label", default="manual")
    flow_cmd.set_defaults(func=_handler(command_handlers, "command_workspace_flow"))

    report_cmd = subparsers.add_parser("report", help="Render route, iteration, regression, and context reports.")
    report_cmd.add_argument("--refresh-optimization", action="store_true")
    report_cmd.set_defaults(func=_handler(command_handlers, "command_report"))

    skill_report_cmd = subparsers.add_parser("skill-report", help="Render the HTML skill report for a skill package.")
    skill_report_cmd.add_argument("skill_dir", nargs="?", default=".")
    skill_report_cmd.add_argument("--output-html")
    skill_report_cmd.add_argument("--output-json")
    skill_report_cmd.set_defaults(func=_handler(command_handlers, "command_skill_report"))

    skill_interpretation_cmd = subparsers.add_parser(
        "skill-interpretation",
        help="Render the first-class skill interpretation report for a skill package.",
    )
    skill_interpretation_cmd.add_argument("skill_dir", nargs="?", default=".")
    skill_interpretation_cmd.add_argument("--output-html")
    skill_interpretation_cmd.add_argument("--output-json")
    skill_interpretation_cmd.set_defaults(func=_handler(command_handlers, "command_skill_interpretation"))

    review_viewer_cmd = subparsers.add_parser("review-viewer", help="Render a compact HTML review page for a skill package.")
    review_viewer_cmd.add_argument("skill_dir", nargs="?", default=".")
    review_viewer_cmd.add_argument("--output-html")
    review_viewer_cmd.add_argument("--output-json")
    review_viewer_cmd.set_defaults(func=_handler(command_handlers, "command_review_viewer"))

    review_studio_cmd = subparsers.add_parser("review-studio", help="Render Review Studio 2.0 for a skill package.")
    review_studio_cmd.add_argument("skill_dir", nargs="?", default=".")
    review_studio_cmd.add_argument("--output-html")
    review_studio_cmd.add_argument("--output-json")
    review_studio_cmd.set_defaults(func=_handler(command_handlers, "command_review_studio"))

    skill_os2_audit_cmd = subparsers.add_parser(
        "skill-os2-audit",
        help="Render a requirement-by-requirement Skill OS 2.0 completion audit.",
    )
    skill_os2_audit_cmd.add_argument("skill_dir", nargs="?", default=".")
    skill_os2_audit_cmd.add_argument("--output-json")
    skill_os2_audit_cmd.add_argument("--output-md")
    skill_os2_audit_cmd.add_argument("--generated-at")
    skill_os2_audit_cmd.set_defaults(func=_handler(command_handlers, "command_skill_os2_audit"))

    skill_os2_coverage_cmd = subparsers.add_parser(
        "skill-os2-coverage",
        help="Render Skill OS 2.0 blueprint-to-evidence coverage.",
    )
    skill_os2_coverage_cmd.add_argument("skill_dir", nargs="?", default=".")
    skill_os2_coverage_cmd.add_argument("--output-json")
    skill_os2_coverage_cmd.add_argument("--output-md")
    skill_os2_coverage_cmd.add_argument("--generated-at")
    skill_os2_coverage_cmd.set_defaults(func=_handler(command_handlers, "command_skill_os2_coverage"))

    world_class_evidence_cmd = subparsers.add_parser(
        "world-class-evidence",
        help="Render the evidence collection plan for remaining world-class readiness gaps.",
    )
    world_class_evidence_cmd.add_argument("skill_dir", nargs="?", default=".")
    world_class_evidence_cmd.add_argument("--output-json")
    world_class_evidence_cmd.add_argument("--output-md")
    world_class_evidence_cmd.add_argument("--generated-at")
    world_class_evidence_cmd.set_defaults(func=_handler(command_handlers, "command_world_class_evidence"))

    world_class_ledger_cmd = subparsers.add_parser(
        "world-class-ledger",
        help="Render the machine-checkable ledger for world-class evidence gaps.",
    )
    world_class_ledger_cmd.add_argument("skill_dir", nargs="?", default=".")
    world_class_ledger_cmd.add_argument("--output-json")
    world_class_ledger_cmd.add_argument("--output-md")
    world_class_ledger_cmd.add_argument("--submissions-dir")
    world_class_ledger_cmd.add_argument("--generated-at")
    world_class_ledger_cmd.set_defaults(func=_handler(command_handlers, "command_world_class_ledger"))

    world_class_intake_cmd = subparsers.add_parser(
        "world-class-intake",
        help="Validate world-class human and external evidence intake packets.",
    )
    world_class_intake_cmd.add_argument("skill_dir", nargs="?", default=".")
    world_class_intake_cmd.add_argument("--submissions-dir")
    world_class_intake_cmd.add_argument("--output-json")
    world_class_intake_cmd.add_argument("--output-md")
    world_class_intake_cmd.add_argument("--generated-at")
    world_class_intake_cmd.set_defaults(func=_handler(command_handlers, "command_world_class_intake"))

    world_class_submission_kit_cmd = subparsers.add_parser(
        "world-class-submission-kit",
        help="Prepare editable world-class evidence submission drafts.",
    )
    world_class_submission_kit_cmd.add_argument("skill_dir", nargs="?", default=".")
    world_class_submission_kit_cmd.add_argument("--output-dir")
    world_class_submission_kit_cmd.add_argument("--evidence-key", action="append", default=[])
    world_class_submission_kit_cmd.add_argument("--overwrite", action="store_true")
    world_class_submission_kit_cmd.add_argument("--generated-at")
    world_class_submission_kit_cmd.add_argument("--output-html")
    world_class_submission_kit_cmd.set_defaults(func=_handler(command_handlers, "command_world_class_submission_kit"))

    world_class_submission_review_cmd = subparsers.add_parser(
        "world-class-submission-review",
        help="Render a read-only review queue for world-class evidence submissions.",
    )
    world_class_submission_review_cmd.add_argument("skill_dir", nargs="?", default=".")
    world_class_submission_review_cmd.add_argument("--submissions-dir")
    world_class_submission_review_cmd.add_argument("--output-json")
    world_class_submission_review_cmd.add_argument("--output-md")
    world_class_submission_review_cmd.add_argument("--generated-at")
    world_class_submission_review_cmd.set_defaults(func=_handler(command_handlers, "command_world_class_submission_review"))

    world_class_runbook_cmd = subparsers.add_parser(
        "world-class-runbook",
        help="Render an operator runbook for pending world-class evidence.",
    )
    world_class_runbook_cmd.add_argument("skill_dir", nargs="?", default=".")
    world_class_runbook_cmd.add_argument("--submissions-dir")
    world_class_runbook_cmd.add_argument("--output-json")
    world_class_runbook_cmd.add_argument("--output-md")
    world_class_runbook_cmd.add_argument("--output-html")
    world_class_runbook_cmd.add_argument("--generated-at")
    world_class_runbook_cmd.set_defaults(func=_handler(command_handlers, "command_world_class_runbook"))

    world_class_claim_guard_cmd = subparsers.add_parser(
        "world-class-claim-guard",
        help="Scan public claim surfaces for premature world-class completion claims.",
    )
    world_class_claim_guard_cmd.add_argument("skill_dir", nargs="?", default=".")
    world_class_claim_guard_cmd.add_argument("--claim-surface", action="append", default=[])
    world_class_claim_guard_cmd.add_argument("--output-json")
    world_class_claim_guard_cmd.add_argument("--output-md")
    world_class_claim_guard_cmd.add_argument("--generated-at")
    world_class_claim_guard_cmd.set_defaults(func=_handler(command_handlers, "command_world_class_claim_guard"))

    benchmark_reproducibility_cmd = subparsers.add_parser(
        "benchmark-reproducibility",
        help="Render benchmark methodology, artifact, failure-disclosure, and reproduction-command evidence.",
    )
    benchmark_reproducibility_cmd.add_argument("skill_dir", nargs="?", default=".")
    benchmark_reproducibility_cmd.add_argument("--output-json")
    benchmark_reproducibility_cmd.add_argument("--output-md")
    benchmark_reproducibility_cmd.add_argument("--generated-at")
    benchmark_reproducibility_cmd.set_defaults(func=_handler(command_handlers, "command_benchmark_reproducibility"))

    evidence_consistency_cmd = subparsers.add_parser(
        "evidence-consistency",
        help="Render cross-report evidence consistency checks.",
    )
    evidence_consistency_cmd.add_argument("skill_dir", nargs="?", default=".")
    evidence_consistency_cmd.add_argument("--output-json")
    evidence_consistency_cmd.add_argument("--output-md")
    evidence_consistency_cmd.add_argument("--generated-at")
    evidence_consistency_cmd.set_defaults(func=_handler(command_handlers, "command_evidence_consistency"))

    reference_scan_cmd = subparsers.add_parser(
        "reference-scan",
        help="Render a controlled benchmark scan report for a skill package.",
    )
    reference_scan_cmd.add_argument("skill_dir", nargs="?", default=".")
    reference_scan_cmd.add_argument("--reference", action="append", default=[])
    reference_scan_cmd.add_argument("--external-reference", action="append", default=[])
    reference_scan_cmd.add_argument("--user-reference", action="append", default=[])
    reference_scan_cmd.add_argument("--local-constraint", action="append", default=[])
    reference_scan_cmd.add_argument("--output-md")
    reference_scan_cmd.add_argument("--output-json")
    reference_scan_cmd.set_defaults(func=_handler(command_handlers, "command_reference_scan"))

    github_scan_cmd = subparsers.add_parser(
        "github-benchmark-scan",
        help="Search top public GitHub repositories and extract borrow or avoid patterns for a skill.",
    )
    github_scan_cmd.add_argument("skill_dir", nargs="?", default=".")
    github_scan_cmd.add_argument("--query", required=True)
    github_scan_cmd.add_argument("--top-n", type=int, default=3)
    github_scan_cmd.add_argument("--fixture-dir")
    github_scan_cmd.add_argument("--output-md")
    github_scan_cmd.add_argument("--output-json")
    github_scan_cmd.set_defaults(func=_handler(command_handlers, "command_github_benchmark_scan"))

    intent_confidence_cmd = subparsers.add_parser(
        "intent-confidence",
        help="Render a confidence report for how well the real job, inputs, outputs, and exclusions are understood.",
    )
    intent_confidence_cmd.add_argument("skill_dir", nargs="?", default=".")
    intent_confidence_cmd.add_argument("--context-json")
    intent_confidence_cmd.add_argument("--output-md")
    intent_confidence_cmd.add_argument("--output-json")
    intent_confidence_cmd.set_defaults(func=_handler(command_handlers, "command_intent_confidence"))

    intent_dialogue_cmd = subparsers.add_parser(
        "intent-dialogue",
        help="Render a front-loaded intent dialogue guide for a skill package.",
    )
    intent_dialogue_cmd.add_argument("skill_dir", nargs="?", default=".")
    intent_dialogue_cmd.add_argument("--output-md")
    intent_dialogue_cmd.add_argument("--output-json")
    intent_dialogue_cmd.set_defaults(func=_handler(command_handlers, "command_intent_dialogue"))

    reference_synthesis_cmd = subparsers.add_parser(
        "reference-synthesis",
        help="Render a multi-source reference synthesis report for a skill package.",
    )
    reference_synthesis_cmd.add_argument("skill_dir", nargs="?", default=".")
    reference_synthesis_cmd.add_argument("--output-md")
    reference_synthesis_cmd.add_argument("--output-json")
    reference_synthesis_cmd.set_defaults(func=_handler(command_handlers, "command_reference_synthesis"))

    output_risk_cmd = subparsers.add_parser(
        "output-risk-profile",
        help="Render predicted output failure modes and self-repair checks for a skill package.",
    )
    output_risk_cmd.add_argument("skill_dir", nargs="?", default=".")
    output_risk_cmd.add_argument("--output-md")
    output_risk_cmd.add_argument("--output-json")
    output_risk_cmd.set_defaults(func=_handler(command_handlers, "command_output_risk_profile"))

    artifact_design_cmd = subparsers.add_parser(
        "artifact-design-profile",
        help="Render artifact design direction and visual quality gates for a skill package.",
    )
    artifact_design_cmd.add_argument("skill_dir", nargs="?", default=".")
    artifact_design_cmd.add_argument("--output-md")
    artifact_design_cmd.add_argument("--output-json")
    artifact_design_cmd.set_defaults(func=_handler(command_handlers, "command_artifact_design_profile"))

    prompt_quality_cmd = subparsers.add_parser(
        "prompt-quality-profile",
        help="Render prompt-facing need model, RTF mapping, complexity, and quality checks for a skill package.",
    )
    prompt_quality_cmd.add_argument("skill_dir", nargs="?", default=".")
    prompt_quality_cmd.add_argument("--output-md")
    prompt_quality_cmd.add_argument("--output-json")
    prompt_quality_cmd.set_defaults(func=_handler(command_handlers, "command_prompt_quality_profile"))

    system_model_cmd = subparsers.add_parser(
        "system-model",
        help="Render a systems-thinking model for boundaries, feedback loops, drift, and leverage points.",
    )
    system_model_cmd.add_argument("skill_dir", nargs="?", default=".")
    system_model_cmd.add_argument("--output-md")
    system_model_cmd.add_argument("--output-json")
    system_model_cmd.set_defaults(func=_handler(command_handlers, "command_system_model"))

    iteration_directions_cmd = subparsers.add_parser(
        "iteration-directions",
        help="Render the top three next iteration directions for a skill package.",
    )
    iteration_directions_cmd.add_argument("skill_dir", nargs="?", default=".")
    iteration_directions_cmd.add_argument("--output-md")
    iteration_directions_cmd.add_argument("--output-json")
    iteration_directions_cmd.set_defaults(func=_handler(command_handlers, "command_iteration_directions"))

    feedback_cmd = subparsers.add_parser(
        "feedback",
        help="Capture lightweight reviewer feedback without running the full promotion flow.",
    )
    feedback_cmd.add_argument("skill_dir", nargs="?", default=".")
    feedback_cmd.add_argument("--note")
    feedback_cmd.add_argument("--rating", type=int, default=3)
    feedback_cmd.add_argument("--category", default="general")
    feedback_cmd.add_argument("--recommended-action", default="review")
    feedback_cmd.set_defaults(func=_handler(command_handlers, "command_feedback"))

    adapt_scan_cmd = subparsers.add_parser(
        "adapt-scan",
        help="Scan one explicit local source file for redacted repeated user preference signals.",
    )
    adapt_scan_cmd.add_argument("skill_dir", nargs="?", default=".")
    adapt_scan_cmd.add_argument("--source", required=True)
    adapt_scan_cmd.add_argument("--output-json")
    adapt_scan_cmd.add_argument("--output-md")
    adapt_scan_cmd.add_argument("--min-support", type=int, default=2)
    adapt_scan_cmd.add_argument("--generated-at")
    adapt_scan_cmd.add_argument("--allow-history-source", action="store_true")
    adapt_scan_cmd.set_defaults(func=_handler(command_handlers, "command_adapt_scan"))

    adapt_propose_cmd = subparsers.add_parser(
        "adapt-propose",
        help="Create proposal-only adaptation plans from redacted repeated preference patterns.",
    )
    adapt_propose_cmd.add_argument("skill_dir", nargs="?", default=".")
    adapt_propose_cmd.add_argument("--patterns-json")
    adapt_propose_cmd.add_argument("--output-json")
    adapt_propose_cmd.add_argument("--output-md")
    adapt_propose_cmd.add_argument("--generated-at")
    adapt_propose_cmd.set_defaults(func=_handler(command_handlers, "command_adapt_propose"))

    adapt_apply_cmd = subparsers.add_parser(
        "adapt-apply",
        help="Dry-run or apply an approved adaptation patch with allowlist, regression, and rollback evidence.",
    )
    adapt_apply_cmd.add_argument("skill_dir", nargs="?", default=".")
    adapt_apply_cmd.add_argument("--proposal-id")
    adapt_apply_cmd.add_argument("--patch-file")
    adapt_apply_cmd.add_argument("--proposals-json")
    adapt_apply_cmd.add_argument("--approval-ledger")
    adapt_apply_cmd.add_argument("--output-json")
    adapt_apply_cmd.add_argument("--output-md")
    adapt_apply_cmd.add_argument("--generated-at")
    adapt_apply_cmd.add_argument("--today")
    adapt_apply_cmd.add_argument("--write-template", action="store_true")
    adapt_apply_cmd.add_argument("--prepare-approval", action="store_true")
    adapt_apply_cmd.add_argument("--apply", action="store_true")
    adapt_apply_cmd.add_argument("--run-verification", action="store_true")
    adapt_apply_cmd.add_argument(
        "--no-rollback-on-failure",
        dest="rollback_on_failure",
        action="store_false",
        help="Leave an applied patch in place if verification fails. Default is to reverse the patch.",
    )
    adapt_apply_cmd.set_defaults(rollback_on_failure=True)
    adapt_apply_cmd.set_defaults(func=_handler(command_handlers, "command_adapt_apply"))

    adoption_drift_cmd = subparsers.add_parser(
        "adoption-drift",
        help="Render local-first metadata-only adoption and drift telemetry for a skill package.",
    )
    adoption_drift_cmd.add_argument("skill_dir", nargs="?", default=".")
    adoption_drift_cmd.add_argument("--events-jsonl")
    adoption_drift_cmd.add_argument("--output-json")
    adoption_drift_cmd.add_argument("--output-md")
    adoption_drift_cmd.add_argument("--generated-at")
    adoption_drift_cmd.add_argument(
        "--record-event",
        choices=["review_event", "script_run", "skill_activation", "skill_output"],
    )
    adoption_drift_cmd.add_argument(
        "--activation-type",
        choices=["explicit", "implicit", "manual", "unknown"],
        default="unknown",
    )
    adoption_drift_cmd.add_argument(
        "--outcome",
        choices=["accepted", "edited", "failed", "missed", "rejected", "reviewed", "unknown"],
        default="unknown",
    )
    adoption_drift_cmd.add_argument(
        "--failure-type",
        choices=[
            "bad_output",
            "missing_resource",
            "none",
            "review_overdue",
            "script_error",
            "under_trigger",
            "wrong_trigger",
        ],
        default="none",
    )
    adoption_drift_cmd.add_argument("--source", choices=["external", "manual", "unknown", "yao_cli"], default="manual")
    adoption_drift_cmd.add_argument("--command", dest="telemetry_command", default="unknown")
    adoption_drift_cmd.add_argument("--timestamp")
    adoption_drift_cmd.add_argument("--skill-name")
    adoption_drift_cmd.add_argument("--version")
    adoption_drift_cmd.set_defaults(func=_handler(command_handlers, "command_adoption_drift"))

    telemetry_import_cmd = subparsers.add_parser(
        "telemetry-import",
        help="Import external metadata-only telemetry JSONL and refresh the adoption drift report.",
    )
    telemetry_import_cmd.add_argument("skill_dir", nargs="?", default=".")
    telemetry_import_cmd.add_argument("--input-jsonl", required=True)
    telemetry_import_cmd.add_argument("--events-jsonl")
    telemetry_import_cmd.add_argument("--output-json")
    telemetry_import_cmd.add_argument("--output-md")
    telemetry_import_cmd.add_argument("--generated-at")
    telemetry_import_cmd.add_argument("--source", choices=["external", "manual", "unknown", "yao_cli"], default="external")
    telemetry_import_cmd.add_argument("--command", dest="telemetry_command", default="external-client")
    telemetry_import_cmd.add_argument("--dry-run", action="store_true")
    telemetry_import_cmd.set_defaults(func=_handler(command_handlers, "command_telemetry_import"))

    telemetry_emit_cmd = subparsers.add_parser(
        "telemetry-emit",
        help="Emit one metadata-only telemetry event for later import.",
    )
    telemetry_emit_cmd.add_argument("skill_dir", nargs="?", default=".")
    telemetry_emit_cmd.add_argument("--output-jsonl")
    telemetry_emit_cmd.add_argument(
        "--event",
        choices=["review_event", "script_run", "skill_activation", "skill_output"],
        default="script_run",
    )
    telemetry_emit_cmd.add_argument(
        "--activation-type",
        choices=["explicit", "implicit", "manual", "unknown"],
        default="manual",
    )
    telemetry_emit_cmd.add_argument(
        "--outcome",
        choices=["accepted", "edited", "failed", "missed", "rejected", "reviewed", "unknown"],
        default="unknown",
    )
    telemetry_emit_cmd.add_argument(
        "--failure-type",
        choices=[
            "bad_output",
            "missing_resource",
            "none",
            "review_overdue",
            "script_error",
            "under_trigger",
            "wrong_trigger",
        ],
        default="none",
    )
    telemetry_emit_cmd.add_argument("--source", choices=["external", "manual", "unknown", "yao_cli"], default="external")
    telemetry_emit_cmd.add_argument("--command", dest="telemetry_command", default="external-client")
    telemetry_emit_cmd.add_argument("--timestamp")
    telemetry_emit_cmd.add_argument("--skill-name")
    telemetry_emit_cmd.add_argument("--version")
    telemetry_emit_cmd.add_argument("--dry-run", action="store_true")
    telemetry_emit_cmd.set_defaults(func=_handler(command_handlers, "command_telemetry_emit"))

    telemetry_hooks_cmd = subparsers.add_parser(
        "telemetry-hooks",
        help="Render metadata-only telemetry client hook recipes.",
    )
    telemetry_hooks_cmd.add_argument("skill_dir", nargs="?", default=".")
    telemetry_hooks_cmd.add_argument("--output-json")
    telemetry_hooks_cmd.add_argument("--output-md")
    telemetry_hooks_cmd.add_argument("--output-jsonl")
    telemetry_hooks_cmd.set_defaults(func=_handler(command_handlers, "command_telemetry_hooks"))

    review_waivers_cmd = subparsers.add_parser(
        "review-waivers",
        help="Render or update human reviewer waiver evidence for Review Studio.",
    )
    review_waivers_cmd.add_argument("skill_dir", nargs="?", default=".")
    review_waivers_cmd.add_argument("--waivers-json")
    review_waivers_cmd.add_argument("--output-json")
    review_waivers_cmd.add_argument("--output-md")
    review_waivers_cmd.add_argument("--generated-at")
    review_waivers_cmd.add_argument("--add-waiver", action="store_true")
    review_waivers_cmd.add_argument(
        "--gate-key",
        choices=[
            "architecture-maintainability",
            "context-budget",
            "intent-canvas",
            "operations-loop",
            "output-lab",
            "python-compat",
            "registry-audit",
            "release-notes",
            "runtime-matrix",
            "skill-atlas",
            "trigger-lab",
            "trust-report",
            "permission-gates",
            "permission-runtime",
        ],
    )
    review_waivers_cmd.add_argument(
        "--decision",
        choices=["accepted-risk", "false-positive", "temporary-exception"],
        default="accepted-risk",
    )
    review_waivers_cmd.add_argument("--reviewer")
    review_waivers_cmd.add_argument("--reason")
    review_waivers_cmd.add_argument("--expires-at")
    review_waivers_cmd.add_argument("--created-at")
    review_waivers_cmd.add_argument("--evidence")
    review_waivers_cmd.add_argument("--scope", default="current-release")
    review_waivers_cmd.set_defaults(func=_handler(command_handlers, "command_review_waivers"))

    review_annotations_cmd = subparsers.add_parser(
        "review-annotations",
        help="Render or update inline reviewer annotations for Review Studio gates and source paths.",
    )
    review_annotations_cmd.add_argument("skill_dir", nargs="?", default=".")
    review_annotations_cmd.add_argument("--annotations-json")
    review_annotations_cmd.add_argument("--output-json")
    review_annotations_cmd.add_argument("--output-md")
    review_annotations_cmd.add_argument("--write-template", action="store_true")
    review_annotations_cmd.add_argument("--add-annotation", action="store_true")
    review_annotations_cmd.add_argument("--annotation-id")
    review_annotations_cmd.add_argument(
        "--gate-key",
        choices=[
            "architecture-maintainability",
            "context-budget",
            "intent-canvas",
            "operations-loop",
            "output-lab",
            "python-compat",
            "registry-audit",
            "release-notes",
            "review-waivers",
            "runtime-matrix",
            "skill-atlas",
            "trigger-lab",
            "trust-report",
            "world-class-evidence",
            "permission-gates",
            "permission-runtime",
        ],
    )
    review_annotations_cmd.add_argument("--target-path")
    review_annotations_cmd.add_argument("--line", type=int)
    review_annotations_cmd.add_argument("--severity", choices=["blocker", "info", "note", "warning"], default="note")
    review_annotations_cmd.add_argument("--status", choices=["deferred", "open", "resolved"], default="open")
    review_annotations_cmd.add_argument("--reviewer")
    review_annotations_cmd.add_argument("--created-at")
    review_annotations_cmd.add_argument("--body")
    review_annotations_cmd.add_argument("--suggested-action")
    review_annotations_cmd.add_argument("--evidence")
    review_annotations_cmd.set_defaults(func=_handler(command_handlers, "command_review_annotations"))

    baseline_compare_cmd = subparsers.add_parser(
        "baseline-compare",
        help="Render a lightweight with-skill vs baseline comparison across tracked targets.",
    )
    baseline_compare_cmd.set_defaults(func=_handler(command_handlers, "command_baseline_compare"))

    skill_ir_cmd = subparsers.add_parser("skill-ir", help="Export platform-neutral Skill IR for a skill package.")
    skill_ir_cmd.add_argument("skill_dir", nargs="?", default=".")
    skill_ir_cmd.add_argument("--output-json")
    skill_ir_cmd.add_argument("--validate-only", action="store_true")
    skill_ir_cmd.set_defaults(func=_handler(command_handlers, "command_skill_ir"))

    compile_skill_cmd = subparsers.add_parser(
        "compile-skill",
        help="Compile Skill IR into target-specific semantic contracts.",
    )
    compile_skill_cmd.add_argument("skill_dir", nargs="?", default=".")
    compile_skill_cmd.add_argument("--target", action="append")
    compile_skill_cmd.add_argument("--output-json")
    compile_skill_cmd.add_argument("--output-md")
    compile_skill_cmd.add_argument("--generated-at")
    compile_skill_cmd.set_defaults(func=_handler(command_handlers, "command_compile_skill"))

    output_eval_cmd = subparsers.add_parser("output-eval", help="Run Output Eval Lab assertion grading.")
    output_eval_cmd.add_argument("--cases")
    output_eval_cmd.add_argument("--output-json")
    output_eval_cmd.add_argument("--output-md")
    output_eval_cmd.add_argument("--blind-pack-json")
    output_eval_cmd.add_argument("--blind-pack-md")
    output_eval_cmd.add_argument("--blind-answer-key-json")
    output_eval_cmd.set_defaults(func=_handler(command_handlers, "command_output_eval"))

    output_review_kit_cmd = subparsers.add_parser(
        "output-review-kit",
        help="Prepare a reviewer-facing blind A/B output review kit without exposing the answer key.",
    )
    output_review_kit_cmd.add_argument("--blind-pack-json")
    output_review_kit_cmd.add_argument("--blind-pack-md")
    output_review_kit_cmd.add_argument("--decisions")
    output_review_kit_cmd.add_argument("--output-json")
    output_review_kit_cmd.add_argument("--output-md")
    output_review_kit_cmd.add_argument("--output-html")
    output_review_kit_cmd.add_argument("--write-template", action="store_true")
    output_review_kit_cmd.set_defaults(func=_handler(command_handlers, "command_output_review_kit"))

    output_execution_cmd = subparsers.add_parser(
        "output-exec",
        help="Record output-eval execution evidence, timing, and token usage.",
    )
    output_execution_cmd.add_argument("--cases")
    output_execution_cmd.add_argument("--output-json")
    output_execution_cmd.add_argument("--output-md")
    output_execution_cmd.add_argument("--runner-command")
    output_execution_cmd.add_argument(
        "--provider-runner",
        choices=["openai"],
        help="Use the bundled provider-backed runner instead of a custom runner command.",
    )
    output_execution_cmd.add_argument("--provider-model", help="Model for --provider-runner; otherwise use YAO_OUTPUT_EVAL_MODEL.")
    output_execution_cmd.add_argument("--provider-base-url", help="Override provider endpoint for compatible APIs.")
    output_execution_cmd.add_argument("--api-key-env", default="OPENAI_API_KEY")
    output_execution_cmd.add_argument("--allow-insecure-localhost", action="store_true")
    output_execution_cmd.add_argument("--allow-custom-base-url", action="store_true")
    output_execution_cmd.add_argument("--timeout-seconds", type=float)
    output_execution_cmd.set_defaults(func=_handler(command_handlers, "command_output_execution"))

    output_review_cmd = subparsers.add_parser(
        "output-review",
        help="Adjudicate blind A/B output review decisions against the answer key.",
    )
    output_review_cmd.add_argument("--blind-pack")
    output_review_cmd.add_argument("--answer-key")
    output_review_cmd.add_argument("--decisions")
    output_review_cmd.add_argument("--output-json")
    output_review_cmd.add_argument("--output-md")
    output_review_cmd.add_argument("--write-template", action="store_true")
    output_review_cmd.set_defaults(func=_handler(command_handlers, "command_output_review"))

    conformance_cmd = subparsers.add_parser("conformance", help="Run runtime conformance checks for Skill OS targets.")
    conformance_cmd.add_argument("skill_dir", nargs="?", default=".")
    conformance_cmd.add_argument("--target", action="append", choices=["openai", "claude", "agent-skills", "vscode", "generic"])
    conformance_cmd.add_argument("--output-json")
    conformance_cmd.add_argument("--output-md")
    conformance_cmd.set_defaults(func=_handler(command_handlers, "command_conformance"))

    runtime_permissions_cmd = subparsers.add_parser(
        "runtime-permissions",
        help="Probe generated target adapters for runtime permission enforcement metadata.",
    )
    runtime_permissions_cmd.add_argument("skill_dir", nargs="?", default=".")
    runtime_permissions_cmd.add_argument("--package-dir", default="dist")
    runtime_permissions_cmd.add_argument("--target", action="append", choices=["openai", "claude", "generic", "vscode"])
    runtime_permissions_cmd.add_argument("--install-simulation-json")
    runtime_permissions_cmd.add_argument("--output-json")
    runtime_permissions_cmd.add_argument("--output-md")
    runtime_permissions_cmd.set_defaults(func=_handler(command_handlers, "command_runtime_permissions"))

    trust_cmd = subparsers.add_parser("trust", help="Run trust and security checks for a skill package.")
    trust_cmd.add_argument("skill_dir", nargs="?", default=".")
    trust_cmd.add_argument("--output-json")
    trust_cmd.add_argument("--output-md")
    trust_cmd.set_defaults(func=_handler(command_handlers, "command_trust"))

    skill_atlas_cmd = subparsers.add_parser("skill-atlas", help="Build a portfolio-level Skill Atlas for a workspace.")
    skill_atlas_cmd.add_argument("--workspace-root", default=".")
    skill_atlas_cmd.add_argument("--output-dir")
    skill_atlas_cmd.add_argument("--report-html")
    skill_atlas_cmd.add_argument("--report-json")
    skill_atlas_cmd.add_argument("--overlap-threshold", type=float)
    skill_atlas_cmd.add_argument("--today")
    skill_atlas_cmd.set_defaults(func=_handler(command_handlers, "command_skill_atlas"))

    registry_audit_cmd = subparsers.add_parser("registry-audit", help="Build and audit Skill OS registry package metadata.")
    registry_audit_cmd.add_argument("skill_dir", nargs="?", default=".")
    registry_audit_cmd.add_argument("--registry-dir")
    registry_audit_cmd.add_argument("--output-json")
    registry_audit_cmd.add_argument("--output-md")
    registry_audit_cmd.add_argument("--generated-at")
    registry_audit_cmd.set_defaults(func=_handler(command_handlers, "command_registry_audit"))

    package_cmd = subparsers.add_parser("package", help="Export compatibility artifacts for selected targets.")
    package_cmd.add_argument("skill_dir", nargs="?", default=".")
    package_cmd.add_argument("--platform", action="append")
    package_cmd.add_argument("--output-dir", default="dist")
    package_cmd.add_argument("--expectations")
    package_cmd.add_argument("--zip", action="store_true")
    package_cmd.set_defaults(func=_handler(command_handlers, "command_package"))

    package_verify_cmd = subparsers.add_parser("package-verify", help="Verify generated package artifacts, archive safety, and registry parity.")
    package_verify_cmd.add_argument("skill_dir", nargs="?", default=".")
    package_verify_cmd.add_argument("--package-dir", default="dist")
    package_verify_cmd.add_argument("--expectations", default="evals/packaging_expectations.json")
    package_verify_cmd.add_argument("--registry-json", default="reports/registry_audit.json")
    package_verify_cmd.add_argument("--output-json")
    package_verify_cmd.add_argument("--output-md")
    package_verify_cmd.add_argument("--require-zip", action="store_true")
    package_verify_cmd.add_argument("--generated-at")
    package_verify_cmd.set_defaults(func=_handler(command_handlers, "command_package_verify"))

    install_simulate_cmd = subparsers.add_parser("install-simulate", help="Simulate installing a generated package into a temporary local skill root.")
    install_simulate_cmd.add_argument("skill_dir", nargs="?", default=".")
    install_simulate_cmd.add_argument("--package-dir", default="dist")
    install_simulate_cmd.add_argument("--install-root")
    install_simulate_cmd.add_argument("--output-json")
    install_simulate_cmd.add_argument("--output-md")
    install_simulate_cmd.add_argument("--generated-at")
    install_simulate_cmd.set_defaults(func=_handler(command_handlers, "command_install_simulate"))

    upgrade_check_cmd = subparsers.add_parser("upgrade-check", help="Compare current and previous registry package metadata for upgrade readiness.")
    upgrade_check_cmd.add_argument("skill_dir", nargs="?", default=".")
    upgrade_check_cmd.add_argument("--previous-package-json", required=True)
    upgrade_check_cmd.add_argument("--current-package-json", default="reports/registry_audit.json")
    upgrade_check_cmd.add_argument("--output-json")
    upgrade_check_cmd.add_argument("--output-md")
    upgrade_check_cmd.add_argument("--generated-at")
    upgrade_check_cmd.set_defaults(func=_handler(command_handlers, "command_upgrade_check"))

    test_cmd = subparsers.add_parser("test", help="Run a Makefile test target.")
    test_cmd.add_argument("--target", default="test")
    test_cmd.set_defaults(func=_handler(command_handlers, "command_test"))

    update_cmd = subparsers.add_parser("check-update", help="Check whether a newer yao-meta-skill version is available.")
    update_cmd.add_argument("--force", action="store_true")
    update_cmd.add_argument("--no-cache", action="store_true")
    update_cmd.add_argument("--version-url")
    update_cmd.add_argument("--manifest-url")
    update_cmd.add_argument("--timeout", type=float, default=3.0)
    update_cmd.add_argument("--allow-custom-update-url", action="store_true")
    update_cmd.set_defaults(func=_handler(command_handlers, "command_check_update"))

    return parser
