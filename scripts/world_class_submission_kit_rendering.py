#!/usr/bin/env python3
"""Render Markdown and HTML artifacts for world-class submission kits."""

from typing import Any

from html_rendering import html_text


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Shared renderer for world-class submission kit Markdown and HTML artifacts."


def render_readme(report: dict[str, Any]) -> str:
    commands = report["commands"]
    lines = [
        "# World-Class Evidence Submission Kit",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "This kit contains editable drafts for human and external evidence packets. Drafts are not accepted evidence.",
        "",
        "## Workflow",
        "",
        "1. Run the real provider, human review, native permission, or native client telemetry work first.",
        "2. Edit the matching JSON draft with only aggregate artifact references and provenance metadata.",
        "3. Set `template_only` to `false` only after real evidence exists.",
        "4. Set attestation booleans truthfully; do not include credentials, raw prompts, raw outputs, transcripts, notes, or private user content.",
        "5. Validate the packet before asking the ledger reviewer to set `attestation.ledger_reviewer`, `attestation.ledger_reviewed_at`, and `attestation.ledger_reviewer_approved` truthfully.",
        "6. Optional artifact prefill only inserts SHA-256 digests for current local aggregate artifacts; it does not mark a draft as real evidence.",
        "",
        "## Commands",
        "",
        f"- validate intake: `{commands['validate_intake']}`",
        f"- review submission: `{commands['review_submission']}`",
        f"- refresh ledger: `{commands['refresh_ledger']}`",
        f"- guard public claims: `{commands['guard_claim']}`",
        "",
        "## Operator Handoff",
        "",
        "Follow these steps in order when handing the kit from operator to reviewer. Handoff rows are procedural and never count as completion evidence.",
        "",
        "| Step | Status | Command | Completion signal |",
        "| --- | --- | --- | --- |",
    ]
    for item in report.get("operator_handoff", []):
        command = item.get("command") or "manual"
        lines.append(
            f"| `{item['step_id']}` | `{item['status']}` | `{command}` | {item['completion_signal']} |"
        )
    lines.extend(
        [
            "",
        "## Drafts",
        "",
        "| Evidence | Draft | Status | Prefilled refs |",
        "| --- | --- | --- | ---: |",
        ]
    )
    for item in report["files"]:
        lines.append(
            f"| `{item['evidence_key']}` | `{item['output_path']}` | `{item['status']}` | `{item.get('prefilled_artifact_ref_count', 0)}` |"
        )
    lines.extend(
        [
            "",
            "## Evidence Matrix",
            "",
            "This matrix combines draft, artifact, and source-check readiness into one operator action list. Matrix rows are guidance only; they do not count as completion evidence.",
            "",
            "| Evidence | Stage | Draft | Submission refs | Supporting assets | Source checks | Next action |",
            "| --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for item in report.get("evidence_matrix", []):
        lines.append(
            f"| `{item['evidence_key']}` | `{item['stage']}` | `{item['draft_status']}` | "
            f"`{item.get('submission_ref_ready_count', 0)}/{item.get('submission_ref_total_count', 0)}` | "
            f"`{item.get('supporting_artifact_ready_count', 0)}/{item.get('supporting_artifact_total_count', 0)}` | "
            f"`{item['source_pass_count']}/{item['source_check_count']}` | {item['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Repair Checklist",
            "",
            "This checklist turns every draft, artifact, and source blocker into a concrete repair row. Repair rows are procedural guidance and do not count as completion evidence.",
            "",
            "| Evidence | Type | Target | Status | Next action |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    repair_rows = report.get("repair_checklist", [])
    if repair_rows:
        for item in repair_rows:
            lines.append(
                f"| `{item['evidence_key']}` | `{item['repair_type']}` | `{item['target']}` | "
                f"`{item['status']}` | {item['next_action']} |"
            )
    else:
        lines.append("| `all` | `none` | `n/a` | `ready` | No repair rows were generated. |")
    lines.extend(["", "## Execution Runbook", ""])
    for item in report.get("evidence_items", []):
        must_collect = item.get("must_collect", {}) if isinstance(item.get("must_collect", {}), dict) else {}
        runbook = must_collect.get("runbook", [])
        lines.extend(["", f"### {item.get('label', item.get('evidence_key', 'Evidence'))}", ""])
        if runbook:
            for step in runbook:
                lines.append(f"- `{step}`" if str(step).startswith("python3 ") or "=" in str(step) else f"- {step}")
        else:
            lines.append("- No source runbook listed.")
    lines.extend(
        [
            "",
            "## Artifact Checklist",
            "",
            "Use these paths and SHA-256 digests when filling `artifact_refs`. Glob patterns are expanded into concrete files; submissions must reference concrete paths, not globs.",
            "",
            "| Evidence | Role | Path | Status | SHA-256 |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in report.get("artifact_checklist", []):
        digest = item.get("sha256") or "n/a"
        lines.append(
            f"| `{item['evidence_key']}` | `{item.get('artifact_role', 'supporting-evidence')}` | "
            f"`{item['path']}` | `{item['status']}` | `{digest}` |"
        )
    lines.extend(
        [
            "",
            "## Source Evidence Snapshot",
            "",
            "These checks explain why a draft is not ready for ledger acceptance yet. They mirror current aggregate reports and do not accept evidence by themselves.",
            "",
            "| Evidence | Check | Current | Expected | Status |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in report.get("source_checklist", []):
        lines.append(
            f"| `{item['evidence_key']}` | {item['label']} | `{item['actual']}` | `{item['expected']}` | `{item['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Anti-Overclaim",
            "",
            "- This kit never marks ledger evidence as accepted.",
            "- Planned work, metadata fallback, pending review, and local command-runner output remain non-evidence.",
            "- A valid intake packet means ready for ledger review, not world-class completion.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def render_html_list(values: list[Any], empty: str) -> str:
    if not values:
        return f"<li>{html_text(empty)}</li>"
    return "".join(f"<li>{html_text(value)}</li>" for value in values)


def render_html_commands(commands: dict[str, str]) -> str:
    return "".join(
        f"<li><span>{html_text(label.replace('_', ' '))}</span><code>{html_text(command)}</code></li>"
        for label, command in commands.items()
    )


def render_html_files(files: list[dict[str, Any]]) -> str:
    if not files:
        return '<p class="muted">No submission drafts were requested.</p>'
    return "".join(
        """
        <article class="draft-card {status}">
          <div>
            <span>{status}</span>
            <h3>{key}</h3>
          </div>
          <dl>
            <dt>Template</dt><dd><code>{template}</code></dd>
            <dt>Draft</dt><dd><code>{output}</code></dd>
            <dt>Prefill</dt><dd>{prefill} artifact refs</dd>
          </dl>
          {errors}
        </article>
        """.format(
            status=html_text(item.get("status", "")),
            key=html_text(item.get("evidence_key", "")),
            template=html_text(item.get("template_path", "")),
            output=html_text(item.get("output_path", "")),
            prefill=html_text(item.get("prefilled_artifact_ref_count", 0)),
            errors=(
                '<ul class="errors">'
                + render_html_list(item.get("errors", []), "No errors.")
                + "</ul>"
                if item.get("errors")
                else ""
            ),
        )
        for item in files
    )


def render_html_artifact_checklist(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="muted">No required artifacts were listed for the requested evidence.</p>'
    return "".join(
        """
        <article class="artifact-card {status}">
          <div>
            <span>{key}</span>
            <h3>{path}</h3>
          </div>
          <dl>
            <dt>Pattern</dt><dd><code>{pattern}</code></dd>
            <dt>Role</dt><dd>{role}</dd>
            <dt>Status</dt><dd>{status}</dd>
            <dt>SHA-256</dt><dd><code>{sha}</code></dd>
          </dl>
        </article>
        """.format(
            status=html_text(item.get("status", "")),
            key=html_text(item.get("evidence_key", "")),
            path=html_text(item.get("path", "")),
            pattern=html_text(item.get("source_pattern", "")),
            role=html_text(item.get("artifact_role", "supporting-evidence")),
            sha=html_text(item.get("sha256") or "n/a"),
        )
        for item in items
    )


def render_html_source_checklist(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="muted">No source checks were listed for the requested evidence.</p>'
    return "".join(
        """
        <article class="source-card {status}">
          <div>
            <span>{key}</span>
            <h3>{label}</h3>
          </div>
          <dl>
            <dt>Field</dt><dd><code>{field}</code></dd>
            <dt>Current</dt><dd><code>{actual}</code></dd>
            <dt>Expected</dt><dd><code>{expected}</code></dd>
            <dt>Action</dt><dd>{action}</dd>
          </dl>
        </article>
        """.format(
            status=html_text(item.get("status", "")),
            key=html_text(item.get("evidence_key", "")),
            label=html_text(item.get("label", "")),
            field=html_text(item.get("field", "")),
            actual=html_text(item.get("actual", "")),
            expected=html_text(item.get("expected", "")),
            action=html_text(item.get("next_action", "")),
        )
        for item in items
    )


def render_html_matrix(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="muted">No evidence matrix rows were generated.</p>'
    return "".join(
        """
        <article class="matrix-card {stage}">
          <header>
            <span>{stage}</span>
            <h3>{key}</h3>
          </header>
          <dl>
            <dt>Draft</dt><dd>{draft}</dd>
            <dt>Submission refs</dt><dd>{submission_ref_ready}/{submission_ref_total} ready</dd>
            <dt>Supporting assets</dt><dd>{supporting_ready}/{supporting_total} ready</dd>
            <dt>Source</dt><dd>{source_pass}/{source_total} pass</dd>
            <dt>Owner</dt><dd>{owner}</dd>
          </dl>
          <p>{action}</p>
        </article>
        """.format(
            stage=html_text(item.get("stage", "")),
            key=html_text(item.get("evidence_key", "")),
            draft=html_text(item.get("draft_status", "")),
            submission_ref_ready=html_text(item.get("submission_ref_ready_count", 0)),
            submission_ref_total=html_text(item.get("submission_ref_total_count", 0)),
            supporting_ready=html_text(item.get("supporting_artifact_ready_count", 0)),
            supporting_total=html_text(item.get("supporting_artifact_total_count", 0)),
            source_pass=html_text(item.get("source_pass_count", 0)),
            source_total=html_text(item.get("source_check_count", 0)),
            owner=html_text(item.get("owner", "")),
            action=html_text(item.get("next_action", "")),
        )
        for item in items
    )


def render_html_repair_checklist(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="muted">No repair rows were generated.</p>'
    return "".join(
        """
        <article class="repair-card {status}">
          <header>
            <span>{key} · {repair_type}</span>
            <h3>{target}</h3>
          </header>
          <dl>
            <dt>Status</dt><dd>{status}</dd>
            <dt>Reason</dt><dd>{reason}</dd>
            <dt>Action</dt><dd>{action}</dd>
            <dt>Evidence</dt><dd>does not count as completion</dd>
          </dl>
        </article>
        """.format(
            status=html_text(item.get("status", "")),
            key=html_text(item.get("evidence_key", "")),
            repair_type=html_text(item.get("repair_type", "")),
            target=html_text(item.get("target", "")),
            reason=html_text(item.get("blocking_reason", "")),
            action=html_text(item.get("next_action", "")),
        )
        for item in items
    )


def render_html_handoff(items: list[dict[str, Any]]) -> str:
    if not items:
        return '<p class="muted">No operator handoff steps were generated.</p>'
    return "".join(
        """
        <article class="handoff-card {status}">
          <header>
            <span>{status}</span>
            <h3>{label}</h3>
          </header>
          <dl>
            <dt>Step</dt><dd><code>{step}</code></dd>
            <dt>Command</dt><dd><code>{command}</code></dd>
            <dt>Signal</dt><dd>{signal}</dd>
            <dt>Evidence</dt><dd>{counts}</dd>
          </dl>
          <p>{blocking}</p>
        </article>
        """.format(
            status=html_text(item.get("status", "")),
            label=html_text(item.get("label", "")),
            step=html_text(item.get("step_id", "")),
            command=html_text(item.get("command") or "manual"),
            signal=html_text(item.get("completion_signal", "")),
            counts="does not count as completion" if item.get("counts_as_completion") is False else "review required",
            blocking=html_text(item.get("blocking_condition", "")),
        )
        for item in items
    )


def render_html_item(item: dict[str, Any]) -> str:
    must_collect = item.get("must_collect", {}) if isinstance(item.get("must_collect", {}), dict) else {}
    runbook = must_collect.get("runbook", [])
    return f"""
      <article class="evidence-card {html_text(item.get('readiness', ''))}">
        <header>
          <span>{html_text(item.get('category', ''))} · {html_text(item.get('readiness', ''))}</span>
          <h3>{html_text(item.get('label', item.get('evidence_key', '')))}</h3>
        </header>
        <p>{html_text(item.get('blocking_reason', ''))}</p>
        <dl>
          <dt>Owner</dt><dd>{html_text(item.get('owner', ''))}</dd>
          <dt>Evidence</dt><dd><code>{html_text(item.get('evidence_key', ''))}</code></dd>
          <dt>Submission</dt><dd><code>{html_text(item.get('submission_path', ''))}</code></dd>
        </dl>
        <section class="runbook-panel">
          <h4>Execution Runbook</h4>
          <ul>{render_html_list(runbook, 'No source runbook listed.')}</ul>
        </section>
        <div class="mini-grid">
          <section>
            <h4>Must Collect</h4>
            <ul>{render_html_list(must_collect.get('provenance_requirements', []), 'No provenance requirements listed.')}</ul>
          </section>
          <section>
            <h4>Pass Checks</h4>
            <ul>{render_html_list(must_collect.get('success_checks', []), 'No success checks listed.')}</ul>
          </section>
          <section>
            <h4>Privacy</h4>
            <ul>{render_html_list(must_collect.get('privacy_contract', []), 'No privacy contract listed.')}</ul>
          </section>
        </div>
      </article>
    """


def render_html(report: dict[str, Any]) -> str:
    summary = report["summary"]
    artifact_ready = summary.get("artifact_ready_count", 0)
    artifact_total = summary.get("artifact_checklist_count", 0)
    submission_ref_ready = summary.get("submission_ref_ready_count", 0)
    submission_ref_total = summary.get("submission_ref_count", 0)
    stats = [
        ("Requested", summary["requested_count"]),
        ("Written", summary["written_count"]),
        ("Existing", summary["existing_count"]),
        ("Skipped", summary["skipped_count"]),
        ("Submit refs", f"{submission_ref_ready}/{submission_ref_total}"),
        ("Support", f"{artifact_ready - submission_ref_ready}/{artifact_total - submission_ref_total}"),
        ("Prefilled", summary.get("artifact_ref_prefill_count", 0)),
    ]
    stat_html = "".join(
        f"<article><span>{html_text(label)}</span><strong>{html_text(value)}</strong></article>"
        for label, value in stats
    )
    evidence_html = "".join(render_html_item(item) for item in report.get("evidence_items", []))
    matrix_html = render_html_matrix(report.get("evidence_matrix", []))
    repair_html = render_html_repair_checklist(report.get("repair_checklist", []))
    handoff_html = render_html_handoff(report.get("operator_handoff", []))
    artifact_html = render_html_artifact_checklist(report.get("artifact_checklist", []))
    source_html = render_html_source_checklist(report.get("source_checklist", []))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>World-Class Evidence Submission Kit</title>
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
    .stats {{ display:grid; grid-template-columns:repeat(6, minmax(0,1fr)); gap:12px; margin:26px 0 0; }}
    .stats article, .panel, .draft-card, .evidence-card {{ border:1px solid var(--line); border-radius:8px; background:#fff; }}
    .stats article {{ padding:16px; }}
    .stats span, .draft-card span, .evidence-card span, .muted {{ color:var(--muted); }}
    .stats strong {{ display:block; color:var(--ink); font-size:34px; line-height:1; }}
    .section {{ padding:32px 0; border-bottom:1px solid var(--line); }}
    .panel {{ padding:20px; }}
    .two-col {{ display:grid; grid-template-columns:minmax(0, .45fr) minmax(0, 1fr); gap:18px; align-items:start; }}
    .draft-grid, .evidence-grid, .artifact-grid, .source-grid, .matrix-grid, .repair-grid, .handoff-grid {{ display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:16px; }}
    .draft-card, .evidence-card, .artifact-card, .source-card, .matrix-card, .repair-card, .handoff-card {{ padding:18px; min-width:0; border:1px solid var(--line); border-radius:8px; background:#fff; }}
    .draft-card.written, .draft-card.exists {{ border-left:4px solid var(--pass); }}
    .draft-card.skipped {{ border-left:4px solid var(--warn); }}
    .matrix-card.collect-source, .matrix-card.prepare-draft, .matrix-card.fix-artifacts, .matrix-card.fix-draft {{ border-left:4px solid var(--warn); }}
    .matrix-card.validate-packet {{ border-left:4px solid var(--pass); }}
    .repair-card.blocked {{ border-left:4px solid var(--warn); }}
    .repair-card.ready {{ border-left:4px solid var(--pass); }}
    .handoff-card.blocked, .handoff-card.fix-required {{ border-left:4px solid var(--warn); }}
    .handoff-card.ready {{ border-left:4px solid var(--pass); }}
    .evidence-card.awaiting-submission, .evidence-card.fix-submission, .evidence-card.fix-template, .artifact-card.missing, .artifact-card.glob-no-match, .artifact-card.unsafe-path, .artifact-card.raw-content-disallowed {{ border-left:4px solid var(--warn); }}
    .artifact-card.ready {{ border-left:4px solid var(--pass); }}
    .source-card.blocked {{ border-left:4px solid var(--warn); }}
    .source-card.pass {{ border-left:4px solid var(--pass); }}
    dl {{ display:grid; grid-template-columns:96px minmax(0,1fr); gap:8px 12px; }}
    dt {{ color:var(--ink); }}
    dd {{ margin:0; min-width:0; overflow-wrap:anywhere; }}
    code {{ font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size:13px; overflow-wrap:anywhere; }}
    ul, ol {{ padding-left:20px; }}
    .commands {{ list-style:none; padding:0; margin:0; display:grid; gap:10px; }}
    .commands li {{ padding:12px; background:var(--soft); border-radius:8px; }}
    .commands span {{ display:block; color:var(--ink); font-weight:700; margin-bottom:4px; }}
    .mini-grid {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:12px; margin-top:14px; }}
    .mini-grid section, .runbook-panel {{ background:var(--soft); border-radius:8px; padding:14px; min-width:0; }}
    .mini-grid li, .runbook-panel li, .notice li {{ overflow-wrap:anywhere; }}
    .notice {{ background:var(--soft); border-left:4px solid var(--ink); padding:16px; border-radius:8px; }}
    .errors {{ color:var(--warn); }}
    @media (max-width:820px) {{ .stats, .two-col, .draft-grid, .evidence-grid, .artifact-grid, .source-grid, .matrix-grid, .repair-grid, .handoff-grid, .mini-grid {{ grid-template-columns:1fr; }} h1 {{ font-size:38px; }} .topbar-inner {{ align-items:flex-start; flex-direction:column; }} }}
  </style>
</head>
<body>
  <nav class="topbar"><div class="topbar-inner"><span class="brand">World-Class Kit</span><div class="links"><a href="#workflow">Workflow</a><a href="#handoff">Handoff</a><a href="#matrix">Matrix</a><a href="#repair">Repair</a><a href="#drafts">Drafts</a><a href="#artifacts">Artifacts</a><a href="#source">Source</a><a href="#evidence">Evidence</a><a href="#safety">Safety</a></div></div></nav>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">Evidence Intake</span>
      <h1>World-Class Evidence Submission Kit</h1>
      <p class="lede">Use this cockpit to prepare human and external evidence packets. Drafts are not accepted evidence, artifact prefill only inserts local SHA-256 digests, and this page never changes the ledger result.</p>
      <div class="stats">{stat_html}</div>
    </section>
    <section class="section two-col" id="workflow">
      <article class="panel"><h2>Workflow</h2><ol><li>Run the real provider, human review, native permission, or native client telemetry work first.</li><li>Edit the matching JSON draft with aggregate artifact references and provenance metadata.</li><li>Set template_only to false only after real evidence exists.</li><li>Use prefilled SHA-256 values as convenience data, not evidence acceptance.</li><li>Validate intake, ask the ledger reviewer to approve explicitly, refresh the ledger, then guard public claims.</li></ol></article>
      <aside class="panel"><h2>Commands</h2><ul class="commands">{render_html_commands(report['commands'])}</ul></aside>
    </section>
    <section class="section" id="handoff"><h2>Operator Handoff</h2><p class="muted">These ordered steps make the operator-to-reviewer handoff auditable. They are procedural guardrails and never count as world-class evidence.</p><div class="handoff-grid">{handoff_html}</div></section>
    <section class="section" id="matrix"><h2>Evidence Matrix</h2><p class="muted">The matrix separates submission artifact_refs from supporting assets, then combines draft status, source checks, and the next operator action. It is guidance only and never counts as accepted evidence.</p><div class="matrix-grid">{matrix_html}</div></section>
    <section class="section" id="repair"><h2>Repair Checklist</h2><p class="muted">Each row names one concrete blocker and the next action required before ledger review. This checklist does not count as completion evidence.</p><div class="repair-grid">{repair_html}</div></section>
    <section class="section" id="drafts"><h2>Drafts</h2><div class="draft-grid">{render_html_files(report['files'])}</div></section>
    <section class="section" id="artifacts"><h2>Artifact Checklist</h2><p class="muted">Rows marked submission-ref are the paths expected in artifact_refs. Supporting-evidence rows help reviewers audit the packet but do not all need to be copied into the submission. Glob patterns are expanded for operator convenience only.</p><div class="artifact-grid">{artifact_html}</div></section>
    <section class="section" id="source"><h2>Source Evidence Snapshot</h2><p class="muted">This section shows current aggregate source checks. It explains remaining blockers without changing the ledger.</p><div class="source-grid">{source_html}</div></section>
    <section class="section" id="evidence"><h2>Evidence Requirements</h2><div class="evidence-grid">{evidence_html}</div></section>
    <section class="section" id="safety"><h2>Safety Boundary</h2><div class="notice"><ul><li>Drafts never count as accepted ledger evidence.</li><li>Valid intake means ready for ledger review, not world-class completion.</li><li>Do not include credentials, raw prompts, raw outputs, transcripts, notes, or private user content.</li></ul></div></section>
  </main>
</body>
</html>
"""
