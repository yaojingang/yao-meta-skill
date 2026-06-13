#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path

from review_viewer_data import (
    architecture_steps,
    benchmark_cards,
    compare_rows,
    ensure_report_inputs,
    evidence_readiness,
    synthesis_cards,
    variant_diff_cards,
)


def render_html(report: dict) -> str:
    overview = report["overview"]
    intent = report["intent"]
    intent_confidence = report.get("intent_confidence", {})
    reference = report["reference"]
    iteration = report["iteration"]
    directions = iteration.get("directions", [])[:3]
    feedback = report.get("feedback", {})
    baseline = report.get("baseline", {})
    compare = report.get("compare", {})
    promotion = report.get("promotion", {})
    benchmark = report.get("benchmark", {})
    reference_synthesis = report.get("reference_synthesis", {})
    output_risk = report.get("output_risk", {})
    artifact_design = report.get("artifact_design", {})
    prompt_quality = report.get("prompt_quality", {})
    architecture = architecture_steps(overview)
    compare_table_rows = compare_rows(compare)
    benchmark_rows = benchmark_cards(benchmark)
    synthesis_rows = synthesis_cards(reference_synthesis)
    variant_cards = variant_diff_cards(compare)
    readiness = evidence_readiness(report)

    strength_items = "".join(f"<li>{html.escape(item)}</li>" for item in overview.get("strengths", []))
    logic_items = "".join(f"<li>{html.escape(item)}</li>" for item in overview.get("logic_steps", []))
    usage_items = "".join(f"<li>{html.escape(item)}</li>" for item in overview.get("usage_steps", []))
    question_items = "".join(
        f"<li><strong>{html.escape(item['question'])}</strong><br><span>{html.escape(item['why'])}</span></li>"
        for item in intent.get("questions", [])[:5]
    )
    reference_items = "".join(
        (
            f"<li><strong>{html.escape(item['name'])}</strong> · {html.escape(item['category'])}<br>"
            f"<span>Borrow: {html.escape(item['borrow'])}</span><br>"
            f"<span>Avoid: {html.escape(item['avoid'])}</span></li>"
        )
        for item in reference.get("external_references", [])[:4]
    )
    if not reference_items:
        reference_items = "<li>No external benchmark objects recorded yet. Add 2 to 5 references before deepening the package.</li>"

    output_risk_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item.get('label', item.get('key', 'Risk')))}</strong><br>"
            f"<span>{html.escape('; '.join(item.get('risks', [])[:2]))}</span>"
            "</li>"
        )
        for item in output_risk.get("risk_families", [])[:3]
    )
    if not output_risk_items:
        output_risk_items = "<li>No output risk profile attached yet. Generate one before approving example outputs.</li>"

    artifact_design_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item.get('label', item.get('key', 'Artifact')))}</strong><br>"
            f"<span>{html.escape(item.get('direction', ''))}</span>"
            "</li>"
        )
        for item in artifact_design.get("artifact_families", [])[:3]
    )
    if not artifact_design_items:
        artifact_design_items = "<li>No artifact design profile attached yet. Generate one before approving visual or document outputs.</li>"
    design_gate_items = "".join(
        f"<li>{html.escape(item)}</li>" for item in artifact_design.get("quality_gates", [])[:5]
    ) or "<li>No artifact design quality gates attached yet.</li>"

    prompt_quality_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item.get('label', item.get('key', 'Quality')))}</strong> · "
            f"{html.escape(str(item.get('score', 'n/a')))} / 100<br>"
            f"<span>{html.escape(item.get('repair', ''))}</span>"
            "</li>"
        )
        for item in prompt_quality.get("quality_matrix", [])[:5]
    ) or "<li>No prompt quality profile attached yet.</li>"
    rtf_items = "".join(
        (
            "<li>"
            f"<strong>{html.escape(key.title())}</strong><br>"
            f"<span>{html.escape(str(value))}</span>"
            "</li>"
        )
        for key, value in prompt_quality.get("rtf_to_skill", {}).items()
    ) or "<li>No RTF mapping attached yet.</li>"

    readiness_html = "".join(
        (
            "<li>"
            f"<strong>{html.escape(item['label'])}</strong> · {html.escape(item['status'])}<br>"
            f"<span>{html.escape(item['detail'])}</span>"
            "</li>"
        )
        for item in readiness["checks"]
    )

    direction_cards = "".join(
        (
            "<div class='direction-card'>"
            f"<h3>{html.escape(item['title'])}</h3>"
            f"<p>{html.escape(item['why'])}</p>"
            "<ul>"
            + "".join(f"<li>{html.escape(action)}</li>" for action in item.get("actions", [])[:3])
            + "</ul>"
            f"<div class='minor'>Unlocks: {html.escape(item['unlocks'])}</div>"
            "</div>"
        )
        for item in directions
    )

    architecture_html = "".join(
        (
            "<div class='arch-step'>"
            f"<div class='step-label'>{html.escape(item['label'])}</div>"
            f"<div class='step-detail'>{html.escape(item['detail'])}</div>"
            "</div>"
        )
        for item in architecture
    )

    feedback_entries = feedback.get("entries", [])[-3:]
    feedback_html = ""
    if feedback_entries:
        feedback_html = "".join(
            (
                "<li>"
                f"<strong>{html.escape(entry.get('category', 'general'))}</strong> · "
                f"rating {html.escape(str(entry.get('rating', 'n/a')))}<br>"
                f"<span>{html.escape(entry.get('note', ''))}</span>"
                "</li>"
            )
            for entry in reversed(feedback_entries)
        )
    else:
        feedback_html = "<li>No lightweight feedback captured yet. Use `yao.py feedback` to record quick review notes.</li>"

    baseline_html = ""
    if compare_table_rows:
        compare_rows_html = "".join(
            f"<tr><td>{html.escape(item['label'])}</td><td>{html.escape(str(item['tokens']))}</td><td>{html.escape(str(item['dev_errors']))}</td><td>{html.escape(str(item['holdout_errors']))}</td><td>{html.escape(item['strategy'])}</td></tr>"
            for item in compare_table_rows
        )
        selection_logic = compare.get("selection_logic", "Choose the smallest candidate that improves routing without adding unnecessary weight.")
        winner_label = compare.get("summary", {}).get("winner_label", compare.get("winner", {}).get("label", "Current"))
        baseline_html = (
            "<div class='baseline-box'>"
            f"<p><strong>Winner:</strong> {html.escape(str(winner_label))}</p>"
            f"<p class='minor'>{html.escape(str(selection_logic))}</p>"
            "<table><thead><tr><th>Variant</th><th>Tokens</th><th>Dev Errors</th><th>Holdout Errors</th><th>Strategy</th></tr></thead>"
            f"<tbody>{compare_rows_html}</tbody></table>"
            "</div>"
        )
    elif baseline:
        summary = baseline.get("summary", {})
        baseline_html = (
            "<div class='baseline-box'>"
            f"<p><strong>Targets:</strong> {html.escape(str(summary.get('target_count', 0)))}</p>"
            f"<p><strong>Baseline errors:</strong> {html.escape(str(summary.get('baseline_total_errors', 0)))}</p>"
            f"<p><strong>Current errors:</strong> {html.escape(str(summary.get('current_total_errors', 0)))}</p>"
            f"<p><strong>Winner errors:</strong> {html.escape(str(summary.get('winner_total_errors', 0)))}</p>"
            "</div>"
        )
    else:
        baseline_html = "<p class='minor'>No baseline comparison has been recorded for this package yet.</p>"

    promotion_html = ""
    if promotion:
        summary = promotion.get("summary", {})
        promotion_html = (
            "<div class='baseline-box'>"
            f"<p><strong>Promote:</strong> {html.escape(str(summary.get('promote', 0)))}</p>"
            f"<p><strong>Keep current:</strong> {html.escape(str(summary.get('keep_current', 0)))}</p>"
            f"<p><strong>Blocked:</strong> {html.escape(str(summary.get('blocked', 0)))}</p>"
            "</div>"
        )
    else:
        promotion_html = "<p class='minor'>No promotion summary is attached to this package yet.</p>"

    benchmark_html = ""
    if benchmark_rows:
        benchmark_html = "".join(
            (
                "<div class='direction-card'>"
                f"<h3>{html.escape(item['name'])}</h3>"
                "<p><strong>Borrow now</strong></p>"
                + ("<ul>" + "".join(f"<li>{html.escape(borrow)}</li>" for borrow in item.get('borrow', [])) + "</ul>" if item.get("borrow") else "<p>No borrow cues recorded.</p>")
                + "<p><strong>Avoid</strong></p>"
                + ("<ul>" + "".join(f"<li>{html.escape(avoid)}</li>" for avoid in item.get('avoid', [])) + "</ul>" if item.get("avoid") else "<p>No avoid cues recorded.</p>")
                + "</div>"
            )
            for item in benchmark_rows
        )
    else:
        benchmark_html = "<p class='minor'>No GitHub benchmark scan has been attached to this package yet.</p>"

    synthesis_html = ""
    if synthesis_rows:
        synthesis_html = "".join(
            (
                "<div class='direction-card'>"
                f"<h3>{html.escape(item['name'])}</h3>"
                "<p><strong>Borrow now</strong></p>"
                + ("<ul>" + "".join(f"<li>{html.escape(borrow)}</li>" for borrow in item.get('borrow', [])) + "</ul>" if item.get("borrow") else "<p>No borrow cues recorded.</p>")
                + "<p><strong>Avoid</strong></p>"
                + ("<ul>" + "".join(f"<li>{html.escape(avoid)}</li>" for avoid in item.get('avoid', [])) + "</ul>" if item.get("avoid") else "<p>No avoid cues recorded.</p>")
                + "</div>"
            )
            for item in synthesis_rows
        )
    else:
        synthesis_html = "<p class='minor'>No multi-source synthesis has been generated yet.</p>"

    variant_diff_html = ""
    if variant_cards:
        variant_diff_html = "".join(
            (
                "<div class='variant-card'>"
                f"<div class='variant-head'><h3>{html.escape(item['label'])}</h3><span>{html.escape(item['strategy'])}</span></div>"
                f"<p class='variant-description'>{html.escape(item['description'])}</p>"
                "<div class='variant-metrics'>"
                f"<span>tokens {html.escape(str(item['tokens']))} ({html.escape(item['token_delta'])})</span>"
                f"<span>dev {html.escape(str(item['dev_errors']))} ({html.escape(item['dev_delta'])})</span>"
                f"<span>holdout {html.escape(str(item['holdout_errors']))} ({html.escape(item['holdout_delta'])})</span>"
                "</div>"
                "<div class='variant-cues'>"
                "<p><strong>Adds relative to baseline</strong></p>"
                + (
                    "<ul>" + "".join(f"<li>{html.escape(value)}</li>" for value in item["added"]) + "</ul>"
                    if item["added"]
                    else "<p class='minor'>No added cues.</p>"
                )
                + "<p><strong>Drops from baseline</strong></p>"
                + (
                    "<ul>" + "".join(f"<li>{html.escape(value)}</li>" for value in item["removed"]) + "</ul>"
                    if item["removed"]
                    else "<p class='minor'>No dropped cues.</p>"
                )
                + "</div></div>"
            )
            for item in variant_cards
        )
    else:
        variant_diff_html = "<p class='minor'>No description optimization compare payload is attached yet.</p>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(overview.get('display_name', overview.get('title', 'Skill Review')))} Review Viewer</title>
  <style>
    :root {{
      --text: #111111;
      --muted: #666666;
      --line: #e8e8e8;
      --soft: #f6f6f4;
      --white: #ffffff;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--white);
      color: var(--text);
      font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
      line-height: 1.6;
    }}
    .page {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 48px 32px 72px;
    }}
    .hero {{
      padding-bottom: 28px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 28px;
    }}
    h1, h2, h3 {{
      margin: 0 0 12px;
      letter-spacing: -0.02em;
      font-weight: 600;
    }}
    h1 {{ font-size: 40px; line-height: 1.08; }}
    h2 {{ font-size: 22px; margin-top: 34px; }}
    h3 {{ font-size: 16px; }}
    p, li, span {{ font-size: 15px; }}
    .lede {{
      max-width: 860px;
      font-size: 18px;
      color: var(--muted);
      margin: 0 0 18px;
    }}
    .meta {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 16px;
    }}
    .meta span {{
      border: 1px solid var(--line);
      padding: 6px 10px;
      background: var(--soft);
    }}
    .arch-grid {{
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 12px;
      margin-top: 16px;
    }}
    .arch-step, .panel, .direction-card, .baseline-box {{
      border: 1px solid var(--line);
      background: var(--white);
    }}
    .arch-step {{
      padding: 14px;
      min-height: 132px;
    }}
    .step-label {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      margin-bottom: 10px;
    }}
    .step-detail {{
      font-size: 14px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.1fr 0.9fr;
      gap: 18px;
      margin-top: 16px;
    }}
    .panel {{
      padding: 18px;
    }}
    .panel ul {{
      margin: 0;
      padding-left: 18px;
    }}
    .direction-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
      margin-top: 16px;
    }}
    .variant-grid {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 16px;
      margin-top: 16px;
    }}
    .direction-card {{
      padding: 18px;
    }}
    .direction-card ul {{
      margin: 12px 0;
      padding-left: 18px;
    }}
    .minor {{
      color: var(--muted);
      font-size: 13px;
    }}
    .variant-card {{
      border: 1px solid var(--line);
      background: var(--white);
      padding: 18px;
    }}
    .variant-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
    }}
    .variant-head span {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }}
    .variant-description {{
      margin: 14px 0;
      padding-left: 14px;
      border-left: 2px solid var(--line);
      color: var(--text);
    }}
    .variant-metrics {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 14px;
    }}
    .variant-metrics span {{
      border: 1px solid var(--line);
      background: var(--soft);
      padding: 6px 10px;
      font-size: 12px;
    }}
    .variant-cues p {{
      margin: 8px 0 6px;
    }}
    .variant-cues ul {{
      margin: 0 0 12px;
      padding-left: 18px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 14px;
      font-size: 14px;
    }}
    th, td {{
      border-top: 1px solid var(--line);
      text-align: left;
      padding: 10px 8px;
      vertical-align: top;
    }}
    th {{
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
    }}
    @media (max-width: 1000px) {{
      .arch-grid, .direction-grid, .variant-grid, .grid {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <div class="page">
    <section class="hero">
      <p class="minor">Review Viewer</p>
      <h1>{html.escape(overview.get('display_name', overview.get('title', 'Skill Review')))}</h1>
      <p class="lede">{html.escape(overview.get('description', ''))}</p>
      <div class="meta">
        <span>maturity: {html.escape(str(overview.get('metadata', {}).get('maturity_tier', 'scaffold')))}</span>
        <span>archetype: {html.escape(str(overview.get('metadata', {}).get('skill_archetype', 'scaffold')))}</span>
        <span>format: {html.escape(str(overview.get('metadata', {}).get('canonical_format', 'agent-skills')))}</span>
        <span>updated: {html.escape(str(overview.get('metadata', {}).get('updated_at', 'n/a')))}</span>
        <span>intent confidence: {html.escape(str(intent_confidence.get('score', 'n/a')))} / 100</span>
      </div>
    </section>

    <section>
      <h2>Architecture at a glance</h2>
      <div class="arch-grid">{architecture_html}</div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Core logic</h2>
        <ul>{logic_items}</ul>
      </div>
      <div class="panel">
        <h2>How to use it</h2>
        <ul>{usage_items}</ul>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Intent questions</h2>
        <ul>{question_items}</ul>
      </div>
      <div class="panel">
        <h2>Why this package is strong</h2>
        <ul>{strength_items}</ul>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Borrow plan</h2>
        <ul>{reference_items}</ul>
      </div>
      <div class="panel">
        <h2>Compare view</h2>
        {baseline_html}
      </div>
    </section>

    <section>
      <h2>Variant diff studio</h2>
      <div class="variant-grid">{variant_diff_html}</div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Evidence readiness</h2>
        <p class="minor">Readiness score: {html.escape(str(readiness['score']))}/100</p>
        <ul>{readiness_html}</ul>
      </div>
      <div class="panel">
        <h2>Honest boundary check</h2>
        <ul>
          <li>Are the known limits visible before the package deepens?</li>
          <li>Does the evidence support the borrowed patterns?</li>
          <li>Should uncertainty become a clarification question instead of more structure?</li>
        </ul>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Output risk profile</h2>
        <ul>{output_risk_items}</ul>
      </div>
      <div class="panel">
        <h2>Self-repair checks</h2>
        <ul>{"".join(f"<li>{html.escape(item)}</li>" for item in output_risk.get('self_repair_checks', [])[:5]) or "<li>No self-repair checks attached yet.</li>"}</ul>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Artifact design profile</h2>
        <p class="minor">Design system: {html.escape(str(artifact_design.get('design_system', 'not generated')))}</p>
        <ul>{artifact_design_items}</ul>
      </div>
      <div class="panel">
        <h2>Visual quality gates</h2>
        <ul>{design_gate_items}</ul>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Prompt quality profile</h2>
        <p class="minor">Relevance: {html.escape(str(prompt_quality.get('relevance', 'not generated')))} · score {html.escape(str(prompt_quality.get('overall_quality_score', 'n/a')))} / 100 · complexity {html.escape(str(prompt_quality.get('complexity', {}).get('band', 'n/a')))}</p>
        <ul>{prompt_quality_items}</ul>
      </div>
      <div class="panel">
        <h2>RTF to skill mapping</h2>
        <ul>{rtf_items}</ul>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Reference coach</h2>
        <div class="direction-grid">{benchmark_html}</div>
      </div>
      <div class="panel">
        <h2>Decide before you deepen</h2>
        <ul>
          <li>Choose one pattern to borrow on purpose, not three at once.</li>
          <li>State one thing this skill will not inherit from the benchmark objects.</li>
          <li>Only deepen the package after that choice is visible in the boundary or execution flow.</li>
        </ul>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Reference synthesis</h2>
        <div class="direction-grid">{synthesis_html}</div>
      </div>
      <div class="panel">
        <h2>Borrow now</h2>
        <ul>{"".join(f"<li>{html.escape(item)}</li>" for item in reference_synthesis.get('synthesis', {}).get('borrow_now', [])[:4]) or "<li>No synthesis borrow cues recorded yet.</li>"}</ul>
        <p class="minor">{html.escape(reference_synthesis.get('synthesis', {}).get('decision_prompt', 'Run the reference synthesis after the benchmark scan to decide what to borrow next.'))}</p>
      </div>
    </section>

    <section>
      <h2>Top three next moves</h2>
      <div class="direction-grid">{direction_cards}</div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Recent feedback</h2>
        <ul>{feedback_html}</ul>
      </div>
      <div class="panel">
        <h2>Promotion status</h2>
        {promotion_html}
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Package map</h2>
        <ul>{"".join(f"<li><strong>{html.escape(item['path'])}</strong> — {html.escape(item['label'])}</li>" for item in overview.get('package_map', [])[:8])}</ul>
      </div>
      <div class="panel">
        <h2>First-pass review frame</h2>
        <ul>
          <li>Does the trigger stay narrow enough for the intended job?</li>
          <li>Does the archetype match the real reuse level?</li>
          <li>Are we adding structure faster than we are adding reliability?</li>
          <li>Should the next step be trigger tightening, execution assets, or portability hardening?</li>
        </ul>
      </div>
    </section>

    <section class="grid">
      <div class="panel">
        <h2>Authoring discipline</h2>
        <ul>
          <li>Name unresolved assumptions before deepening the package.</li>
          <li>Keep the package no larger than the recurring job requires.</li>
          <li>Touch only files that directly support the requested change.</li>
          <li>Tie every meaningful new artifact to a check or reviewer note.</li>
        </ul>
      </div>
      <div class="panel">
        <h2>Reviewer guardrails</h2>
        <ul>
          <li>Block speculative features that are not backed by real workflow variation.</li>
          <li>Move unverifiable ideas into next-step candidates instead of baseline structure.</li>
          <li>Reject decorative folders, reports, or governance that do not reduce risk.</li>
          <li>Ask for one high-leverage clarification when job, output, or exclusion is still fuzzy.</li>
        </ul>
      </div>
    </section>
  </div>
</body>
</html>
"""


def render_review_viewer(skill_dir: Path, output_html: Path | None = None, output_json: Path | None = None) -> dict:
    skill_dir = skill_dir.resolve()
    reports_dir = skill_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_html = output_html or reports_dir / "review-viewer.html"
    output_json = output_json or reports_dir / "review-viewer.json"

    report = ensure_report_inputs(skill_dir)
    report["evidence_readiness"] = evidence_readiness(report)
    output_html.write_text(render_html(report), encoding="utf-8")
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "ok": True,
        "skill_dir": str(skill_dir),
        "artifacts": {
            "html": str(output_html),
            "json": str(output_json),
        },
        "summary": {
            "title": report["overview"].get("title", skill_dir.name),
            "maturity_tier": report["overview"].get("metadata", {}).get("maturity_tier", "scaffold"),
            "directions": len(report["iteration"].get("directions", [])),
            "feedback_entries": len(report.get("feedback", {}).get("entries", [])),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a compact HTML review viewer for a skill package.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-html")
    parser.add_argument("--output-json")
    args = parser.parse_args()
    result = render_review_viewer(
        Path(args.skill_dir),
        output_html=Path(args.output_html).resolve() if args.output_html else None,
        output_json=Path(args.output_json).resolve() if args.output_json else None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
