#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

from html_rendering import html_text
from render_world_class_evidence_intake import build_intake
from render_world_class_evidence_ledger import build_ledger
from render_world_class_preflight import build_preflight
from render_world_class_submission_review import build_submission_review


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Renders an operator runbook for collecting pending world-class evidence without accepting evidence."


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def by_key(items: list[dict[str, Any]], key_name: str) -> dict[str, dict[str, Any]]:
    return {str(item.get(key_name, "")): item for item in items if item.get(key_name)}


def output_path(path: str, skill_dir: Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        return rel_path(candidate, skill_dir)
    return path


def build_runbook_item(
    entry: dict[str, Any],
    checklist: dict[str, Any],
    review_item: dict[str, Any],
    preflight_item: dict[str, Any],
) -> dict[str, Any]:
    commands = checklist.get("commands", {}) if isinstance(checklist.get("commands", {}), dict) else {}
    must_collect = checklist.get("must_collect", {}) if isinstance(checklist.get("must_collect", {}), dict) else {}
    source_checklist = review_item.get("source_checklist", [])
    blocked_source_checks = [
        row for row in source_checklist if isinstance(row, dict) and row.get("status") != "pass"
    ]
    next_source_actions = []
    for row in blocked_source_checks:
        action = str(row.get("next_action", "")).strip()
        if action and action not in next_source_actions:
            next_source_actions.append(action)
    return {
        "evidence_key": entry.get("key", ""),
        "label": entry.get("label", entry.get("key", "")),
        "category": entry.get("category", "external"),
        "owner": entry.get("owner", "release reviewer"),
        "ledger_status": entry.get("status", "pending"),
        "intake_readiness": checklist.get("readiness", "missing"),
        "review_state": review_item.get("review_state", "missing"),
        "source_accepted": review_item.get("source_accepted") is True,
        "objective": entry.get("objective", ""),
        "current": entry.get("current", ""),
        "execution_runbook": entry.get("runbook", []),
        "blocking_reason": review_item.get("blocking_reason") or checklist.get("blocking_reason") or entry.get("next_action", ""),
        "submission_path": checklist.get("submission_path") or entry.get("submission_state", {}).get("path", ""),
        "template_path": checklist.get("template_path", ""),
        "commands": {
            "prepare_submission": commands.get("prepare_submission", ""),
            "validate_intake": commands.get("validate_intake", ""),
            "review_queue": commands.get("submission_review", ""),
            "refresh_ledger": commands.get("refresh_ledger", "python3 scripts/yao.py world-class-ledger ."),
            "guard_claim": commands.get("guard_claim", "python3 scripts/yao.py world-class-claim-guard ."),
        },
        "must_collect": {
            "provenance_requirements": must_collect.get("provenance_requirements", entry.get("provenance_requirements", [])),
            "success_checks": must_collect.get("success_checks", entry.get("success_checks", [])),
            "privacy_contract": must_collect.get("privacy_contract", entry.get("privacy_contract", [])),
        },
        "evidence_artifacts": entry.get("evidence_artifacts", []),
        "observed_state": entry.get("observed_state", {}),
        "source_checklist": source_checklist,
        "blocked_source_check_count": len(blocked_source_checks),
        "next_source_actions": next_source_actions,
        "repair_checklist": preflight_item.get("repair_checklist", [])
        if isinstance(preflight_item.get("repair_checklist", []), list)
        else [],
        "repair_blocked_count": sum(
            1
            for row in preflight_item.get("repair_checklist", [])
            if isinstance(row, dict) and row.get("status") != "ready"
        ),
        "repair_counts_as_completion": False,
        "phase_queue": preflight_item.get("phase_queue", [])
        if isinstance(preflight_item.get("phase_queue", []), list)
        else [],
        "phase_queue_blocked_count": sum(
            1
            for row in preflight_item.get("phase_queue", [])
            if isinstance(row, dict) and row.get("status") != "ready"
        ),
        "phase_queue_counts_as_completion": False,
        "submission_state": entry.get("submission_state", {}),
        "anti_overclaim": entry.get("anti_overclaim", {}),
    }


def build_operator_runbook(skill_dir: Path, generated_at: str, submissions_dir: Path | None = None) -> dict[str, Any]:
    submissions_dir = submissions_dir or (skill_dir / "evidence" / "world_class" / "submissions")
    ledger = build_ledger(skill_dir, generated_at, submissions_dir=submissions_dir)
    intake = build_intake(skill_dir, generated_at, submissions_dir=submissions_dir)
    review = build_submission_review(skill_dir, generated_at, submissions_dir=submissions_dir)
    preflight = build_preflight(skill_dir, generated_at, submissions_dir=submissions_dir)
    checklist_by_key = by_key(intake.get("operator_checklist", []), "evidence_key")
    review_by_key = by_key(review.get("items", []), "evidence_key")
    preflight_by_key = by_key(preflight.get("items", []), "evidence_key")
    items = [
        build_runbook_item(
            entry,
            checklist_by_key.get(str(entry.get("key", "")), {}),
            review_by_key.get(str(entry.get("key", "")), {}),
            preflight_by_key.get(str(entry.get("key", "")), {}),
        )
        for entry in ledger.get("entries", [])
    ]
    summary = ledger.get("summary", {})
    review_summary = review.get("summary", {})
    preflight_summary = preflight.get("summary", {}) if isinstance(preflight.get("summary", {}), dict) else {}
    return {
        "schema_version": "1.0",
        "ok": True,
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        "summary": {
            "evidence_item_count": len(items),
            "pending_count": summary.get("pending_count", 0),
            "accepted_count": summary.get("accepted_count", 0),
            "awaiting_submission_count": review_summary.get("awaiting_submission_count", 0),
            "ready_for_ledger_review_count": review_summary.get("ready_for_ledger_review_count", 0),
            "valid_packet_source_incomplete_count": review_summary.get("valid_packet_source_incomplete_count", 0),
            "invalid_submission_count": review_summary.get("invalid_submission_count", 0),
            "source_check_count": review_summary.get("source_check_count", 0),
            "source_pass_count": review_summary.get("source_pass_count", 0),
            "source_blocked_count": review_summary.get("source_blocked_count", 0),
            "repair_checklist_count": preflight_summary.get("repair_checklist_count", 0),
            "repair_blocked_count": preflight_summary.get("repair_blocked_count", 0),
            "phase_queue_count": preflight_summary.get("phase_queue_count", 0),
            "phase_queue_blocked_count": preflight_summary.get("phase_queue_blocked_count", 0),
            "phase_queue_row_count": preflight_summary.get("phase_queue_row_count", 0),
            "phase_queue_next_phase": preflight_summary.get("phase_queue_next_phase", ""),
            "phase_queue_next_action_id": preflight_summary.get("phase_queue_next_action_id", ""),
            "phase_queue_next_command": preflight_summary.get("phase_queue_next_command", ""),
            "phase_queue_counts_as_completion": False,
            "ready_to_claim_world_class": summary.get("ready_to_claim_world_class") is True,
            "runbook_counts_as_completion": False,
            "decision": "ready-for-completion-audit" if summary.get("ready_to_claim_world_class") is True else "collect-evidence",
        },
        "submissions": {
            "directory": rel_path(submissions_dir, skill_dir),
            "runbook_counts_submission_as_completion": False,
        },
        "items": items,
        "repair_checklist": preflight.get("repair_checklist", [])
        if isinstance(preflight.get("repair_checklist", []), list)
        else [],
        "phase_queue": preflight.get("phase_queue", []) if isinstance(preflight.get("phase_queue", []), list) else [],
        "source_reports": {
            "ledger": "reports/world_class_evidence_ledger.json",
            "intake": "reports/world_class_evidence_intake.json",
            "preflight": "reports/world_class_evidence_preflight.json",
            "submission_review": "reports/world_class_submission_review.json",
            "claim_guard": "reports/world_class_claim_guard.json",
        },
        "artifacts": {
            "json": "reports/world_class_operator_runbook.json",
            "markdown": "reports/world_class_operator_runbook.md",
            "html": "reports/world_class_operator_runbook.html",
        },
    }


def list_lines(values: list[Any], empty: str) -> list[str]:
    if not values:
        return [f"- {empty}"]
    return [f"- {value}" for value in values]


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# World-Class Operator Runbook",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- ready to claim world-class: `{str(summary['ready_to_claim_world_class']).lower()}`",
        f"- runbook counts as completion: `{str(summary['runbook_counts_as_completion']).lower()}`",
        f"- evidence items: `{summary['evidence_item_count']}`",
        f"- pending: `{summary['pending_count']}`",
        f"- awaiting submission: `{summary['awaiting_submission_count']}`",
        f"- ready for ledger review: `{summary['ready_for_ledger_review_count']}`",
        f"- phase queue: `{summary['phase_queue_blocked_count']}` blocked / `{summary['phase_queue_count']}` phases",
        f"- phase queue rows: `{summary['phase_queue_row_count']}`",
        f"- phase queue counts as completion: `{str(summary['phase_queue_counts_as_completion']).lower()}`",
        "",
        "This runbook coordinates evidence collection only. It does not accept submissions or make world-class completion true.",
        "",
        "## Fast Path",
        "",
        "1. Run the real external or human work for one evidence item.",
        "2. Generate the matching submission draft.",
        "3. Replace template-only fields with aggregate evidence and provenance.",
        "4. Validate intake, review the queue, refresh the ledger, then run the claim guard.",
        "",
    ]
    lines.extend(
        [
            "## Phase Queue",
            "",
            "| Phase | Status | Rows | Blocked | Owners | Next action | Verify |",
            "| --- | --- | ---: | ---: | --- | --- | --- |",
        ]
    )
    for row in report.get("phase_queue", []):
        owners = ", ".join(str(owner) for owner in row.get("owners", []))
        lines.append(
            f"| `{row.get('phase', '')}` | `{row.get('status', '')}` | `{row.get('row_count', 0)}` | "
            f"`{row.get('blocked_count', 0)}` | {owners} | {row.get('next_action', '')} | `{row.get('verification_command', '')}` |"
        )
    lines.append("")
    lines.extend(
        [
            "## Evidence Items",
            "",
            "| Evidence | Ledger | Intake | Review | Blocked checks | Next source action | Owner |",
            "| --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for item in report["items"]:
        next_action = item.get("next_source_actions", ["none"])[0] if item.get("next_source_actions") else "none"
        lines.append(
            f"| `{item['evidence_key']}` | `{item['ledger_status']}` | `{item['intake_readiness']}` | "
            f"`{item['review_state']}` | `{item.get('blocked_source_check_count', 0)}` | {next_action} | {item['owner']} |"
        )
    for item in report["items"]:
        lines.extend(
            [
                "",
                f"## {item['label']}",
                "",
                f"- objective: {item['objective']}",
                f"- blocking reason: {item['blocking_reason']}",
                f"- blocked source checks: `{item.get('blocked_source_check_count', 0)}`",
                f"- repair rows: `{item.get('repair_blocked_count', 0)}` blocked",
                f"- phase queue: `{item.get('phase_queue_blocked_count', 0)}` blocked phases",
                f"- submission: `{item['submission_path'] or 'missing'}`",
                f"- template: `{item['template_path'] or 'missing'}`",
                "",
                "### Phase Queue",
                "",
                "| Phase | Status | Rows | Blocked | Next action |",
                "| --- | --- | ---: | ---: | --- |",
            ]
        )
        item_phase_queue = item.get("phase_queue", [])
        if item_phase_queue:
            for row in item_phase_queue:
                lines.append(
                    f"| `{row.get('phase', '')}` | `{row.get('status', '')}` | `{row.get('row_count', 0)}` | "
                    f"`{row.get('blocked_count', 0)}` | {row.get('next_action', '')} |"
                )
        else:
            lines.append("| No phase queue listed. | `n/a` | `0` | `0` | n/a |")
        lines.extend(
            [
                "",
                "### Source Runbook",
                "",
                *list_lines(item.get("execution_runbook", []), "No source runbook listed."),
                "",
                "### Commands",
                "",
            ]
        )
        for label, command in item["commands"].items():
            lines.append(f"- {label}: `{command}`")
        lines.extend(["", "### Must Collect", ""])
        lines.extend(list_lines(item["must_collect"].get("provenance_requirements", []), "No provenance requirements listed."))
        lines.extend(["", "### Success Checks", ""])
        lines.extend(list_lines(item["must_collect"].get("success_checks", []), "No success checks listed."))
        lines.extend(["", "### Privacy Contract", ""])
        lines.extend(list_lines(item["must_collect"].get("privacy_contract", []), "No privacy contract listed."))
        lines.extend(["", "### Evidence Artifacts", ""])
        lines.extend(list_lines(item.get("evidence_artifacts", []), "No evidence artifacts listed."))
        lines.extend(["", "### Next Source Actions", ""])
        lines.extend(list_lines(item.get("next_source_actions", []), "No blocked source checks."))
        lines.extend(
            [
                "",
                "### Source Evidence Snapshot",
                "",
                "| Check | Current | Expected | Status | Next action |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        source_rows = item.get("source_checklist", [])
        if source_rows:
            for row in source_rows:
                lines.append(
                    f"| {row['label']} | `{row['actual']}` | `{row['expected']}` | `{row['status']}` | {row.get('next_action', '')} |"
                )
        else:
            lines.append("| No source checks listed. | `n/a` | `n/a` | `n/a` | n/a |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Planned work, draft packets, metadata fallback, pending human decisions, and local command runners do not count as completion.",
            "- Valid intake means ready for submission review; ledger review still requires passing source evidence.",
            "- The world-class ledger and claim guard remain the source of truth.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def html_list(values: list[Any], empty: str) -> str:
    if not values:
        return f"<li>{html_text(empty)}</li>"
    return "".join(f"<li>{html_text(value)}</li>" for value in values)


def html_source_checks(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p class='muted'>No source checks listed.</p>"
    items = []
    for row in rows:
        items.append(
            "<li class='source-check "
            + html_text(row.get("status", ""))
            + "'>"
            f"<span>{html_text(row.get('label', ''))}</span>"
            f"<code>{html_text(row.get('field', ''))}: {html_text(row.get('actual', ''))} / {html_text(row.get('expected', ''))}</code>"
            f"<small>{html_text(row.get('next_action', ''))}</small>"
            "</li>"
        )
    return "<ul class='source-checks'>" + "".join(items) + "</ul>"


def html_phase_queue(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p class='muted'>No phase queue listed.</p>"
    items = []
    for row in rows:
        items.append(
            "<li class='source-check'>"
            f"<span>{html_text(row.get('label', row.get('phase', '')))}</span>"
            f"<code>{html_text(row.get('phase', ''))}: {html_text(row.get('blocked_count', 0))} / {html_text(row.get('row_count', 0))}</code>"
            f"<small>{html_text(row.get('next_action', ''))}</small>"
            "</li>"
        )
    return "<ul class='source-checks'>" + "".join(items) + "</ul>"


def render_html_item(item: dict[str, Any]) -> str:
    commands = "".join(
        f"<li><span>{html_text(label.replace('_', ' '))}</span><code>{html_text(command)}</code></li>"
        for label, command in item["commands"].items()
    )
    must_collect = item["must_collect"]
    return f"""
      <article class="item-card {html_text(item['review_state'])}">
        <header><span>{html_text(item['category'])} · {html_text(item['review_state'])}</span><h3>{html_text(item['label'])}</h3></header>
        <p>{html_text(item['blocking_reason'])}</p>
        <dl>
          <dt>Owner</dt><dd>{html_text(item['owner'])}</dd>
          <dt>Ledger</dt><dd><code>{html_text(item['ledger_status'])}</code></dd>
          <dt>Blocked</dt><dd><code>{html_text(item.get('blocked_source_check_count', 0))}</code></dd>
          <dt>Queue</dt><dd><code>{html_text(item.get('phase_queue_blocked_count', 0))}</code></dd>
          <dt>Submission</dt><dd><code>{html_text(item['submission_path'])}</code></dd>
        </dl>
        <section class="source-panel"><h4>Phase Queue</h4>{html_phase_queue(item.get('phase_queue', []))}</section>
        <section class="source-panel"><h4>Source Runbook</h4><ul>{html_list(item.get('execution_runbook', []), 'No source runbook listed.')}</ul></section>
        <section><h4>Commands</h4><ul class="commands">{commands}</ul></section>
        <div class="mini-grid">
          <section><h4>Must Collect</h4><ul>{html_list(must_collect.get('provenance_requirements', []), 'No provenance requirements listed.')}</ul></section>
          <section><h4>Success Checks</h4><ul>{html_list(must_collect.get('success_checks', []), 'No success checks listed.')}</ul></section>
          <section><h4>Privacy</h4><ul>{html_list(must_collect.get('privacy_contract', []), 'No privacy contract listed.')}</ul></section>
        </div>
        <section class="source-panel"><h4>Next Source Actions</h4><ul>{html_list(item.get('next_source_actions', []), 'No blocked source checks.')}</ul></section>
        <section class="source-panel"><h4>Source Evidence Snapshot</h4>{html_source_checks(item.get('source_checklist', []))}</section>
      </article>
    """.strip()


def render_html(report: dict[str, Any]) -> str:
    summary = report["summary"]
    stats = [
        ("Pending", summary["pending_count"]),
        ("Awaiting", summary["awaiting_submission_count"]),
        ("Ready", summary["ready_for_ledger_review_count"]),
        ("Source", f"{summary.get('source_pass_count', 0)}/{summary.get('source_check_count', 0)}"),
        ("Queue", f"{summary.get('phase_queue_blocked_count', 0)}/{summary.get('phase_queue_count', 0)}"),
        ("Blocked", summary.get("source_blocked_count", 0)),
        ("Invalid", summary["invalid_submission_count"]),
    ]
    stat_html = "".join(f"<article><span>{html_text(label)}</span><strong>{html_text(value)}</strong></article>" for label, value in stats)
    item_html = "".join(render_html_item(item) for item in report["items"])
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>World-Class Operator Runbook</title>
  <style>
    :root {{ --ink:#1B365D; --text:#202124; --muted:#6f6a63; --line:#e8e1d8; --soft:#f8f6f2; --warn:#9b4d0f; --pass:#1f6f43; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#fff; color:var(--text); font:16px/1.55 Georgia, "Times New Roman", serif; }}
    .topbar {{ position:sticky; top:0; z-index:10; background:rgba(255,255,255,.96); border-bottom:1px solid var(--line); }}
    .topbar-inner {{ max-width:1180px; margin:0 auto; padding:12px 24px; display:flex; justify-content:space-between; gap:16px; align-items:center; }}
    .brand, a {{ color:var(--ink); }}
    .links {{ display:flex; gap:14px; flex-wrap:wrap; }}
    .links a {{ text-decoration:none; }}
    .shell {{ max-width:1180px; margin:0 auto; padding:36px 24px 72px; }}
    .hero {{ border-bottom:1px solid var(--line); padding:32px 0 28px; }}
    .eyebrow {{ color:var(--ink); font-size:12px; text-transform:uppercase; font-weight:700; letter-spacing:0; }}
    h1 {{ margin:8px 0 12px; color:var(--ink); font-size:56px; line-height:1.04; letter-spacing:0; }}
    h2, h3, h4 {{ color:var(--ink); letter-spacing:0; }}
    h2 {{ margin:0 0 14px; font-size:30px; }}
    h3 {{ margin:4px 0 10px; font-size:22px; }}
    h4 {{ margin:0 0 8px; font-size:16px; }}
    .lede {{ max-width:800px; color:var(--muted); font-size:20px; }}
    .stats {{ display:grid; grid-template-columns:repeat(6, minmax(0,1fr)); gap:12px; margin-top:26px; }}
    .stats article, .panel, .item-card {{ border:1px solid var(--line); border-radius:8px; background:#fff; }}
    .stats article {{ padding:16px; }}
    .stats span, .item-card span, .muted {{ color:var(--muted); }}
    .stats strong {{ display:block; color:var(--ink); font-size:34px; line-height:1; }}
    .section {{ padding:32px 0; border-bottom:1px solid var(--line); }}
    .item-grid {{ display:grid; grid-template-columns:1fr; gap:18px; }}
    .item-card {{ padding:20px; border-left:4px solid var(--warn); }}
    .item-card.ready-for-ledger-review, .item-card.accepted {{ border-left-color:var(--pass); }}
    dl {{ display:grid; grid-template-columns:96px minmax(0,1fr); gap:8px 12px; }}
    dt {{ color:var(--ink); }}
    dd {{ margin:0; min-width:0; overflow-wrap:anywhere; }}
    code {{ font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size:13px; overflow-wrap:anywhere; }}
    ul, ol {{ padding-left:20px; }}
    .commands {{ list-style:none; padding:0; margin:0; display:grid; gap:10px; }}
    .commands li {{ padding:12px; background:var(--soft); border-radius:8px; }}
    .commands span {{ display:block; color:var(--ink); font-weight:700; margin-bottom:4px; }}
    .mini-grid {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:12px; margin-top:14px; }}
    .mini-grid section, .panel {{ background:var(--soft); border-radius:8px; padding:14px; min-width:0; }}
    .mini-grid li, .panel li {{ overflow-wrap:anywhere; }}
    .source-panel {{ background:var(--soft); border-radius:8px; padding:14px; min-width:0; }}
    .source-checks {{ list-style:none; padding:0; margin:0; display:grid; gap:8px; }}
    .source-check {{ border-top:1px solid var(--line); padding-top:8px; display:grid; gap:3px; }}
    .source-check span {{ color:var(--ink); }}
    .source-check code, .source-check small {{ overflow-wrap:anywhere; }}
    @media (max-width:820px) {{ .stats, .mini-grid {{ grid-template-columns:1fr; }} h1 {{ font-size:38px; }} .topbar-inner {{ align-items:flex-start; flex-direction:column; }} }}
  </style>
</head>
<body>
  <nav class="topbar"><div class="topbar-inner"><span class="brand">World-Class Runbook</span><div class="links"><a href="#fast-path">Fast Path</a><a href="#items">Evidence</a><a href="#boundary">Boundary</a></div></div></nav>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">Evidence Operations</span>
      <h1>World-Class Operator Runbook</h1>
      <p class="lede">A single operating page for collecting the remaining human and external evidence. It coordinates action, but does not accept evidence or change the ledger.</p>
      <div class="stats">{stat_html}</div>
    </section>
    <section class="section panel" id="fast-path"><h2>Fast Path</h2><ol><li>Run the real external or human work for one evidence item.</li><li>Generate and fill the matching submission draft.</li><li>Validate intake and inspect the submission review queue.</li><li>Refresh the ledger and run the claim guard before making any completion claim.</li></ol></section>
    <section class="section panel" id="phase-queue"><h2>Phase Queue</h2>{html_phase_queue(report.get('phase_queue', []))}</section>
    <section class="section" id="items"><h2>Evidence Items</h2><div class="item-grid">{item_html}</div></section>
    <section class="section panel" id="boundary"><h2>Boundary</h2><ul><li>Planned work, draft packets, metadata fallback, pending human decisions, and local command runners do not count as completion.</li><li>Valid intake means ready for submission review; ledger review still requires passing source evidence.</li><li>The world-class ledger and claim guard remain the source of truth.</li></ul></section>
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an operator runbook for collecting pending world-class evidence.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--submissions-dir")
    parser.add_argument("--output-json", default="reports/world_class_operator_runbook.json")
    parser.add_argument("--output-md", default="reports/world_class_operator_runbook.md")
    parser.add_argument("--output-html", default="reports/world_class_operator_runbook.html")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    submissions_dir = Path(args.submissions_dir).resolve() if args.submissions_dir else None
    report = build_operator_runbook(skill_dir, args.generated_at, submissions_dir=submissions_dir)
    outputs = {
        "json": Path(args.output_json),
        "markdown": Path(args.output_md),
        "html": Path(args.output_html),
    }
    for key, path in outputs.items():
        if not path.is_absolute():
            path = skill_dir / path
        path.parent.mkdir(parents=True, exist_ok=True)
        report["artifacts"][key] = output_path(str(path), skill_dir)
        if key == "json":
            path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        elif key == "markdown":
            path.write_text(render_markdown(report), encoding="utf-8")
        else:
            path.write_text(render_html(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
