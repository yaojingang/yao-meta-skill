#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Renders a weekly SkillOps curator report from generated reports without scanning private logs or writing source files."

SUMMARY_FIELDS = [
    "decision",
    "week_id",
    "daily_report_count",
    "opportunity_count",
    "unique_opportunity_count",
    "ready_for_approval_review_count",
    "proposal_review_count",
    "observe_more_evidence_count",
    "report_only_count",
    "top_score",
    "skill_count",
    "actionable_portfolio_issue_count",
    "release_lock_ready",
    "evidence_consistency_ok",
    "public_world_class_ready",
    "world_class_pending_count",
    "writes_source_files",
    "auto_patch_enabled",
    "failure_count",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_date(value: str) -> date:
    candidate = value[:10] if len(value) >= 10 else value
    try:
        return date.fromisoformat(candidate)
    except ValueError:
        return date.today()


def week_id(generated_at: str) -> str:
    iso = parse_date(generated_at).isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def display_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return f"[external-explicit-source]/{path.name}"


def resolve_output(skill_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else skill_dir / path


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def default_weekly_path(skill_dir: Path, generated_at: str, suffix: str) -> Path:
    return skill_dir / "reports" / "skillops" / "weekly" / f"{week_id(generated_at)}.{suffix}"


def daily_report_paths(skill_dir: Path, explicit_paths: list[Path]) -> list[Path]:
    if explicit_paths:
        return [path if path.is_absolute() else skill_dir / path for path in explicit_paths]
    daily_dir = skill_dir / "reports" / "skillops" / "daily"
    if not daily_dir.exists():
        return []
    return sorted(daily_dir.glob("*.json"))


def _as_int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _dedupe_opportunities(daily_reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for report in daily_reports:
        report_date = str(report.get("generated_at") or "")[:10]
        for item in report.get("opportunities", []):
            if not isinstance(item, dict):
                continue
            opportunity_id = str(item.get("opportunity_id") or "")
            if not opportunity_id:
                continue
            current = {**item, "daily_report_date": report_date}
            existing = by_id.get(opportunity_id)
            if existing is None or _as_int(current.get("score")) > _as_int(existing.get("score")):
                by_id[opportunity_id] = current
    return sorted(by_id.values(), key=lambda item: (-_as_int(item.get("score")), str(item.get("opportunity_id"))))


def _counter(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    values = Counter(str(item.get(key) or "") for item in items)
    values.pop("", None)
    return dict(sorted(values.items()))


def _portfolio_issue_count(atlas_summary: dict[str, Any]) -> int:
    keys = [
        "actionable_route_collision_count",
        "actionable_owner_gap_count",
        "actionable_stale_count",
        "actionable_drift_signal_count",
        "no_route_opportunity_count",
    ]
    return sum(_as_int(atlas_summary.get(key)) for key in keys)


def build_actions(summary: dict[str, Any], opportunities: list[dict[str, Any]], atlas_summary: dict[str, Any]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if summary["ready_for_approval_review_count"]:
        actions.append(
            {
                "key": "review-ready-opportunities",
                "priority": "high",
                "action": "Review the top ready-for-approval SkillOps opportunities before preparing any approval ledger entry.",
            }
        )
    elif opportunities:
        actions.append(
            {
                "key": "review-proposal-queue",
                "priority": "medium",
                "action": "Review proposal-level SkillOps opportunities and keep low-evidence items in observation.",
            }
        )
    if summary["actionable_portfolio_issue_count"]:
        actions.append(
            {
                "key": "triage-skill-library",
                "priority": "high",
                "action": "Triage actionable route collisions, owner gaps, stale skills, drift signals, or no-route opportunities from Skill Atlas.",
            }
        )
    if summary["world_class_pending_count"]:
        actions.append(
            {
                "key": "close-world-class-evidence",
                "priority": "high",
                "action": "Collect accepted external or human evidence for pending world-class ledger entries before public claims.",
            }
        )
    if summary["evidence_consistency_ok"] is not True:
        actions.append(
            {
                "key": "refresh-evidence-consistency",
                "priority": "high",
                "action": "Regenerate evidence consistency before using this curator report for release decisions.",
            }
        )
    if not atlas_summary:
        actions.append(
            {
                "key": "refresh-skill-atlas",
                "priority": "medium",
                "action": "Generate Skill Atlas so weekly curation can see portfolio-level drift and stale-skill signals.",
            }
        )
    if not actions:
        actions.append({"key": "monitor", "priority": "low", "action": "No curation action required beyond routine monitoring."})
    return actions


def build_report(skill_dir: Path, generated_at: str, daily_json: list[Path] | None = None) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    reports_dir = skill_dir / "reports"
    failures: list[str] = []

    daily_paths = daily_report_paths(skill_dir, daily_json or [])
    daily_reports = []
    for path in daily_paths:
        payload = load_json(path)
        if payload.get("ok") is True:
            daily_reports.append(payload)
        else:
            failures.append(f"Daily SkillOps report is missing or invalid: {display_path(path, skill_dir)}")

    opportunities = _dedupe_opportunities(daily_reports)
    decision_counts = _counter(opportunities, "decision")
    action_counts = _counter(opportunities, "action_type")
    risk_counts = _counter(opportunities, "risk_level")

    atlas = load_json(reports_dir / "skill_atlas.json")
    atlas_summary = atlas.get("summary", {}) if isinstance(atlas.get("summary"), dict) else {}
    benchmark = load_json(reports_dir / "benchmark_reproducibility.json")
    benchmark_summary = benchmark.get("summary", {}) if isinstance(benchmark.get("summary"), dict) else {}
    consistency = load_json(reports_dir / "evidence_consistency.json")
    ledger = load_json(reports_dir / "world_class_evidence_ledger.json")
    ledger_summary = ledger.get("summary", {}) if isinstance(ledger.get("summary"), dict) else {}

    portfolio_issue_count = _portfolio_issue_count(atlas_summary)
    failure_count = len(failures)
    summary = {
        "decision": "blocked"
        if failure_count
        else "curator-review"
        if opportunities or portfolio_issue_count or _as_int(ledger_summary.get("pending_count"))
        else "monitor",
        "week_id": week_id(generated_at),
        "daily_report_count": len(daily_reports),
        "opportunity_count": sum(_as_int(report.get("opportunity_summary", {}).get("opportunity_count")) for report in daily_reports),
        "unique_opportunity_count": len(opportunities),
        "ready_for_approval_review_count": decision_counts.get("ready_for_approval_review", 0),
        "proposal_review_count": decision_counts.get("proposal_review", 0),
        "observe_more_evidence_count": decision_counts.get("observe_more_evidence", 0),
        "report_only_count": decision_counts.get("report_only", 0),
        "top_score": _as_int(opportunities[0].get("score")) if opportunities else 0,
        "skill_count": _as_int(atlas_summary.get("skill_count")),
        "actionable_portfolio_issue_count": portfolio_issue_count,
        "release_lock_ready": benchmark_summary.get("release_lock_ready") is True,
        "evidence_consistency_ok": consistency.get("ok") is True,
        "public_world_class_ready": ledger_summary.get("ready_to_claim_world_class") is True,
        "world_class_pending_count": _as_int(ledger_summary.get("pending_count")),
        "writes_source_files": False,
        "auto_patch_enabled": False,
        "failure_count": failure_count,
    }
    actions = build_actions(summary, opportunities, atlas_summary)
    curator_contract = {
        "schema_version": "1.0",
        "contract": "weekly-skillops-curator-report",
        "cadence": "weekly",
        "source_of_truth": [
            "reports/skillops/daily/*.json",
            "reports/skill_atlas.json",
            "reports/benchmark_reproducibility.json",
            "reports/evidence_consistency.json",
            "reports/world_class_evidence_ledger.json",
        ],
        "raw_content_stored": False,
        "redacted_or_generated_evidence_only": True,
        "proposal_only": True,
        "writes_source_files": False,
        "auto_patch_enabled": False,
        "approval_required_for_writes": True,
        "counts_as_world_class_evidence": False,
    }
    report = {
        "schema_version": "1.0",
        "ok": failure_count == 0,
        "generated_at": generated_at,
        "skill_dir": display_path(skill_dir, skill_dir),
        **{key: summary[key] for key in SUMMARY_FIELDS},
        "summary": summary,
        "curator_contract": curator_contract,
        "report_contract": {
            "schema_version": "1.0",
            "contract": "weekly-skillops-curator-report",
            "top_level_mirrors_summary": True,
            "summary_fields": SUMMARY_FIELDS,
        },
        "daily_reports": [display_path(path, skill_dir) for path in daily_paths],
        "opportunity_summary": {
            "action_type_counts": action_counts,
            "decision_counts": decision_counts,
            "risk_level_counts": risk_counts,
        },
        "curator_queue": opportunities[:20],
        "portfolio": {
            "skill_count": summary["skill_count"],
            "actionable_issue_count": portfolio_issue_count,
            "route_collision_count": _as_int(atlas_summary.get("route_collision_count")),
            "actionable_route_collision_count": _as_int(atlas_summary.get("actionable_route_collision_count")),
            "owner_gap_count": _as_int(atlas_summary.get("owner_gap_count")),
            "actionable_owner_gap_count": _as_int(atlas_summary.get("actionable_owner_gap_count")),
            "stale_count": _as_int(atlas_summary.get("stale_count")),
            "actionable_stale_count": _as_int(atlas_summary.get("actionable_stale_count")),
            "drift_signal_count": _as_int(atlas_summary.get("drift_signal_count")),
            "actionable_drift_signal_count": _as_int(atlas_summary.get("actionable_drift_signal_count")),
            "no_route_opportunity_count": _as_int(atlas_summary.get("no_route_opportunity_count")),
        },
        "release_state": {
            "release_lock_ready": summary["release_lock_ready"],
            "evidence_consistency_ok": summary["evidence_consistency_ok"],
            "public_world_class_ready": summary["public_world_class_ready"],
            "world_class_pending_count": summary["world_class_pending_count"],
        },
        "actions": actions,
        "failures": failures,
        "source_reports": {
            "daily_dir": "reports/skillops/daily",
            "skill_atlas": "reports/skill_atlas.json",
            "benchmark_reproducibility": "reports/benchmark_reproducibility.json",
            "evidence_consistency": "reports/evidence_consistency.json",
            "world_class_ledger": "reports/world_class_evidence_ledger.json",
        },
        "artifacts": {
            "json": str(default_weekly_path(skill_dir, generated_at, "json").relative_to(skill_dir)),
            "markdown": str(default_weekly_path(skill_dir, generated_at, "md").relative_to(skill_dir)),
        },
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Weekly SkillOps Curator Report",
        "",
        f"Generated at: `{report['generated_at']}`",
        f"Week: `{summary['week_id']}`",
        "",
        "## Summary",
        "",
    ]
    for key in [
        "decision",
        "daily_report_count",
        "unique_opportunity_count",
        "ready_for_approval_review_count",
        "proposal_review_count",
        "top_score",
        "skill_count",
        "actionable_portfolio_issue_count",
        "release_lock_ready",
        "evidence_consistency_ok",
        "public_world_class_ready",
        "world_class_pending_count",
    ]:
        lines.append(f"- {key}: `{summary[key]}`")
    lines.extend(
        [
            "",
            "This report is a weekly curator cockpit for generated SkillOps evidence. It does not scan private logs, write source files, apply patches, or count as world-class evidence.",
            "",
            "## Curator Boundary",
            "",
        ]
    )
    contract = report["curator_contract"]
    for key in [
        "raw_content_stored",
        "redacted_or_generated_evidence_only",
        "proposal_only",
        "writes_source_files",
        "auto_patch_enabled",
        "approval_required_for_writes",
        "counts_as_world_class_evidence",
    ]:
        lines.append(f"- {key}: `{str(contract[key]).lower()}`")
    lines.extend(["", "## Actions", ""])
    for action in report["actions"]:
        lines.append(f"- `{action['priority']}` {action['action']}")
    lines.extend(["", "## Curator Queue", ""])
    if not report["curator_queue"]:
        lines.append("- No weekly curator opportunities.")
    for item in report["curator_queue"]:
        lines.extend(
            [
                f"### {item.get('title', '')}",
                "",
                f"- ID: `{item.get('opportunity_id', '')}`",
                f"- Action: `{item.get('action_type', '')}`",
                f"- Decision: `{item.get('decision', '')}`",
                f"- Score: `{item.get('score', 0)}`",
                f"- Risk: `{item.get('risk_level', '')}`",
                f"- Source day: `{item.get('daily_report_date', '')}`",
                f"- Policy: {item.get('policy_reason', '')}",
                "",
            ]
        )
    lines.extend(["## Portfolio Signals", ""])
    for key, value in report["portfolio"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Evidence", ""])
    for label, path in report["source_reports"].items():
        lines.append(f"- {label}: `{path}`")
    if report["failures"]:
        lines.extend(["", "## Failures", ""])
        lines.extend(f"- {failure}" for failure in report["failures"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a weekly SkillOps curator report from generated SkillOps evidence.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--daily-json", action="append", default=[], help="Explicit Daily SkillOps JSON report to include.")
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    parser.add_argument("--generated-at", default=utc_now())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    report = build_report(skill_dir, args.generated_at, [Path(item) for item in args.daily_json])
    output_json = resolve_output(skill_dir, args.output_json) if args.output_json else default_weekly_path(skill_dir, args.generated_at, "json")
    output_md = resolve_output(skill_dir, args.output_md) if args.output_md else default_weekly_path(skill_dir, args.generated_at, "md")
    report["artifacts"] = {
        "json": display_path(output_json, skill_dir),
        "markdown": display_path(output_md, skill_dir),
    }
    write_json(output_json, report)
    write_text(output_md, render_markdown(report))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
