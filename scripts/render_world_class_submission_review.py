#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from render_world_class_evidence_intake import build_intake
from render_world_class_evidence_ledger import build_ledger
from world_class_source_checks import build_source_checklist, summarize_source_checklist


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Renders a read-only review queue for world-class evidence submissions before ledger acceptance."

TOP_LEVEL_SUMMARY_FIELDS = [
    "decision",
    "ready_to_claim_world_class",
    "review_item_count",
    "accepted_count",
    "awaiting_submission_count",
    "valid_packet_source_incomplete_count",
    "ready_for_ledger_review_count",
    "fix_submission_count",
    "unmatched_submission_count",
    "invalid_submission_count",
    "source_check_count",
    "source_pass_count",
    "source_blocked_count",
    "review_counts_submission_as_completion",
]


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def by_key(items: list[dict[str, Any]], key_name: str = "evidence_key") -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in items:
        key = str(item.get(key_name, ""))
        if key and key not in result:
            result[key] = item
    return result


def top_level_summary_mirrors(summary: dict[str, Any]) -> dict[str, Any]:
    return {key: summary[key] for key in TOP_LEVEL_SUMMARY_FIELDS if key in summary}


def review_state(entry: dict[str, Any], intake_result: dict[str, Any] | None) -> tuple[str, str]:
    if entry.get("status") == "accepted":
        return "accepted", "Ledger already accepts this evidence item."

    submission = entry.get("submission_state", {}) if isinstance(entry.get("submission_state", {}), dict) else {}
    submission_status = str(submission.get("status", "missing"))
    if submission_status == "missing":
        return "awaiting-submission", "No evidence packet has been submitted for review."
    if submission_status in {"invalid-json", "invalid-contract"}:
        return "fix-submission", "Submission exists but fails the ledger submission contract."
    if intake_result is None:
        return "fix-submission", "Submission exists but is missing from the intake validation results."
    if intake_result.get("status") != "pass":
        return "fix-submission", "Submission exists but failed intake validation."

    observed = entry.get("observed_state", {}) if isinstance(entry.get("observed_state", {}), dict) else {}
    if observed.get("accepted") is True:
        return "ready-for-ledger-review", "Submission and source evidence are ready for final ledger review."
    return "source-evidence-incomplete", "Submission packet is valid, but the source evidence checks still do not pass."


def build_item(entry: dict[str, Any], intake_result: dict[str, Any] | None) -> dict[str, Any]:
    state, reason = review_state(entry, intake_result)
    submission = entry.get("submission_state", {}) if isinstance(entry.get("submission_state", {}), dict) else {}
    observed = entry.get("observed_state", {}) if isinstance(entry.get("observed_state", {}), dict) else {}
    source_checklist = build_source_checklist([entry])
    source_summary = summarize_source_checklist(source_checklist)
    return {
        "evidence_key": entry.get("key", ""),
        "label": entry.get("label", entry.get("key", "")),
        "category": entry.get("category", "external"),
        "owner": entry.get("owner", "release reviewer"),
        "ledger_status": entry.get("status", "pending"),
        "submission_status": submission.get("status", "missing"),
        "intake_status": intake_result.get("status", "missing") if intake_result else "missing",
        "source_accepted": observed.get("accepted") is True,
        "review_state": state,
        "blocking_reason": reason,
        "submission_path": submission.get("path", ""),
        "submitted_by": submission.get("submitted_by", ""),
        "submitted_at": submission.get("submitted_at", ""),
        "artifact_ref_count": submission.get("artifact_ref_count", 0),
        "intake_errors": intake_result.get("errors", []) if intake_result else [],
        "observed_state": observed,
        "source_checklist": source_checklist,
        **source_summary,
        "success_checks": entry.get("success_checks", []),
        "privacy_contract": entry.get("privacy_contract", []),
        "next_action": entry.get("next_action", ""),
    }


def build_submission_review(skill_dir: Path, generated_at: str, submissions_dir: Path | None = None) -> dict[str, Any]:
    submissions_dir = submissions_dir or (skill_dir / "evidence" / "world_class" / "submissions")
    ledger = build_ledger(skill_dir, generated_at, submissions_dir=submissions_dir)
    intake = build_intake(skill_dir, generated_at, submissions_dir=submissions_dir)
    intake_by_key = by_key(intake.get("submissions", []))
    entries = ledger.get("entries", [])
    items = [build_item(entry, intake_by_key.get(str(entry.get("key", "")))) for entry in entries]
    known_keys = {str(entry.get("key", "")) for entry in entries}
    unmatched = [item for item in intake.get("submissions", []) if str(item.get("evidence_key", "")) not in known_keys]
    counts: dict[str, int] = {}
    for item in items:
        state = str(item.get("review_state", "unknown"))
        counts[state] = counts.get(state, 0) + 1
    invalid_count = counts.get("fix-submission", 0) + len(unmatched)
    ready_count = counts.get("ready-for-ledger-review", 0)
    accepted_count = counts.get("accepted", 0)
    source_incomplete_count = counts.get("source-evidence-incomplete", 0)
    awaiting_count = counts.get("awaiting-submission", 0)
    source_rows = [row for item in items for row in item.get("source_checklist", [])]
    source_summary = summarize_source_checklist(source_rows)
    if accepted_count == len(items) and items:
        decision = "ledger-complete"
    elif invalid_count:
        decision = "fix-submissions"
    elif ready_count:
        decision = "review-ready"
    elif source_incomplete_count:
        decision = "source-evidence-incomplete"
    else:
        decision = "awaiting-submissions"
    summary = {
        "review_item_count": len(items),
        "accepted_count": accepted_count,
        "awaiting_submission_count": awaiting_count,
        "valid_packet_source_incomplete_count": source_incomplete_count,
        "ready_for_ledger_review_count": ready_count,
        "fix_submission_count": counts.get("fix-submission", 0),
        "unmatched_submission_count": len(unmatched),
        "invalid_submission_count": invalid_count,
        **source_summary,
        "ready_to_claim_world_class": ledger.get("summary", {}).get("ready_to_claim_world_class") is True,
        "review_counts_submission_as_completion": False,
        "decision": decision,
    }
    return {
        "schema_version": "1.0",
        "ok": invalid_count == 0,
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        **top_level_summary_mirrors(summary),
        "summary": summary,
        "report_contract": {
            "schema_version": "1.0",
            "contract": "world-class-submission-review",
            "top_level_mirrors_summary": True,
            "summary_fields": TOP_LEVEL_SUMMARY_FIELDS,
            "source_of_truth": "summary",
        },
        "submissions": {
            "directory": rel_path(submissions_dir, skill_dir),
            "review_counts_submission_as_completion": False,
        },
        "items": items,
        "unmatched_submissions": unmatched,
        "source_reports": {
            "ledger": "reports/world_class_evidence_ledger.json",
            "intake": "reports/world_class_evidence_intake.json",
        },
        "artifacts": {
            "json": "reports/world_class_submission_review.json",
            "markdown": "reports/world_class_submission_review.md",
        },
    }


def render_list(values: list[Any], empty: str) -> list[str]:
    if not values:
        return [f"- {empty}"]
    return [f"- {value}" for value in values]


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# World-Class Submission Review",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- review items: `{summary['review_item_count']}`",
        f"- accepted: `{summary['accepted_count']}`",
        f"- awaiting submission: `{summary['awaiting_submission_count']}`",
        f"- valid packet but source incomplete: `{summary['valid_packet_source_incomplete_count']}`",
        f"- ready for ledger review: `{summary['ready_for_ledger_review_count']}`",
        f"- fix submission: `{summary['fix_submission_count']}`",
        f"- unmatched submissions: `{summary['unmatched_submission_count']}`",
        f"- ready to claim world-class: `{str(summary['ready_to_claim_world_class']).lower()}`",
        f"- review counts submission as completion: `{str(summary['review_counts_submission_as_completion']).lower()}`",
        "",
        "This report is a read-only reviewer queue. It does not accept evidence or make world-class completion true.",
        "",
        "## Queue",
        "",
        "| Evidence | Review state | Intake | Source accepted | Submission | Next action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["items"]:
        source_accepted = str(item.get("source_accepted") is True).lower()
        next_action = str(item.get("next_action", "")).replace("|", "\\|")
        lines.append(
            f"| `{item['evidence_key']}` | `{item['review_state']}` | `{item['intake_status']}` | "
            f"`{source_accepted}` | `{item['submission_status']}` | {next_action} |"
        )
    if report.get("unmatched_submissions"):
        lines.extend(["", "## Unmatched Submissions", ""])
        for item in report["unmatched_submissions"]:
            errors = "; ".join(item.get("errors", [])) or "unknown evidence key"
            lines.append(f"- `{item.get('path', '')}`: {errors}")
    lines.extend(["", "## Details", ""])
    for item in report["items"]:
        lines.extend(
            [
                f"### {item['label']}",
                "",
                f"- review state: `{item['review_state']}`",
                f"- blocking reason: {item['blocking_reason']}",
                f"- ledger status: `{item['ledger_status']}`",
                f"- submission status: `{item['submission_status']}`",
                f"- intake status: `{item['intake_status']}`",
                f"- source accepted: `{str(item['source_accepted']).lower()}`",
                f"- submission path: `{item.get('submission_path') or 'missing'}`",
                "",
                "#### Source Checks",
                "",
                *render_list(
                    [
                        f"{row['label']}: {row['actual']} / {row['expected']} => {row['status']}"
                        for row in item.get("source_checklist", [])
                    ],
                    "No source checks listed.",
                ),
                "",
                "#### Completion Assertions",
                "",
                *render_list(item.get("success_checks", []), "No completion assertions listed."),
                "",
                "#### Intake Errors",
                "",
                *render_list(item.get("intake_errors", []), "No intake errors."),
                "",
                "#### Privacy Contract",
                "",
                *render_list(item.get("privacy_contract", []), "No privacy contract listed."),
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "- A valid submission packet is not accepted evidence by itself.",
            "- Planned work, metadata fallback, pending human review, and local command-runner output still do not count.",
            "- The world-class ledger remains the source of truth for `ready_to_claim_world_class`.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a read-only review queue for world-class evidence submissions.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--submissions-dir")
    parser.add_argument("--output-json", default="reports/world_class_submission_review.json")
    parser.add_argument("--output-md", default="reports/world_class_submission_review.md")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    submissions_dir = Path(args.submissions_dir).resolve() if args.submissions_dir else None
    report = build_submission_review(skill_dir, args.generated_at, submissions_dir=submissions_dir)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    if not output_json.is_absolute():
        output_json = skill_dir / output_json
    if not output_md.is_absolute():
        output_md = skill_dir / output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
