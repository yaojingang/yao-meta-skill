#!/usr/bin/env python3
import argparse
import hashlib
import html
import json
import shlex
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from render_world_class_evidence_intake import build_intake
from world_class_evidence_contract import DISALLOWED_REAL_ARTIFACTS


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Prepares editable world-class evidence intake packets without counting drafts as accepted evidence."


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def shell_path(path: Path, root: Path) -> str:
    return shlex.quote(rel_path(path, root))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def html_text(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def has_glob_pattern(value: str) -> bool:
    return any(token in value for token in ("*", "?", "["))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def requested_checklist_items(intake: dict[str, Any], evidence_keys: list[str]) -> list[dict[str, Any]]:
    items = intake.get("operator_checklist", [])
    if not evidence_keys:
        return items
    requested = set(evidence_keys)
    return [item for item in items if item.get("evidence_key") in requested]


def template_result_by_key(intake: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("evidence_key")): item for item in intake.get("templates", [])}


def copy_template(
    skill_dir: Path,
    output_dir: Path,
    item: dict[str, Any],
    template_results: dict[str, dict[str, Any]],
    overwrite: bool,
) -> dict[str, Any]:
    key = str(item.get("evidence_key", ""))
    template_result = template_results.get(key, {})
    template_path = skill_dir / str(item.get("template_path", ""))
    output_path = output_dir / f"{key}.json"
    errors: list[str] = []

    if template_result.get("status") != "pass":
        errors.append("template failed intake validation")
    if not template_path.exists():
        errors.append("template file is missing")

    if errors:
        return {
            "evidence_key": key,
            "status": "skipped",
            "template_path": rel_path(template_path, skill_dir),
            "output_path": rel_path(output_path, skill_dir),
            "errors": errors,
        }

    if output_path.exists() and not overwrite:
        return {
            "evidence_key": key,
            "status": "exists",
            "template_path": rel_path(template_path, skill_dir),
            "output_path": rel_path(output_path, skill_dir),
            "errors": [],
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template_path, output_path)
    return {
        "evidence_key": key,
        "status": "written",
        "template_path": rel_path(template_path, skill_dir),
        "output_path": rel_path(output_path, skill_dir),
        "errors": [],
    }


def artifact_row(skill_dir: Path, evidence_key: str, pattern: str, path: Path, status: str) -> dict[str, Any]:
    exists = path.exists()
    is_file = exists and path.is_file()
    relative = rel_path(path, skill_dir) if exists else pattern
    contains_raw_content = relative in DISALLOWED_REAL_ARTIFACTS
    digest = sha256_file(path) if is_file and not contains_raw_content else ""
    row_status = status if status else ("ready" if is_file else "missing")
    if contains_raw_content:
        row_status = "raw-content-disallowed"
    return {
        "evidence_key": evidence_key,
        "source_pattern": pattern,
        "path": relative,
        "status": row_status,
        "exists": exists,
        "is_file": is_file,
        "sha256": digest,
        "artifact_ref_ready": bool(is_file and digest and not contains_raw_content),
        "copy_path": relative if is_file else "",
        "copy_sha256": digest,
        "contains_raw_content": contains_raw_content,
        "concrete_reference_required": has_glob_pattern(pattern),
    }


def artifact_checklist_for_item(skill_dir: Path, item: dict[str, Any]) -> list[dict[str, Any]]:
    key = str(item.get("evidence_key", ""))
    must_collect = item.get("must_collect", {}) if isinstance(item.get("must_collect", {}), dict) else {}
    artifacts = must_collect.get("evidence_artifacts", [])
    if not isinstance(artifacts, list):
        return []
    rows: list[dict[str, Any]] = []
    for artifact in artifacts:
        pattern = str(artifact or "").strip()
        if not pattern:
            continue
        if Path(pattern).is_absolute() or ".." in Path(pattern).parts:
            rows.append(
                {
                    "evidence_key": key,
                    "source_pattern": pattern,
                    "path": pattern,
                    "status": "unsafe-path",
                    "exists": False,
                    "is_file": False,
                    "sha256": "",
                    "artifact_ref_ready": False,
                    "copy_path": "",
                    "copy_sha256": "",
                    "contains_raw_content": False,
                    "concrete_reference_required": True,
                }
            )
            continue
        if has_glob_pattern(pattern):
            matches = sorted(path for path in skill_dir.glob(pattern) if path.is_file())
            if not matches:
                rows.append(
                    {
                        "evidence_key": key,
                        "source_pattern": pattern,
                        "path": pattern,
                        "status": "glob-no-match",
                        "exists": False,
                        "is_file": False,
                        "sha256": "",
                        "artifact_ref_ready": False,
                        "copy_path": "",
                        "copy_sha256": "",
                        "contains_raw_content": False,
                        "concrete_reference_required": True,
                    }
                )
                continue
            for match in matches:
                rows.append(artifact_row(skill_dir, key, pattern, match, "ready"))
            continue
        rows.append(artifact_row(skill_dir, key, pattern, skill_dir / pattern, ""))
    return rows


def build_artifact_checklist(skill_dir: Path, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        rows.extend(artifact_checklist_for_item(skill_dir, item))
    return rows


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
        "5. Validate the packet before asking the ledger reviewer to accept it.",
        "",
        "## Commands",
        "",
        f"- validate intake: `{commands['validate_intake']}`",
        f"- refresh ledger: `{commands['refresh_ledger']}`",
        f"- guard public claims: `{commands['guard_claim']}`",
        "",
        "## Drafts",
        "",
        "| Evidence | Draft | Status |",
        "| --- | --- | --- |",
    ]
    for item in report["files"]:
        lines.append(f"| `{item['evidence_key']}` | `{item['output_path']}` | `{item['status']}` |")
    lines.extend(
        [
            "",
            "## Artifact Checklist",
            "",
            "Use these paths and SHA-256 digests when filling `artifact_refs`. Glob patterns are expanded into concrete files; submissions must reference concrete paths, not globs.",
            "",
            "| Evidence | Path | Status | SHA-256 |",
            "| --- | --- | --- | --- |",
        ]
    )
    for item in report.get("artifact_checklist", []):
        digest = item.get("sha256") or "n/a"
        lines.append(
            f"| `{item['evidence_key']}` | `{item['path']}` | `{item['status']}` | `{digest}` |"
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
        return "<p class=\"muted\">No submission drafts were requested.</p>"
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
          </dl>
          {errors}
        </article>
        """.format(
            status=html_text(item.get("status", "")),
            key=html_text(item.get("evidence_key", "")),
            template=html_text(item.get("template_path", "")),
            output=html_text(item.get("output_path", "")),
            errors=(
                "<ul class=\"errors\">"
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
        return "<p class=\"muted\">No required artifacts were listed for the requested evidence.</p>"
    return "".join(
        """
        <article class="artifact-card {status}">
          <div>
            <span>{key}</span>
            <h3>{path}</h3>
          </div>
          <dl>
            <dt>Pattern</dt><dd><code>{pattern}</code></dd>
            <dt>Status</dt><dd>{status}</dd>
            <dt>SHA-256</dt><dd><code>{sha}</code></dd>
          </dl>
        </article>
        """.format(
            status=html_text(item.get("status", "")),
            key=html_text(item.get("evidence_key", "")),
            path=html_text(item.get("path", "")),
            pattern=html_text(item.get("source_pattern", "")),
            sha=html_text(item.get("sha256") or "n/a"),
        )
        for item in items
    )


def render_html_item(item: dict[str, Any]) -> str:
    must_collect = item.get("must_collect", {}) if isinstance(item.get("must_collect", {}), dict) else {}
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
    stats = [
        ("Requested", summary["requested_count"]),
        ("Written", summary["written_count"]),
        ("Existing", summary["existing_count"]),
        ("Skipped", summary["skipped_count"]),
        ("Artifacts", f"{artifact_ready}/{artifact_total}"),
    ]
    stat_html = "".join(f"<article><span>{html_text(label)}</span><strong>{html_text(value)}</strong></article>" for label, value in stats)
    evidence_html = "".join(render_html_item(item) for item in report.get("evidence_items", []))
    artifact_html = render_html_artifact_checklist(report.get("artifact_checklist", []))
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
    .stats {{ display:grid; grid-template-columns:repeat(5, minmax(0,1fr)); gap:12px; margin:26px 0 0; }}
    .stats article, .panel, .draft-card, .evidence-card {{ border:1px solid var(--line); border-radius:8px; background:#fff; }}
    .stats article {{ padding:16px; }}
    .stats span, .draft-card span, .evidence-card span, .muted {{ color:var(--muted); }}
    .stats strong {{ display:block; color:var(--ink); font-size:34px; line-height:1; }}
    .section {{ padding:32px 0; border-bottom:1px solid var(--line); }}
    .panel {{ padding:20px; }}
    .two-col {{ display:grid; grid-template-columns:minmax(0, .45fr) minmax(0, 1fr); gap:18px; align-items:start; }}
    .draft-grid, .evidence-grid, .artifact-grid {{ display:grid; grid-template-columns:repeat(2, minmax(0,1fr)); gap:16px; }}
    .draft-card, .evidence-card, .artifact-card {{ padding:18px; min-width:0; }}
    .draft-card.written, .draft-card.exists {{ border-left:4px solid var(--pass); }}
    .draft-card.skipped {{ border-left:4px solid var(--warn); }}
    .evidence-card.awaiting-submission, .evidence-card.fix-submission, .evidence-card.fix-template, .artifact-card.missing, .artifact-card.glob-no-match, .artifact-card.unsafe-path, .artifact-card.raw-content-disallowed {{ border-left:4px solid var(--warn); }}
    .artifact-card.ready {{ border-left:4px solid var(--pass); }}
    dl {{ display:grid; grid-template-columns:96px minmax(0,1fr); gap:8px 12px; }}
    dt {{ color:var(--ink); }}
    dd {{ margin:0; min-width:0; overflow-wrap:anywhere; }}
    code {{ font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size:13px; overflow-wrap:anywhere; }}
    ul, ol {{ padding-left:20px; }}
    .commands {{ list-style:none; padding:0; margin:0; display:grid; gap:10px; }}
    .commands li {{ padding:12px; background:var(--soft); border-radius:8px; }}
    .commands span {{ display:block; color:var(--ink); font-weight:700; margin-bottom:4px; }}
    .mini-grid {{ display:grid; grid-template-columns:repeat(3, minmax(0,1fr)); gap:12px; margin-top:14px; }}
    .mini-grid section {{ background:var(--soft); border-radius:8px; padding:14px; min-width:0; }}
    .mini-grid li, .notice li {{ overflow-wrap:anywhere; }}
    .notice {{ background:var(--soft); border-left:4px solid var(--ink); padding:16px; border-radius:8px; }}
    .errors {{ color:var(--warn); }}
    @media (max-width:820px) {{ .stats, .two-col, .draft-grid, .evidence-grid, .artifact-grid, .mini-grid {{ grid-template-columns:1fr; }} h1 {{ font-size:38px; }} .topbar-inner {{ align-items:flex-start; flex-direction:column; }} }}
  </style>
</head>
<body>
  <nav class="topbar"><div class="topbar-inner"><span class="brand">World-Class Kit</span><div class="links"><a href="#workflow">Workflow</a><a href="#drafts">Drafts</a><a href="#artifacts">Artifacts</a><a href="#evidence">Evidence</a><a href="#safety">Safety</a></div></div></nav>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">Evidence Intake</span>
      <h1>World-Class Evidence Submission Kit</h1>
      <p class="lede">Use this cockpit to prepare human and external evidence packets. Drafts are not accepted evidence, and this page never changes the ledger result.</p>
      <div class="stats">{stat_html}</div>
    </section>
    <section class="section two-col" id="workflow">
      <article class="panel"><h2>Workflow</h2><ol><li>Run the real provider, human review, native permission, or native client telemetry work first.</li><li>Edit the matching JSON draft with aggregate artifact references and provenance metadata.</li><li>Set template_only to false only after real evidence exists.</li><li>Validate intake, refresh the ledger, then guard public claims.</li></ol></article>
      <aside class="panel"><h2>Commands</h2><ul class="commands">{render_html_commands(report['commands'])}</ul></aside>
    </section>
    <section class="section" id="drafts"><h2>Drafts</h2><div class="draft-grid">{render_html_files(report['files'])}</div></section>
    <section class="section" id="artifacts"><h2>Artifact Checklist</h2><p class="muted">Copy concrete paths and SHA-256 digests from here into artifact_refs after real evidence exists. Glob patterns are expanded for operator convenience only.</p><div class="artifact-grid">{artifact_html}</div></section>
    <section class="section" id="evidence"><h2>Evidence Requirements</h2><div class="evidence-grid">{evidence_html}</div></section>
    <section class="section" id="safety"><h2>Safety Boundary</h2><div class="notice"><ul><li>Drafts never count as accepted ledger evidence.</li><li>Valid intake means ready for ledger review, not world-class completion.</li><li>Do not include credentials, raw prompts, raw outputs, transcripts, notes, or private user content.</li></ul></div></section>
  </main>
</body>
</html>
"""


def build_submission_kit(
    skill_dir: Path,
    output_dir: Path,
    generated_at: str,
    evidence_keys: list[str] | None = None,
    overwrite: bool = False,
    output_html: Path | None = None,
) -> dict[str, Any]:
    intake = build_intake(skill_dir, generated_at, submissions_dir=output_dir)
    items = requested_checklist_items(intake, evidence_keys or [])
    valid_keys = {str(item.get("evidence_key")) for item in intake.get("operator_checklist", [])}
    unknown_keys = sorted(set(evidence_keys or []) - valid_keys)
    template_results = template_result_by_key(intake)
    files = [copy_template(skill_dir, output_dir, item, template_results, overwrite) for item in items]
    artifact_checklist = build_artifact_checklist(skill_dir, items)
    manifest_path = output_dir / "submission_manifest.json"
    readme_path = output_dir / "README.md"
    output_html = output_html or (output_dir / "index.html")
    written_count = sum(1 for item in files if item["status"] == "written")
    existing_count = sum(1 for item in files if item["status"] == "exists")
    skipped_count = sum(1 for item in files if item["status"] == "skipped")
    artifact_ready_count = sum(1 for item in artifact_checklist if item.get("artifact_ref_ready"))
    artifact_missing_count = sum(1 for item in artifact_checklist if not item.get("artifact_ref_ready"))
    artifact_glob_count = sum(1 for item in artifact_checklist if item.get("concrete_reference_required"))
    ok = not unknown_keys and skipped_count == 0
    report = {
        "schema_version": "1.0",
        "ok": ok,
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        "output_dir": rel_path(output_dir, skill_dir),
        "summary": {
            "requested_count": len(items) + len(unknown_keys),
            "prepared_count": len(files),
            "written_count": written_count,
            "existing_count": existing_count,
            "skipped_count": skipped_count,
            "unknown_key_count": len(unknown_keys),
            "artifact_checklist_count": len(artifact_checklist),
            "artifact_ready_count": artifact_ready_count,
            "artifact_missing_count": artifact_missing_count,
            "artifact_glob_expansion_count": artifact_glob_count,
            "drafts_count_as_evidence": False,
            "ledger_counts_submission_as_completion": False,
            "decision": "submission-kit-ready" if ok else "fix-submission-kit",
        },
        "unknown_evidence_keys": unknown_keys,
        "files": files,
        "artifact_checklist": artifact_checklist,
        "evidence_items": items,
        "commands": {
            "validate_intake": f"python3 scripts/yao.py world-class-intake . --submissions-dir {shell_path(output_dir, skill_dir)}",
            "refresh_ledger": f"python3 scripts/yao.py world-class-ledger . --submissions-dir {shell_path(output_dir, skill_dir)}",
            "guard_claim": "python3 scripts/yao.py world-class-claim-guard .",
        },
        "safety": {
            "template_only_drafts": True,
            "real_evidence_required_before_template_only_false": True,
            "raw_content_allowed": False,
            "credentials_allowed": False,
            "drafts_count_as_evidence": False,
        },
        "artifacts": {
            "manifest": rel_path(manifest_path, skill_dir),
            "readme": rel_path(readme_path, skill_dir),
            "html": rel_path(output_html, skill_dir),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(manifest_path, report)
    readme_path.write_text(render_readme(report), encoding="utf-8")
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(render_html(report), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare editable world-class evidence submission drafts.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-dir", default="evidence/world_class/submission-kit")
    parser.add_argument("--evidence-key", action="append", default=[])
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    parser.add_argument("--output-html")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = skill_dir / output_dir
    report = build_submission_kit(
        skill_dir,
        output_dir.resolve(),
        args.generated_at,
        evidence_keys=args.evidence_key,
        overwrite=args.overwrite,
        output_html=Path(args.output_html).resolve() if args.output_html else None,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
