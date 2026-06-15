#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from render_world_class_evidence_plan import build_plan
from world_class_evidence_contract import load_json, load_json_with_status, rel_path, validate_payload
from world_class_source_checks import build_source_checklist, summarize_source_checklist


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Renders a machine-checkable ledger for world-class external and human evidence gaps."


def provider_state(skill_dir: Path) -> dict[str, Any]:
    summary = load_json(skill_dir / "reports" / "output_execution_runs.json").get("summary", {})
    return {
        "model_executed_count": summary.get("model_executed_count", 0),
        "timing_observed_count": summary.get("timing_observed_count", 0),
        "token_observed_count": summary.get("token_observed_count", 0),
        "accepted": (
            summary.get("model_executed_count", 0) > 0
            and summary.get("timing_observed_count", 0) > 0
            and summary.get("token_observed_count", 0) > 0
        ),
    }


def human_state(skill_dir: Path) -> dict[str, Any]:
    summary = load_json(skill_dir / "reports" / "output_review_adjudication.json").get("summary", {})
    return {
        "pair_count": summary.get("pair_count", 0),
        "judgment_count": summary.get("judgment_count", 0),
        "pending_count": summary.get("pending_count", 0),
        "invalid_decision_count": summary.get("invalid_decision_count", 0),
        "answer_revealed_count": summary.get("answer_revealed_count", 0),
        "accepted": (
            summary.get("pair_count", 0) > 0
            and summary.get("pending_count", 0) == 0
            and summary.get("judgment_count", 0) == summary.get("pair_count", 0)
            and summary.get("invalid_decision_count", 0) == 0
        ),
    }


def permission_state(skill_dir: Path) -> dict[str, Any]:
    summary = load_json(skill_dir / "reports" / "runtime_permission_probes.json").get("summary", {})
    return {
        "native_enforcement_count": summary.get("native_enforcement_count", 0),
        "metadata_fallback_count": summary.get("metadata_fallback_count", 0),
        "installer_enforcement_pass_count": summary.get("installer_enforcement_pass_count", 0),
        "installer_permission_failure_count": summary.get("installer_permission_failure_count", 0),
        "installer_enforcement_ready": summary.get("installer_enforcement_ready", False),
        "residual_risk_count": summary.get("residual_risk_count", 0),
        "failure_count": summary.get("failure_count", 0),
        "accepted": summary.get("native_enforcement_count", 0) > 0 and summary.get("failure_count", 0) == 0,
    }


def telemetry_state(skill_dir: Path) -> dict[str, Any]:
    payload = load_json(skill_dir / "reports" / "adoption_drift_report.json")
    summary = payload.get("summary", {})
    source_types = summary.get("source_types", {}) if isinstance(summary.get("source_types", {}), dict) else {}
    privacy = payload.get("privacy_contract", {})
    return {
        "external_source_events": source_types.get("external", 0),
        "adoption_sample_count": summary.get("adoption_sample_count", 0),
        "raw_content_allowed": privacy.get("raw_content_allowed"),
        "risk_band": summary.get("risk_band", "missing"),
        "accepted": (
            source_types.get("external", 0) > 0
            and summary.get("adoption_sample_count", 0) > 0
            and privacy.get("raw_content_allowed") is False
        ),
    }


STATE_LOADERS = {
    "provider-holdout": provider_state,
    "human-adjudication": human_state,
    "native-permission-enforcement": permission_state,
    "native-client-telemetry": telemetry_state,
}

PROVENANCE_REQUIREMENTS = {
    "provider-holdout": ["provider-backed model run", "observed timing", "observed token metadata"],
    "human-adjudication": ["real reviewer identity", "blind A/B decisions", "answer key unopened until decisions exist"],
    "native-permission-enforcement": ["real target client or external installer runtime guard", "native enforcement flag or externally accepted guard proof", "residual risk retained for fallback targets"],
    "native-client-telemetry": ["real external client source", "metadata-only event", "local-first import path"],
}

TOP_LEVEL_SUMMARY_FIELDS = [
    "decision",
    "ready_to_claim_world_class",
    "ledger_entry_count",
    "source_accepted_count",
    "accepted_count",
    "pending_count",
    "human_pending_count",
    "external_pending_count",
    "submitted_entry_count",
    "missing_submission_count",
    "invalid_submission_count",
    "source_check_count",
    "source_pass_count",
    "source_blocked_count",
    "submitted_but_pending_count",
    "source_accepted_without_valid_submission_count",
    "overclaim_guard_active",
]


def top_level_summary_mirrors(summary: dict[str, Any]) -> dict[str, Any]:
    return {key: summary[key] for key in TOP_LEVEL_SUMMARY_FIELDS if key in summary}


def submission_state(skill_dir: Path, task: dict[str, Any], submissions_dir: Path) -> dict[str, Any]:
    key = str(task.get("key", ""))
    path = submissions_dir / f"{key}.json"
    payload, load_status = load_json_with_status(path)
    if load_status != "present":
        return {
            "status": load_status,
            "path": rel_path(path, skill_dir),
            "artifact_ref_count": 0,
            "attested_real_evidence": False,
            "privacy_contract_satisfied": False,
            "ledger_counts_as_completion": False,
        }
    validation = validate_payload(payload, task, path=path, root=skill_dir, template_expected=False)
    refs = payload.get("artifact_refs", [])
    attestation = payload.get("attestation", {}) if isinstance(payload.get("attestation", {}), dict) else {}
    status = "submitted" if validation["status"] == "pass" else "invalid-contract"
    artifact_integrity = validation.get("artifact_integrity", {})
    return {
        "status": status,
        "path": rel_path(path, skill_dir),
        "submitted_by": payload.get("submitted_by", ""),
        "submitted_at": payload.get("submitted_at", ""),
        "artifact_ref_count": len(refs) if isinstance(refs, list) else 0,
        "artifact_existing_count": artifact_integrity.get("artifact_existing_count", 0),
        "artifact_sha256_verified_count": artifact_integrity.get("artifact_sha256_verified_count", 0),
        "attested_real_evidence": attestation.get("real_external_or_human_evidence") is True,
        "reviewer_or_operator_identity_present": attestation.get("reviewer_or_operator_identity_present") is True,
        "privacy_contract_satisfied": attestation.get("privacy_contract_satisfied") is True,
        "errors": validation.get("errors", []),
        "ledger_counts_as_completion": False,
    }


def build_entry(skill_dir: Path, task: dict[str, Any], submissions_dir: Path) -> dict[str, Any]:
    state = STATE_LOADERS.get(task["key"], lambda _: {"accepted": task["status"] == "pass"})(skill_dir)
    submission = submission_state(skill_dir, task, submissions_dir)
    source_checklist = build_source_checklist([{"key": task["key"], "observed_state": state}])
    source_summary = summarize_source_checklist(source_checklist)
    source_accepted = bool(source_checklist) and source_summary["source_blocked_count"] == 0
    accepted = source_accepted and submission.get("status") == "submitted"
    return {
        "key": task["key"],
        "label": task["label"],
        "category": task["category"],
        "owner": task["owner"],
        "status": "accepted" if accepted else "pending",
        "source_status": task["status"],
        "source_accepted": source_accepted,
        "current": task["current"],
        "objective": task["objective"],
        "runbook": task.get("runbook", []),
        "provenance_requirements": PROVENANCE_REQUIREMENTS.get(task["key"], ["release reviewer evidence"]),
        "success_checks": task["success_checks"],
        "evidence_artifacts": task["evidence_artifacts"],
        "privacy_contract": task["privacy_contract"],
        "observed_state": state,
        "source_checklist": source_checklist,
        **source_summary,
        "submission_state": submission,
        "anti_overclaim": {
            "planned_work_counts_as_evidence": False,
            "metadata_fallback_counts_as_native_enforcement": False,
            "pending_review_counts_as_human_decision": False,
            "local_command_runner_counts_as_provider_model": False,
        },
        "next_action": task["audit_next_action"],
    }


def build_ledger(skill_dir: Path, generated_at: str, submissions_dir: Path | None = None) -> dict[str, Any]:
    plan = build_plan(skill_dir, generated_at)
    submissions_dir = submissions_dir or (skill_dir / "evidence" / "world_class" / "submissions")
    evidence_requirements = plan.get("evidence_requirements") or plan.get("tasks", [])
    entries = [build_entry(skill_dir, task, submissions_dir) for task in evidence_requirements]
    source_rows = [row for entry in entries for row in entry.get("source_checklist", [])]
    source_summary = summarize_source_checklist(source_rows)
    source_accepted_count = sum(1 for entry in entries if entry.get("source_accepted") is True)
    accepted_count = sum(1 for entry in entries if entry["status"] == "accepted")
    pending_count = len(entries) - accepted_count
    human_pending_count = sum(1 for entry in entries if entry["category"] == "human" and entry["status"] == "pending")
    external_pending_count = sum(1 for entry in entries if entry["category"] == "external" and entry["status"] == "pending")
    submitted_entry_count = sum(1 for entry in entries if entry["submission_state"]["status"] == "submitted")
    missing_submission_count = sum(1 for entry in entries if entry["submission_state"]["status"] == "missing")
    invalid_submission_count = sum(1 for entry in entries if entry["submission_state"]["status"] in {"invalid-json", "invalid-contract"})
    submitted_but_pending_count = sum(
        1 for entry in entries if entry["submission_state"]["status"] == "submitted" and entry["status"] == "pending"
    )
    source_accepted_without_valid_submission_count = sum(
        1
        for entry in entries
        if entry.get("source_accepted") is True and entry["submission_state"]["status"] != "submitted"
    )
    ready = bool(entries) and pending_count == 0 and plan["summary"].get("world_class_ready") is True
    summary = {
        "ledger_entry_count": len(entries),
        "source_accepted_count": source_accepted_count,
        "accepted_count": accepted_count,
        "pending_count": pending_count,
        "human_pending_count": human_pending_count,
        "external_pending_count": external_pending_count,
        "submitted_entry_count": submitted_entry_count,
        "missing_submission_count": missing_submission_count,
        "invalid_submission_count": invalid_submission_count,
        **source_summary,
        "submitted_but_pending_count": submitted_but_pending_count,
        "source_accepted_without_valid_submission_count": source_accepted_without_valid_submission_count,
        "overclaim_guard_active": True,
        "ready_to_claim_world_class": ready,
        "decision": "ready-for-completion-audit" if ready else "evidence-pending",
    }
    return {
        "schema_version": "1.0",
        "ok": True,
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        **top_level_summary_mirrors(summary),
        "summary": summary,
        "report_contract": {
            "schema_version": "1.0",
            "contract": "world-class-evidence-ledger",
            "top_level_mirrors_summary": True,
            "summary_fields": TOP_LEVEL_SUMMARY_FIELDS,
            "source_of_truth": "summary",
        },
        "entries": entries,
        "source_plan": {
            "json": "reports/world_class_evidence_plan.json",
            "markdown": "reports/world_class_evidence_plan.md",
            "task_count": plan["summary"].get("task_count", 0),
            "evidence_requirement_count": len(evidence_requirements),
        },
        "submissions": {
            "directory": rel_path(submissions_dir, skill_dir),
            "ledger_counts_submission_as_completion": False,
            "source_pass_requires_valid_submission": True,
        },
        "artifacts": {
            "json": "reports/world_class_evidence_ledger.json",
            "markdown": "reports/world_class_evidence_ledger.md",
            "intake": "reports/world_class_evidence_intake.md",
        },
    }


def render_markdown(ledger: dict[str, Any]) -> str:
    summary = ledger["summary"]
    lines = [
        "# World-Class Evidence Ledger",
        "",
        f"Generated at: `{ledger['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- ready to claim world-class: `{str(summary['ready_to_claim_world_class']).lower()}`",
        f"- entries: `{summary['ledger_entry_count']}`",
        f"- source accepted: `{summary.get('source_accepted_count', 0)}`",
        f"- source checks: `{summary.get('source_pass_count', 0)}` pass / `{summary.get('source_check_count', 0)}` total",
        f"- source blocked: `{summary.get('source_blocked_count', 0)}`",
        f"- accepted: `{summary['accepted_count']}`",
        f"- pending: `{summary['pending_count']}`",
        f"- human pending: `{summary['human_pending_count']}`",
        f"- external pending: `{summary['external_pending_count']}`",
        f"- submitted entries: `{summary['submitted_entry_count']}`",
        f"- submitted but pending: `{summary['submitted_but_pending_count']}`",
        f"- source accepted without valid submission: `{summary.get('source_accepted_without_valid_submission_count', 0)}`",
        f"- invalid submissions: `{summary['invalid_submission_count']}`",
        f"- overclaim guard active: `{str(summary['overclaim_guard_active']).lower()}`",
        "",
        "This ledger records the current evidence state. It requires both passing source evidence and a validated intake submission with artifact SHA-256 checks before accepting an item. It does not treat planned work, metadata fallback, pending review, or local command-runner output as world-class completion evidence.",
        "",
        "## Ledger",
        "",
        "| Evidence | Status | Submission | Category | Current | Next action |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in ledger["entries"]:
        current = str(entry["current"]).replace("|", "\\|")
        action = str(entry["next_action"]).replace("|", "\\|")
        submission = entry.get("submission_state", {}).get("status", "missing")
        lines.append(f"| `{entry['key']}` | `{entry['status']}` | `{submission}` | `{entry['category']}` | {current} | {action} |")
    if not ledger["entries"]:
        lines.append("| `none` | `accepted` | `none` | all evidence collected | none |")
    for entry in ledger["entries"]:
        lines.extend(["", f"## {entry['label']}", ""])
        lines.append(f"- objective: {entry['objective']}")
        lines.append(f"- source status: `{entry['source_status']}`")
        lines.append(f"- observed state: `{json.dumps(entry['observed_state'], ensure_ascii=False)}`")
        lines.append(
            f"- source checks: `{entry.get('source_pass_count', 0)}` pass / "
            f"`{entry.get('source_check_count', 0)}` total"
        )
        lines.append(f"- submission state: `{json.dumps(entry.get('submission_state', {}), ensure_ascii=False)}`")
        lines.extend(["", "### Provenance Requirements", ""])
        lines.extend(f"- {item}" for item in entry["provenance_requirements"])
        lines.extend(["", "### Source Runbook", ""])
        lines.extend(f"- `{item}`" if str(item).startswith("python3 ") or "=" in str(item) else f"- {item}" for item in entry.get("runbook", []))
        lines.extend(
            [
                "",
                "### Source Evidence Checks",
                "",
                "| Check | Current | Expected | Status |",
                "| --- | --- | --- | --- |",
            ]
        )
        source_checks = entry.get("source_checklist", [])
        if source_checks:
            for row in source_checks:
                lines.append(
                    f"| {row['label']} | `{row['actual']}` | `{row['expected']}` | `{row['status']}` |"
                )
        else:
            lines.append("| No source checks listed. | `n/a` | `n/a` | `n/a` |")
        lines.extend(["", "### Completion Assertions", ""])
        lines.extend(f"- {item}" for item in entry["success_checks"])
        lines.extend(["", "### Privacy Contract", ""])
        lines.extend(f"- {item}" for item in entry["privacy_contract"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a world-class evidence ledger.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-json", default="reports/world_class_evidence_ledger.json")
    parser.add_argument("--output-md", default="reports/world_class_evidence_ledger.md")
    parser.add_argument("--submissions-dir")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    submissions_dir = Path(args.submissions_dir).resolve() if args.submissions_dir else None
    ledger = build_ledger(skill_dir, args.generated_at, submissions_dir=submissions_dir)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    if not output_json.is_absolute():
        output_json = skill_dir / output_json
    if not output_md.is_absolute():
        output_md = skill_dir / output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(ledger), encoding="utf-8")
    print(json.dumps(ledger, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
