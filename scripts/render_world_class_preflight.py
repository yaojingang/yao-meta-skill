#!/usr/bin/env python3
import argparse
import json
import os
import shlex
from datetime import date
from pathlib import Path
from typing import Any

from html_rendering import html_text
from render_world_class_evidence_intake import build_intake
from render_world_class_evidence_ledger import build_ledger
from render_world_class_submission_review import build_submission_review
from world_class_evidence_contract import rel_path
from world_class_source_checks import summarize_source_checklist


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Renders a preflight checklist for collecting pending world-class evidence without accepting evidence."


PREFLIGHT_SPECS: dict[str, list[dict[str, Any]]] = {
    "provider-holdout": [
        {
            "key": "output-cases",
            "label": "Output eval cases",
            "kind": "file",
            "path": "evals/output/cases.jsonl",
            "required": True,
            "next_action": "Keep output holdout cases available before provider execution.",
        },
        {
            "key": "provider-runner",
            "label": "Provider runner",
            "kind": "file",
            "path": "scripts/provider_output_eval_runner.py",
            "required": True,
            "next_action": "Use the provider runner instead of the local command runner for model-backed evidence.",
        },
        {
            "key": "openai-api-key",
            "label": "Provider credential",
            "kind": "env",
            "name": "OPENAI_API_KEY",
            "required": True,
            "secret": True,
            "next_action": "Set OPENAI_API_KEY in the operator shell; never commit or print the value.",
        },
        {
            "key": "provider-model",
            "label": "Provider model",
            "kind": "env",
            "name": "YAO_OUTPUT_EVAL_MODEL",
            "required": False,
            "default": "gpt-4.1-mini",
            "next_action": "Optionally set YAO_OUTPUT_EVAL_MODEL; the runbook defaults to gpt-4.1-mini.",
        },
    ],
    "human-adjudication": [
        {
            "key": "review-kit",
            "label": "Blind review kit",
            "kind": "file",
            "path": "reports/output_review_kit.html",
            "required": True,
            "next_action": "Open the blind review kit and record real reviewer choices.",
        },
        {
            "key": "decision-template",
            "label": "Decision template",
            "kind": "file",
            "path": "reports/output_review_decisions.json",
            "required": True,
            "next_action": "Import real A/B decisions with `python3 scripts/yao.py output-review-import --input <reviewer-decisions.json> --run-adjudication`.",
        },
        {
            "key": "decision-importer",
            "label": "Decision importer",
            "kind": "file",
            "path": "scripts/import_output_review_decisions.py",
            "required": True,
            "next_action": "Use the importer to reject raw content fields and normalize reviewer decisions before adjudication.",
        },
        {
            "key": "human-reviewer",
            "label": "Human reviewer",
            "kind": "human",
            "required": True,
            "next_action": "Assign a real reviewer identity before claiming human adjudication.",
        },
    ],
    "native-permission-enforcement": [
        {
            "key": "permission-policy",
            "label": "Permission policy",
            "kind": "file",
            "path": "security/permission_policy.json",
            "required": True,
            "next_action": "Keep approved high-permission capabilities explicit.",
        },
        {
            "key": "permission-probes",
            "label": "Runtime probes",
            "kind": "file",
            "path": "reports/runtime_permission_probes.json",
            "required": True,
            "next_action": "Refresh runtime permission probes after packaging changes.",
        },
        {
            "key": "native-guard",
            "label": "Native guard",
            "kind": "external",
            "required": True,
            "next_action": "Attach a real target-client or external installer runtime guard; metadata fallback is not enough.",
        },
    ],
    "native-client-telemetry": [
        {
            "key": "native-host",
            "label": "Native telemetry host",
            "kind": "file",
            "path": "scripts/telemetry_native_host.py",
            "required": True,
            "next_action": "Use the native host to receive metadata-only client events.",
        },
        {
            "key": "hook-recipes",
            "label": "Hook recipes",
            "kind": "file",
            "path": "reports/telemetry_hook_recipes.json",
            "required": True,
            "next_action": "Refresh telemetry hook recipes before external client installation.",
        },
        {
            "key": "external-client",
            "label": "External client",
            "kind": "external",
            "required": True,
            "next_action": "Install a real Browser, Chrome, IDE, or provider client that emits metadata-only events.",
        },
    ],
}


def env_present(name: str) -> bool:
    return bool(os.environ.get(name))


def shell_path(path: Path, root: Path) -> str:
    return shlex.quote(rel_path(path, root))


def build_submission_commands(skill_dir: Path, submissions_dir: Path, evidence_key: str | None = None) -> dict[str, str]:
    output_dir = shell_path(submissions_dir, skill_dir)
    prepare = f"python3 scripts/yao.py world-class-submission-kit . --output-dir {output_dir}"
    if evidence_key:
        prepare = f"python3 scripts/yao.py world-class-submission-kit . --evidence-key {evidence_key} --output-dir {output_dir}"
    prefilled_prepare = f"{prepare} --prefill-artifacts"
    return {
        "prepare_submission": prepare,
        "prepare_prefilled_submission": prefilled_prepare,
        "validate_intake": f"python3 scripts/yao.py world-class-intake . --submissions-dir {output_dir}",
        "submission_review": f"python3 scripts/yao.py world-class-submission-review . --submissions-dir {output_dir}",
        "refresh_ledger": f"python3 scripts/yao.py world-class-ledger . --submissions-dir {output_dir}",
        "guard_claim": "python3 scripts/yao.py world-class-claim-guard .",
    }


def build_precheck(skill_dir: Path, evidence_key: str, spec: dict[str, Any]) -> dict[str, Any]:
    kind = str(spec.get("kind", ""))
    required = spec.get("required") is True
    row = {
        "evidence_key": evidence_key,
        "key": spec.get("key", ""),
        "label": spec.get("label", ""),
        "kind": kind,
        "required": required,
        "next_action": spec.get("next_action", ""),
        "secret_value_redacted": spec.get("secret") is True,
    }
    if kind == "file":
        path = skill_dir / str(spec.get("path", ""))
        exists = path.exists()
        row.update(
            {
                "path": rel_path(path, skill_dir),
                "status": "pass" if exists else ("missing" if required else "optional"),
                "actual": "present" if exists else "missing",
            }
        )
        return row
    if kind == "env":
        name = str(spec.get("name", ""))
        present = env_present(name)
        row.update(
            {
                "env": name,
                "status": "pass" if present else ("missing" if required else "optional"),
                "actual": "set" if present else "not-set",
                "default": spec.get("default", ""),
            }
        )
        return row
    if kind == "human":
        row.update(
            {
                "status": "human-required",
                "actual": "external-human-action",
            }
        )
        return row
    if kind == "external":
        row.update(
            {
                "status": "external-required",
                "actual": "external-integration-required",
            }
        )
        return row
    row.update({"status": "unknown", "actual": "unknown"})
    return row


def item_status(entry: dict[str, Any], prechecks: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> str:
    if entry.get("status") == "accepted":
        return "accepted"
    blocking = {row.get("status") for row in prechecks if row.get("required") is True}
    if "missing" in blocking or "external-required" in blocking:
        return "blocked"
    if "human-required" in blocking:
        return "ready-for-human-review"
    if any(row.get("status") != "pass" for row in source_rows):
        return "ready-to-collect"
    return "ready-for-submission"


def first_next_action(prechecks: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> str:
    for row in prechecks:
        if row.get("required") is True and row.get("status") != "pass":
            return str(row.get("next_action", ""))
    for row in source_rows:
        if row.get("status") != "pass":
            return str(row.get("next_action", ""))
    return "Validate intake, refresh the ledger, and run the claim guard."


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|")


def build_preflight(skill_dir: Path, generated_at: str, submissions_dir: Path | None = None) -> dict[str, Any]:
    submissions_dir = submissions_dir or (skill_dir / "evidence" / "world_class" / "submissions")
    ledger = build_ledger(skill_dir, generated_at, submissions_dir=submissions_dir)
    intake = build_intake(skill_dir, generated_at, submissions_dir=submissions_dir)
    review = build_submission_review(skill_dir, generated_at, submissions_dir=submissions_dir)
    review_by_key = {str(item.get("evidence_key", "")): item for item in review.get("items", [])}
    intake_by_key = {str(item.get("evidence_key", "")): item for item in intake.get("operator_checklist", [])}
    items: list[dict[str, Any]] = []
    precheck_rows: list[dict[str, Any]] = []
    source_rows: list[dict[str, Any]] = []
    for entry in ledger.get("entries", []):
        key = str(entry.get("key", ""))
        prechecks = [build_precheck(skill_dir, key, spec) for spec in PREFLIGHT_SPECS.get(key, [])]
        review_item = review_by_key.get(key, {})
        item_source_rows = review_item.get("source_checklist", entry.get("source_checklist", []))
        item_source_rows = item_source_rows if isinstance(item_source_rows, list) else []
        status = item_status(entry, prechecks, item_source_rows)
        item_commands = build_submission_commands(skill_dir, submissions_dir, key)
        item = {
            "evidence_key": key,
            "label": entry.get("label", key),
            "category": entry.get("category", "external"),
            "owner": entry.get("owner", "release reviewer"),
            "status": status,
            "ledger_status": entry.get("status", "pending"),
            "intake_readiness": intake_by_key.get(key, {}).get("readiness", "missing"),
            "review_state": review_item.get("review_state", "missing"),
            "source_accepted": entry.get("source_accepted") is True,
            "prechecks": prechecks,
            "source_checklist": item_source_rows,
            "next_action": first_next_action(prechecks, item_source_rows),
            "submission_path": intake_by_key.get(key, {}).get("submission_path", ""),
            "template_path": intake_by_key.get(key, {}).get("template_path", ""),
            "commands": item_commands,
            "submission_kit": {
                "prepare_command": item_commands["prepare_submission"],
                "prefill_command": item_commands["prepare_prefilled_submission"],
                "output_dir": rel_path(submissions_dir, skill_dir),
                "draft_path": intake_by_key.get(key, {}).get("submission_path", ""),
                "template_path": intake_by_key.get(key, {}).get("template_path", ""),
                "drafts_count_as_evidence": False,
                "artifact_prefill_counts_as_evidence": False,
            },
            "runbook": entry.get("runbook", []),
        }
        items.append(item)
        precheck_rows.extend(prechecks)
        source_rows.extend(item_source_rows)
    precheck_status_counts: dict[str, int] = {}
    for row in precheck_rows:
        status = str(row.get("status", "unknown"))
        precheck_status_counts[status] = precheck_status_counts.get(status, 0) + 1
    source_summary = summarize_source_checklist(source_rows)
    collection_ready_count = sum(1 for item in items if item["status"] in {"ready-to-collect", "ready-for-human-review", "ready-for-submission"})
    blocked_count = sum(1 for item in items if item["status"] == "blocked")
    ready_to_claim = ledger.get("summary", {}).get("ready_to_claim_world_class") is True
    summary = {
        "evidence_item_count": len(items),
        "precheck_count": len(precheck_rows),
        "precheck_pass_count": precheck_status_counts.get("pass", 0),
        "precheck_missing_count": precheck_status_counts.get("missing", 0),
        "precheck_optional_count": precheck_status_counts.get("optional", 0),
        "precheck_human_required_count": precheck_status_counts.get("human-required", 0),
        "precheck_external_required_count": precheck_status_counts.get("external-required", 0),
        "collection_ready_count": collection_ready_count,
        "collection_blocked_count": blocked_count,
        **source_summary,
        "pending_count": ledger.get("summary", {}).get("pending_count", 0),
        "ready_to_claim_world_class": ready_to_claim,
        "credential_value_exposed": False,
        "preflight_counts_as_evidence": False,
        "decision": "ready-for-completion-audit" if ready_to_claim else ("collection-preflight-blocked" if blocked_count else "ready-to-collect-evidence"),
    }
    return {
        "schema_version": "1.0",
        "ok": True,
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        "summary": summary,
        "status_counts": {item["status"]: sum(1 for candidate in items if candidate["status"] == item["status"]) for item in items},
        "precheck_status_counts": precheck_status_counts,
        "items": items,
        "prechecks": precheck_rows,
        "source_checklist": source_rows,
        "submissions": {
            "directory": rel_path(submissions_dir, skill_dir),
            "commands": build_submission_commands(skill_dir, submissions_dir),
            "submission_kit_command": build_submission_commands(skill_dir, submissions_dir)["prepare_submission"],
            "submission_kit_prefill_command": build_submission_commands(skill_dir, submissions_dir)[
                "prepare_prefilled_submission"
            ],
            "preflight_counts_submission_as_completion": False,
            "drafts_count_as_evidence": False,
            "artifact_prefill_counts_as_evidence": False,
        },
        "source_reports": {
            "ledger": "reports/world_class_evidence_ledger.json",
            "intake": "reports/world_class_evidence_intake.json",
            "submission_review": "reports/world_class_submission_review.json",
            "operator_runbook": "reports/world_class_operator_runbook.json",
        },
        "artifacts": {
            "json": "reports/world_class_evidence_preflight.json",
            "markdown": "reports/world_class_evidence_preflight.md",
            "html": "reports/world_class_evidence_preflight.html",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# World-Class Evidence Preflight",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- ready to claim world-class: `{str(summary['ready_to_claim_world_class']).lower()}`",
        f"- preflight counts as evidence: `{str(summary['preflight_counts_as_evidence']).lower()}`",
        f"- credential value exposed: `{str(summary['credential_value_exposed']).lower()}`",
        f"- collection ready: `{summary['collection_ready_count']}`",
        f"- collection blocked: `{summary['collection_blocked_count']}`",
        f"- source checks: `{summary['source_pass_count']}` pass / `{summary['source_check_count']}` total",
        "",
        "This preflight report checks whether an operator can start collecting the remaining external or human evidence. It never accepts evidence, prints secret values, or changes the world-class ledger.",
        "",
        "## Submission Kit Handoff",
        "",
        f"- submissions directory: `{report['submissions']['directory']}`",
        f"- prepare drafts: `{report['submissions']['commands']['prepare_submission']}`",
        f"- prepare drafts with artifact SHA prefill: `{report['submissions']['commands']['prepare_prefilled_submission']}`",
        f"- validate intake: `{report['submissions']['commands']['validate_intake']}`",
        f"- review queue: `{report['submissions']['commands']['submission_review']}`",
        f"- refresh ledger: `{report['submissions']['commands']['refresh_ledger']}`",
        f"- guard claims: `{report['submissions']['commands']['guard_claim']}`",
        f"- drafts count as evidence: `{str(report['submissions']['drafts_count_as_evidence']).lower()}`",
        f"- artifact prefill counts as evidence: `{str(report['submissions']['artifact_prefill_counts_as_evidence']).lower()}`",
        "",
        "Generate the submission kit after the real provider, human, native-permission, or native-client work exists. The generated JSON drafts remain `template_only: true` until an operator edits them with real aggregate artifact references and matching SHA-256 digests. The prefill command only inserts local artifact SHA-256 digests; it does not make a draft count as evidence.",
        "",
        "## Evidence Items",
        "",
        "| Evidence | Status | Intake | Review | Next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["items"]:
        next_action = str(item.get("next_action", "")).replace("|", "\\|")
        lines.append(
            f"| `{item['evidence_key']}` | `{item['status']}` | `{item['intake_readiness']}` | `{item['review_state']}` | {next_action} |"
        )
    for item in report["items"]:
        lines.extend(
            [
                "",
                f"## {item['label']}",
                "",
                f"- status: `{item['status']}`",
                f"- ledger: `{item['ledger_status']}`",
                f"- submission: `{item.get('submission_path') or 'missing'}`",
                f"- prepare draft: `{item['commands']['prepare_submission']}`",
                f"- prepare draft with artifact SHA prefill: `{item['commands']['prepare_prefilled_submission']}`",
                "",
                "### Prechecks",
                "",
                "| Check | Kind | Current | Status | Next action |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in item.get("prechecks", []):
            action = md_cell(row.get("next_action", ""))
            lines.append(
                f"| {row['label']} | `{row['kind']}` | `{row['actual']}` | `{row['status']}` | {action} |"
            )
        lines.extend(
            [
                "",
                "### Source Checks",
                "",
                "| Check | Current | Expected | Status | Next action |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for row in item.get("source_checklist", []):
            action = md_cell(row.get("next_action", ""))
            lines.append(
                f"| {row['label']} | `{row['actual']}` | `{row['expected']}` | `{row['status']}` | {action} |"
            )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Environment variables are reported only as `set` or `not-set`; values are never printed.",
            "- Human-required and external-required states are operator actions, not accepted evidence.",
            "- The world-class ledger remains the source of truth for `ready_to_claim_world_class`.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def html_list(values: list[Any], empty: str) -> str:
    if not values:
        return f"<li>{html_text(empty)}</li>"
    return "".join(f"<li>{html_text(value)}</li>" for value in values)


def render_html_commands(commands: dict[str, str]) -> str:
    return "".join(
        f"<li><span>{html_text(label.replace('_', ' '))}</span><code>{html_text(command)}</code></li>"
        for label, command in commands.items()
    )


def render_html_prechecks(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p class=\"muted\">No prechecks listed.</p>"
    return "".join(
        """
        <article class="check-row {status}">
          <div>
            <span>{kind}</span>
            <strong>{label}</strong>
          </div>
          <dl>
            <dt>Current</dt><dd><code>{actual}</code></dd>
            <dt>Status</dt><dd>{status}</dd>
            <dt>Action</dt><dd>{action}</dd>
          </dl>
        </article>
        """.format(
            status=html_text(row.get("status", "")),
            kind=html_text(row.get("kind", "")),
            label=html_text(row.get("label", "")),
            actual=html_text(row.get("actual", "")),
            action=html_text(row.get("next_action", "")),
        )
        for row in rows
    )


def render_html_source_checks(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "<p class=\"muted\">No source checks listed.</p>"
    return "".join(
        """
        <article class="check-row {status}">
          <div>
            <span>{field}</span>
            <strong>{label}</strong>
          </div>
          <dl>
            <dt>Current</dt><dd><code>{actual}</code></dd>
            <dt>Expected</dt><dd><code>{expected}</code></dd>
            <dt>Status</dt><dd>{status}</dd>
            <dt>Action</dt><dd>{action}</dd>
          </dl>
        </article>
        """.format(
            status=html_text(row.get("status", "")),
            field=html_text(row.get("field", "")),
            label=html_text(row.get("label", "")),
            actual=html_text(row.get("actual", "")),
            expected=html_text(row.get("expected", "")),
            action=html_text(row.get("next_action", "")),
        )
        for row in rows
    )


def render_html_item(item: dict[str, Any]) -> str:
    return f"""
      <article class="evidence-card {html_text(item.get('status', ''))}">
        <header>
          <span>{html_text(item.get('category', ''))} · {html_text(item.get('status', ''))}</span>
          <h3>{html_text(item.get('label', item.get('evidence_key', '')))}</h3>
        </header>
        <dl class="meta">
          <dt>Evidence</dt><dd><code>{html_text(item.get('evidence_key', ''))}</code></dd>
          <dt>Ledger</dt><dd>{html_text(item.get('ledger_status', ''))}</dd>
          <dt>Intake</dt><dd>{html_text(item.get('intake_readiness', ''))}</dd>
          <dt>Review</dt><dd>{html_text(item.get('review_state', ''))}</dd>
          <dt>Draft</dt><dd><code>{html_text(item.get('submission_path', ''))}</code></dd>
        </dl>
        <section class="next-action">
          <h4>Next Action</h4>
          <p>{html_text(item.get('next_action', ''))}</p>
          <code>{html_text(item.get('commands', {}).get('prepare_submission', ''))}</code>
          <code>{html_text(item.get('commands', {}).get('prepare_prefilled_submission', ''))}</code>
        </section>
        <section class="check-section">
          <h4>Prechecks</h4>
          <div class="check-grid">{render_html_prechecks(item.get('prechecks', []))}</div>
        </section>
        <section class="check-section">
          <h4>Source Checks</h4>
          <div class="check-grid">{render_html_source_checks(item.get('source_checklist', []))}</div>
        </section>
        <section class="runbook">
          <h4>Runbook</h4>
          <ul>{html_list(item.get('runbook', []), 'No runbook steps listed.')}</ul>
        </section>
      </article>
    """


def render_html(report: dict[str, Any]) -> str:
    summary = report["summary"]
    stats = [
        ("Decision", summary["decision"]),
        ("Pending", summary["pending_count"]),
        ("Ready", summary["collection_ready_count"]),
        ("Blocked", summary["collection_blocked_count"]),
        ("Source", f"{summary['source_pass_count']}/{summary['source_check_count']}"),
    ]
    stat_html = "".join(
        f"<article><span>{html_text(label)}</span><strong>{html_text(value)}</strong></article>"
        for label, value in stats
    )
    item_cards = "".join(render_html_item(item) for item in report.get("items", []))
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>World-Class Evidence Preflight</title>
  <style>
    :root {{ --ink:#1B365D; --text:#202124; --muted:#6f6a63; --line:#e8e1d8; --soft:#f8f6f2; --warn:#9b4d0f; --pass:#1f6f43; --block:#8a1f11; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#fff; color:var(--text); font:16px/1.55 Georgia, "Times New Roman", serif; }}
    .topbar {{ position:sticky; top:0; z-index:10; background:rgba(255,255,255,.96); border-bottom:1px solid var(--line); }}
    .topbar-inner {{ max-width:1180px; margin:0 auto; padding:12px 24px; display:flex; justify-content:space-between; gap:16px; align-items:center; }}
    .brand, a, h1, h2, h3, h4 {{ color:var(--ink); }}
    .links {{ display:flex; gap:14px; flex-wrap:wrap; }}
    .links a {{ text-decoration:none; }}
    .shell {{ max-width:1180px; margin:0 auto; padding:36px 24px 72px; }}
    .hero {{ border-bottom:1px solid var(--line); padding:32px 0 28px; }}
    .eyebrow {{ color:var(--ink); font-size:12px; text-transform:uppercase; font-weight:700; letter-spacing:0; }}
    h1 {{ margin:8px 0 12px; font-size:56px; line-height:1.04; letter-spacing:0; }}
    h2 {{ margin:0 0 14px; font-size:30px; letter-spacing:0; }}
    h3 {{ margin:4px 0 10px; font-size:22px; letter-spacing:0; }}
    h4 {{ margin:0 0 8px; font-size:16px; letter-spacing:0; }}
    .lede {{ max-width:820px; color:var(--muted); font-size:20px; }}
    .stats {{ display:grid; grid-template-columns:repeat(5, minmax(0,1fr)); gap:12px; margin:26px 0 0; }}
    .stats article, .panel, .evidence-card, .check-row {{ border:1px solid var(--line); border-radius:8px; background:#fff; }}
    .stats article {{ padding:16px; }}
    .stats span, .muted, .evidence-card header span, .check-row span {{ color:var(--muted); }}
    .stats strong {{ display:block; color:var(--ink); font-size:28px; line-height:1.15; overflow-wrap:anywhere; }}
    .section {{ padding:32px 0; border-bottom:1px solid var(--line); }}
    .two-col {{ display:grid; grid-template-columns:minmax(0,.45fr) minmax(0,1fr); gap:18px; align-items:start; }}
    .panel {{ padding:20px; min-width:0; }}
    .commands {{ list-style:none; padding:0; margin:0; display:grid; gap:10px; }}
    .commands li {{ padding:12px; background:var(--soft); border-radius:8px; }}
    .commands span {{ display:block; color:var(--ink); font-weight:700; margin-bottom:4px; }}
    .evidence-grid {{ display:grid; gap:18px; }}
    .evidence-card {{ padding:20px; min-width:0; }}
    .evidence-card.blocked {{ border-left:4px solid var(--block); }}
    .evidence-card.ready-for-human-review, .evidence-card.ready-to-collect, .check-row.human-required, .check-row.external-required, .check-row.missing, .check-row.blocked {{ border-left:4px solid var(--warn); }}
    .evidence-card.ready-for-submission, .check-row.pass {{ border-left:4px solid var(--pass); }}
    .meta, .check-row dl {{ display:grid; grid-template-columns:96px minmax(0,1fr); gap:8px 12px; }}
    dt {{ color:var(--ink); }}
    dd {{ margin:0; min-width:0; overflow-wrap:anywhere; }}
    code {{ font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size:13px; overflow-wrap:anywhere; }}
    .next-action, .runbook {{ background:var(--soft); border-radius:8px; padding:14px; margin:14px 0; }}
    .next-action p {{ margin-top:0; }}
    .next-action code {{ display:block; margin-top:8px; }}
    .check-grid {{ display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:12px; }}
    .check-row {{ padding:14px; min-width:0; }}
    .check-section {{ margin-top:16px; }}
    .notice {{ background:var(--soft); border-left:4px solid var(--ink); padding:16px; border-radius:8px; }}
    li {{ overflow-wrap:anywhere; }}
    @media (max-width:820px) {{ .stats, .two-col, .check-grid {{ grid-template-columns:1fr; }} h1 {{ font-size:38px; }} .topbar-inner {{ align-items:flex-start; flex-direction:column; }} }}
  </style>
</head>
<body>
  <nav class="topbar"><div class="topbar-inner"><span class="brand">World-Class Preflight</span><div class="links"><a href="#handoff">Handoff</a><a href="#queue">Queue</a><a href="#boundary">Boundary</a></div></div></nav>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">Evidence Collection</span>
      <h1>World-Class Evidence Preflight</h1>
      <p class="lede">This operator view shows which external and human evidence is still blocked, which commands prepare editable submission drafts, and why preflight never counts as accepted evidence.</p>
      <div class="stats">{stat_html}</div>
    </section>
    <section class="section two-col" id="handoff">
      <article class="panel">
        <h2>Submission Kit</h2>
        <p class="muted">Generate drafts only after real provider, human-review, native-permission, or native-client work exists. Drafts remain non-evidence until valid aggregate artifact refs and SHA-256 digests are supplied. Artifact prefill is convenience data only.</p>
        <ul>
          <li>submissions directory: <code>{html_text(report['submissions']['directory'])}</code></li>
          <li>drafts count as evidence: <code>{html_text(str(report['submissions']['drafts_count_as_evidence']).lower())}</code></li>
          <li>artifact prefill counts as evidence: <code>{html_text(str(report['submissions']['artifact_prefill_counts_as_evidence']).lower())}</code></li>
          <li>preflight accepts evidence: <code>{html_text(str(report['summary']['preflight_counts_as_evidence']).lower())}</code></li>
        </ul>
      </article>
      <aside class="panel"><h2>Commands</h2><ul class="commands">{render_html_commands(report['submissions']['commands'])}</ul></aside>
    </section>
    <section class="section" id="queue"><h2>Evidence Queue</h2><div class="evidence-grid">{item_cards}</div></section>
    <section class="section" id="boundary">
      <h2>Safety Boundary</h2>
      <div class="notice"><ul><li>Environment variables are displayed only as set or not-set; secret values are never printed.</li><li>Human-required and external-required states are operator work, not accepted evidence.</li><li>The world-class ledger remains the only source of truth for ready_to_claim_world_class.</li></ul></div>
    </section>
  </main>
</body>
</html>
"""
    return "\n".join(line.rstrip() for line in html.splitlines()) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render collection preflight checks for pending world-class evidence.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--submissions-dir")
    parser.add_argument("--output-json", default="reports/world_class_evidence_preflight.json")
    parser.add_argument("--output-md", default="reports/world_class_evidence_preflight.md")
    parser.add_argument("--output-html", default="reports/world_class_evidence_preflight.html")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    submissions_dir = Path(args.submissions_dir).resolve() if args.submissions_dir else None
    report = build_preflight(skill_dir, args.generated_at, submissions_dir=submissions_dir)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_html = Path(args.output_html)
    if not output_json.is_absolute():
        output_json = skill_dir / output_json
    if not output_md.is_absolute():
        output_md = skill_dir / output_md
    if not output_html.is_absolute():
        output_html = skill_dir / output_html
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    output_html.write_text(render_html(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
