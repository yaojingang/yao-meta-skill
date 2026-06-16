#!/usr/bin/env python3
"""HTML layout helpers for the world-class evidence preflight report."""

from typing import Any

from html_rendering import html_text


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_world_class_preflight.py to keep preflight HTML layout out of data assembly."


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


def render_html_artifact_roles(contract: dict[str, Any]) -> str:
    cards = []
    for role in contract.get("roles", []):
        role_name = str(role.get("role", ""))
        if role_name == "submission-ref":
            ready = f"{contract.get('submission_ref_ready_count', 0)}/{contract.get('submission_ref_total_count', 0)} ready"
        else:
            ready = (
                f"{contract.get('supporting_evidence_ready_count', 0)}/"
                f"{contract.get('supporting_evidence_total_count', 0)} ready"
            )
        cards.append(
            """
        <article class="role-card">
          <span>{label}</span>
          <h3>{role}</h3>
          <strong>{ready}</strong>
          <p>{description}</p>
          <small>copy to artifact_refs: <code>{copy}</code></small>
        </article>
        """.format(
                label=html_text(role.get("label", "")),
                role=html_text(role_name),
                ready=html_text(ready),
                description=html_text(role.get("description", "")),
                copy=html_text(str(role.get("copy_to_artifact_refs") is True).lower()),
            )
        )
    return "".join(cards)


def render_html_item(item: dict[str, Any]) -> str:
    role_contract = item.get("submission_kit", {}).get("artifact_role_contract", {})
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
          <h4>Artifact Roles</h4>
          <div class="role-grid compact">{render_html_artifact_roles(role_contract)}</div>
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
    role_contract = report["submissions"]["artifact_role_contract"]
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
    .role-grid {{ display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:12px; margin-top:16px; }}
    .role-grid.compact {{ margin-top:0; }}
    .role-card {{ border:1px solid var(--line); border-radius:8px; padding:14px; background:#fff; min-width:0; }}
    .role-card span, .role-card small {{ color:var(--muted); }}
    .role-card strong {{ display:block; color:var(--ink); font-size:22px; margin:4px 0 6px; overflow-wrap:anywhere; }}
    .role-card p {{ margin:0 0 8px; }}
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
    @media (max-width:820px) {{ .stats, .two-col, .check-grid, .role-grid {{ grid-template-columns:1fr; }} h1 {{ font-size:38px; }} .topbar-inner {{ align-items:flex-start; flex-direction:column; }} }}
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
        <div class="role-grid">{render_html_artifact_roles(role_contract)}</div>
        <p class="muted"><code>submission-ref</code> rows are the paths expected in <code>artifact_refs</code>; <code>supporting-evidence</code> rows stay available for audit context.</p>
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
