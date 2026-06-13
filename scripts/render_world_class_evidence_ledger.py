#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from render_world_class_evidence_plan import build_plan


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Renders a machine-checkable ledger for world-class external and human evidence gaps."


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


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
    "native-permission-enforcement": ["real target or installer guard", "native enforcement flag", "residual risk retained for fallback targets"],
    "native-client-telemetry": ["real external client source", "metadata-only event", "local-first import path"],
}


def build_entry(skill_dir: Path, task: dict[str, Any]) -> dict[str, Any]:
    state = STATE_LOADERS.get(task["key"], lambda _: {"accepted": task["status"] == "pass"})(skill_dir)
    accepted = bool(state.get("accepted"))
    return {
        "key": task["key"],
        "label": task["label"],
        "category": task["category"],
        "owner": task["owner"],
        "status": "accepted" if accepted else "pending",
        "source_status": task["status"],
        "current": task["current"],
        "objective": task["objective"],
        "provenance_requirements": PROVENANCE_REQUIREMENTS.get(task["key"], ["release reviewer evidence"]),
        "success_checks": task["success_checks"],
        "evidence_artifacts": task["evidence_artifacts"],
        "privacy_contract": task["privacy_contract"],
        "observed_state": state,
        "anti_overclaim": {
            "planned_work_counts_as_evidence": False,
            "metadata_fallback_counts_as_native_enforcement": False,
            "pending_review_counts_as_human_decision": False,
            "local_command_runner_counts_as_provider_model": False,
        },
        "next_action": task["audit_next_action"],
    }


def build_ledger(skill_dir: Path, generated_at: str) -> dict[str, Any]:
    plan = build_plan(skill_dir, generated_at)
    entries = [build_entry(skill_dir, task) for task in plan["tasks"]]
    accepted_count = sum(1 for entry in entries if entry["status"] == "accepted")
    pending_count = len(entries) - accepted_count
    human_pending_count = sum(1 for entry in entries if entry["category"] == "human" and entry["status"] == "pending")
    external_pending_count = sum(1 for entry in entries if entry["category"] == "external" and entry["status"] == "pending")
    ready = pending_count == 0 and plan["summary"].get("world_class_ready") is True
    return {
        "schema_version": "1.0",
        "ok": True,
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        "summary": {
            "ledger_entry_count": len(entries),
            "accepted_count": accepted_count,
            "pending_count": pending_count,
            "human_pending_count": human_pending_count,
            "external_pending_count": external_pending_count,
            "overclaim_guard_active": True,
            "ready_to_claim_world_class": ready,
            "decision": "ready-for-completion-audit" if ready else "evidence-pending",
        },
        "entries": entries,
        "source_plan": {
            "json": "reports/world_class_evidence_plan.json",
            "markdown": "reports/world_class_evidence_plan.md",
            "task_count": plan["summary"].get("task_count", 0),
        },
        "artifacts": {
            "json": "reports/world_class_evidence_ledger.json",
            "markdown": "reports/world_class_evidence_ledger.md",
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
        f"- accepted: `{summary['accepted_count']}`",
        f"- pending: `{summary['pending_count']}`",
        f"- human pending: `{summary['human_pending_count']}`",
        f"- external pending: `{summary['external_pending_count']}`",
        f"- overclaim guard active: `{str(summary['overclaim_guard_active']).lower()}`",
        "",
        "This ledger records the current evidence state. It does not treat planned work, metadata fallback, pending review, or local command-runner output as world-class completion evidence.",
        "",
        "## Ledger",
        "",
        "| Evidence | Status | Category | Current | Next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for entry in ledger["entries"]:
        current = str(entry["current"]).replace("|", "\\|")
        action = str(entry["next_action"]).replace("|", "\\|")
        lines.append(f"| `{entry['key']}` | `{entry['status']}` | `{entry['category']}` | {current} | {action} |")
    if not ledger["entries"]:
        lines.append("| `none` | `accepted` | `none` | all evidence collected | none |")
    for entry in ledger["entries"]:
        lines.extend(["", f"## {entry['label']}", ""])
        lines.append(f"- objective: {entry['objective']}")
        lines.append(f"- source status: `{entry['source_status']}`")
        lines.append(f"- observed state: `{json.dumps(entry['observed_state'], ensure_ascii=False)}`")
        lines.extend(["", "### Provenance Requirements", ""])
        lines.extend(f"- {item}" for item in entry["provenance_requirements"])
        lines.extend(["", "### Success Checks", ""])
        lines.extend(f"- {item}" for item in entry["success_checks"])
        lines.extend(["", "### Privacy Contract", ""])
        lines.extend(f"- {item}" for item in entry["privacy_contract"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a world-class evidence ledger.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-json", default="reports/world_class_evidence_ledger.json")
    parser.add_argument("--output-md", default="reports/world_class_evidence_ledger.md")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    ledger = build_ledger(skill_dir, args.generated_at)
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
