#!/usr/bin/env python3
"""Operating-loop command declarations for the Yao CLI parser."""

import argparse
from collections.abc import Callable


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by yao_cli_parser.py to keep SkillOps, telemetry, and review-loop command declarations out of the main parser module."


TELEMETRY_EVENT_CHOICES = ["review_event", "script_run", "skill_activation", "skill_output"]
TELEMETRY_ACTIVATION_CHOICES = ["explicit", "implicit", "manual", "unknown"]
TELEMETRY_OUTCOME_CHOICES = ["accepted", "edited", "failed", "missed", "rejected", "reviewed", "unknown"]
TELEMETRY_FAILURE_CHOICES = [
    "bad_output",
    "missing_resource",
    "none",
    "review_overdue",
    "script_error",
    "under_trigger",
    "wrong_trigger",
]
TELEMETRY_SOURCE_CHOICES = ["external", "manual", "unknown", "yao_cli"]

REVIEW_WAIVER_GATE_CHOICES = [
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
]

REVIEW_ANNOTATION_GATE_CHOICES = [
    *REVIEW_WAIVER_GATE_CHOICES[:8],
    "review-waivers",
    *REVIEW_WAIVER_GATE_CHOICES[8:12],
    "world-class-evidence",
    *REVIEW_WAIVER_GATE_CHOICES[12:],
]


def _handler(command_handlers: dict[str, Callable[[argparse.Namespace], int]], name: str) -> Callable[[argparse.Namespace], int]:
    if name not in command_handlers:
        raise KeyError(f"Missing CLI command handler: {name}")
    return command_handlers[name]


def _add_telemetry_metadata_arguments(
    command: argparse.ArgumentParser,
    *,
    source_default: str,
    command_default: str,
    activation_default: str,
    event_flag: str | None = None,
    event_default: str | None = None,
) -> None:
    if event_flag is not None:
        kwargs = {"choices": TELEMETRY_EVENT_CHOICES}
        if event_default is not None:
            kwargs["default"] = event_default
        command.add_argument(event_flag, **kwargs)
    command.add_argument("--activation-type", choices=TELEMETRY_ACTIVATION_CHOICES, default=activation_default)
    command.add_argument("--outcome", choices=TELEMETRY_OUTCOME_CHOICES, default="unknown")
    command.add_argument("--failure-type", choices=TELEMETRY_FAILURE_CHOICES, default="none")
    command.add_argument("--source", choices=TELEMETRY_SOURCE_CHOICES, default=source_default)
    command.add_argument("--command", dest="telemetry_command", default=command_default)
    command.add_argument("--timestamp")
    command.add_argument("--skill-name")
    command.add_argument("--version")


def add_operating_loop_commands(
    subparsers: argparse._SubParsersAction,
    command_handlers: dict[str, Callable[[argparse.Namespace], int]],
) -> None:
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

    daily_skillops_cmd = subparsers.add_parser(
        "daily-skillops",
        help="Render a Daily SkillOps report from explicit-source adaptive evidence without scanning private logs or applying patches.",
    )
    daily_skillops_cmd.add_argument("skill_dir", nargs="?", default=".")
    daily_skillops_cmd.add_argument("--source")
    daily_skillops_cmd.add_argument("--patterns-json", default="reports/user_patterns.json")
    daily_skillops_cmd.add_argument("--proposals-json", default="reports/adaptation_proposals.json")
    daily_skillops_cmd.add_argument("--output-json")
    daily_skillops_cmd.add_argument("--output-md")
    daily_skillops_cmd.add_argument("--min-support", type=int, default=2)
    daily_skillops_cmd.add_argument("--generated-at")
    daily_skillops_cmd.add_argument("--allow-history-source", action="store_true")
    daily_skillops_cmd.add_argument("--no-refresh-source-reports", action="store_true")
    daily_skillops_cmd.set_defaults(func=_handler(command_handlers, "command_daily_skillops"))

    weekly_curator_cmd = subparsers.add_parser(
        "weekly-curator",
        help="Render a weekly SkillOps curator report from generated daily reports and portfolio evidence.",
    )
    weekly_curator_cmd.add_argument("skill_dir", nargs="?", default=".")
    weekly_curator_cmd.add_argument("--daily-json", action="append", default=[])
    weekly_curator_cmd.add_argument("--output-json")
    weekly_curator_cmd.add_argument("--output-md")
    weekly_curator_cmd.add_argument("--generated-at")
    weekly_curator_cmd.set_defaults(func=_handler(command_handlers, "command_weekly_curator"))

    adoption_drift_cmd = subparsers.add_parser(
        "adoption-drift",
        help="Render local-first metadata-only adoption and drift telemetry for a skill package.",
    )
    adoption_drift_cmd.add_argument("skill_dir", nargs="?", default=".")
    adoption_drift_cmd.add_argument("--events-jsonl")
    adoption_drift_cmd.add_argument("--output-json")
    adoption_drift_cmd.add_argument("--output-md")
    adoption_drift_cmd.add_argument("--generated-at")
    _add_telemetry_metadata_arguments(
        adoption_drift_cmd,
        event_flag="--record-event",
        source_default="manual",
        command_default="unknown",
        activation_default="unknown",
    )
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
    telemetry_import_cmd.add_argument("--source", choices=TELEMETRY_SOURCE_CHOICES, default="external")
    telemetry_import_cmd.add_argument("--command", dest="telemetry_command", default="external-client")
    telemetry_import_cmd.add_argument("--dry-run", action="store_true")
    telemetry_import_cmd.set_defaults(func=_handler(command_handlers, "command_telemetry_import"))

    telemetry_emit_cmd = subparsers.add_parser(
        "telemetry-emit",
        help="Emit one metadata-only telemetry event for later import.",
    )
    telemetry_emit_cmd.add_argument("skill_dir", nargs="?", default=".")
    telemetry_emit_cmd.add_argument("--output-jsonl")
    _add_telemetry_metadata_arguments(
        telemetry_emit_cmd,
        event_flag="--event",
        event_default="script_run",
        source_default="external",
        command_default="external-client",
        activation_default="manual",
    )
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
    review_waivers_cmd.add_argument("--gate-key", choices=REVIEW_WAIVER_GATE_CHOICES)
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
    review_annotations_cmd.add_argument("--gate-key", choices=REVIEW_ANNOTATION_GATE_CHOICES)
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
