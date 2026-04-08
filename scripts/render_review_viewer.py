#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path

from render_intent_dialogue import render_intent_dialogue
from render_iteration_directions import render_iteration_directions
from render_reference_scan import render_reference_scan
from render_skill_overview import render_skill_overview


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_feedback_summary(skill_dir: Path) -> dict:
    payload = load_json(skill_dir / "reports" / "feedback-log.json")
    return payload if isinstance(payload, dict) else {}


def load_baseline_summary(skill_dir: Path) -> dict:
    payload = load_json(skill_dir / "reports" / "baseline-compare.json")
    return payload if isinstance(payload, dict) else {}


def load_specific_compare(skill_dir: Path) -> dict:
    candidates = [
        skill_dir / "reports" / "description_optimization.json",
        skill_dir.parent / "optimization" / "reports" / "description_optimization.json",
    ]
    for path in candidates:
        payload = load_json(path)
        if isinstance(payload, dict) and payload:
            return payload
    return {}


def load_specific_promotion(skill_dir: Path) -> dict:
    payload = load_json(skill_dir / "reports" / "promotion_decisions.json")
    return payload if isinstance(payload, dict) else {}


def ensure_report_inputs(skill_dir: Path) -> dict:
    overview_json = skill_dir / "reports" / "skill-overview.json"
    intent_json = skill_dir / "reports" / "intent-dialogue.json"
    reference_json = skill_dir / "reports" / "reference-scan.json"
    directions_json = skill_dir / "reports" / "iteration-directions.json"

    overview_payload = load_json(overview_json) if overview_json.exists() else {}
    intent_payload = load_json(intent_json) if intent_json.exists() else {}
    reference_payload = load_json(reference_json) if reference_json.exists() else {}
    directions_payload = load_json(directions_json) if directions_json.exists() else {}

    overview = overview_payload or render_skill_overview(skill_dir)["summary"]
    intent = intent_payload or render_intent_dialogue(skill_dir)["summary"]
    reference = reference_payload or render_reference_scan(skill_dir, [])["summary"]
    iteration = directions_payload.get("summary", {}) or render_iteration_directions(skill_dir)["summary"]
    feedback = load_feedback_summary(skill_dir)
    baseline = load_baseline_summary(skill_dir)
    compare = load_specific_compare(skill_dir)
    promotion = load_specific_promotion(skill_dir)
    return {
        "overview": overview,
        "intent": intent,
        "reference": reference,
        "iteration": directions_payload if directions_payload else {"summary": iteration, "directions": []},
        "feedback": feedback,
        "baseline": baseline,
        "compare": compare,
        "promotion": promotion,
    }


def architecture_steps(overview: dict) -> list[dict]:
    logic = overview.get("logic_steps", [])[:3]
    usage = overview.get("usage_steps", [])[:2]
    return [
        {"label": "Inputs", "detail": "workflow, prompt, transcript, docs, or notes"},
        {"label": "Boundary", "detail": overview.get("description", "Define the recurring job and exclusions.")},
        {"label": "Logic", "detail": "; ".join(logic) if logic else "Understand, execute, and validate."},
        {"label": "Usage", "detail": "; ".join(usage) if usage else "Load the skill and follow the workflow."},
        {"label": "Next", "detail": "Review the top iteration directions before growing the package."},
    ]


def compare_rows(compare: dict) -> list[dict]:
    if not compare:
        return []
    rows = []
    items = [
        ("Baseline", compare.get("baseline", {})),
        ("Current", compare.get("current_candidate", {})),
        (compare.get("winner", {}).get("label", "Winner"), compare.get("winner", {})),
    ]
    for label, payload in items:
        if not payload:
            continue
        dev = payload.get("dev", {})
        holdout = payload.get("holdout", {})
        rows.append(
            {
                "label": label,
                "tokens": payload.get("estimated_tokens", 0),
                "dev_errors": dev.get("total_errors", 0),
                "holdout_errors": holdout.get("total_errors", 0),
                "strategy": payload.get("strategy", "existing"),
            }
        )
    return rows


def render_html(report: dict) -> str:
    overview = report["overview"]
    intent = report["intent"]
    reference = report["reference"]
    iteration = report["iteration"]
    directions = iteration.get("directions", [])[:3]
    feedback = report.get("feedback", {})
    baseline = report.get("baseline", {})
    compare = report.get("compare", {})
    promotion = report.get("promotion", {})
    architecture = architecture_steps(overview)
    compare_table_rows = compare_rows(compare)

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
      .arch-grid, .direction-grid, .grid {{
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
