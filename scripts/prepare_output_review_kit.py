#!/usr/bin/env python3
"""Prepare a reviewer-facing blind A/B output review kit."""

import argparse
import html
import json
from pathlib import Path
from typing import Any

from adjudicate_output_review import (
    build_decision_template,
    confidence_value,
    decision_index,
    display_path,
    load_json,
    normalize_variant,
)


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BLIND_PACK_JSON = ROOT / "reports" / "output_blind_review_pack.json"
DEFAULT_BLIND_PACK_MD = ROOT / "reports" / "output_blind_review_pack.md"
DEFAULT_DECISIONS = ROOT / "reports" / "output_review_decisions.json"
DEFAULT_OUTPUT_JSON = ROOT / "reports" / "output_review_kit.json"
DEFAULT_OUTPUT_MD = ROOT / "reports" / "output_review_kit.md"
DEFAULT_OUTPUT_HTML = ROOT / "reports" / "output_review_kit.html"


def load_optional_decisions(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {"schema_version": "1.0", "decisions": []}, []
    return load_json(path)


def pairs_from_pack(blind_pack: dict[str, Any]) -> list[dict[str, Any]]:
    pairs = blind_pack.get("pairs", [])
    if not isinstance(pairs, list):
        return []
    return [item for item in pairs if isinstance(item, dict) and item.get("case_id")]


def decision_state(decision: dict[str, Any] | None) -> dict[str, Any]:
    if not decision:
        return {
            "status": "awaiting-decision",
            "winner_variant_recorded": False,
            "confidence_recorded": False,
            "reason_recorded": False,
            "blocking_reason": "No reviewer choice has been recorded yet.",
        }
    winner = normalize_variant(decision.get("winner_variant", decision.get("reviewer_winner_variant", decision.get("winner", ""))))
    confidence, confidence_failure = confidence_value(decision.get("confidence"))
    reason = str(decision.get("reason", "")).strip()
    if not winner and confidence is None and not reason:
        return {
            "status": "awaiting-decision",
            "winner_variant_recorded": False,
            "confidence_recorded": False,
            "reason_recorded": False,
            "blocking_reason": "Decision template exists but this row is still blank.",
        }
    failures = []
    if winner not in {"A", "B"}:
        failures.append("winner_variant must be A or B")
    if confidence_failure:
        failures.append(confidence_failure)
    if not reason:
        failures.append("reason should explain the reviewer rationale")
    if failures:
        return {
            "status": "needs-fix",
            "winner_variant_recorded": winner in {"A", "B"},
            "confidence_recorded": confidence is not None,
            "reason_recorded": bool(reason),
            "blocking_reason": "; ".join(failures),
        }
    return {
        "status": "ready-for-adjudication",
        "winner_variant_recorded": True,
        "confidence_recorded": confidence is not None,
        "reason_recorded": True,
        "blocking_reason": "Reviewer choice is complete enough for adjudication.",
    }


def build_cases(blind_pack: dict[str, Any], decisions: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    cases = []
    for pair in pairs_from_pack(blind_pack):
        case_id = str(pair.get("case_id", ""))
        rubric = []
        for item in pair.get("rubric", []) if isinstance(pair.get("rubric", []), list) else []:
            if isinstance(item, dict):
                rubric.append(
                    {
                        "id": str(item.get("id", "")),
                        "description": str(item.get("description", "")),
                        "weight": float(item.get("weight", 1) or 0),
                    }
                )
        cases.append(
            {
                "case_id": case_id,
                "prompt": str(pair.get("prompt", "")),
                "input_files": pair.get("input_files", []) if isinstance(pair.get("input_files", []), list) else [],
                "review_instruction": str(pair.get("review_instruction", "")),
                "rubric": rubric,
                "variant_a": {
                    "blind_id": str(pair.get("variant_a", {}).get("blind_id", "")) if isinstance(pair.get("variant_a"), dict) else "",
                    "output": str(pair.get("variant_a", {}).get("output", "")) if isinstance(pair.get("variant_a"), dict) else "",
                },
                "variant_b": {
                    "blind_id": str(pair.get("variant_b", {}).get("blind_id", "")) if isinstance(pair.get("variant_b"), dict) else "",
                    "output": str(pair.get("variant_b", {}).get("output", "")) if isinstance(pair.get("variant_b"), dict) else "",
                },
                "decision_state": decision_state(decisions.get(case_id)),
            }
        )
    return cases


def build_summary(cases: list[dict[str, Any]], failures: list[str], reviewer: str, reviewed_at: str) -> dict[str, Any]:
    status_counts: dict[str, int] = {}
    for case in cases:
        status = str(case.get("decision_state", {}).get("status", "awaiting-decision"))
        status_counts[status] = status_counts.get(status, 0) + 1
    ready_count = status_counts.get("ready-for-adjudication", 0)
    pending_count = status_counts.get("awaiting-decision", 0)
    invalid_count = status_counts.get("needs-fix", 0)
    return {
        "case_count": len(cases),
        "ready_for_adjudication_count": ready_count,
        "pending_decision_count": pending_count,
        "invalid_decision_count": invalid_count,
        "reviewer_metadata_present": bool(str(reviewer).strip() and str(reviewed_at).strip()),
        "answer_key_hidden": True,
        "answer_key_path_exposed": False,
        "ready_to_run_adjudication": bool(cases) and ready_count == len(cases) and invalid_count == 0,
        "failure_count": len(failures),
    }


def build_contract(blind_pack_md: Path, decisions_path: Path) -> dict[str, Any]:
    return {
        "reviewer_steps": [
            f"Open {display_path(blind_pack_md)} or this kit and compare Variant A vs Variant B for each case.",
            f"Record choices in {display_path(decisions_path)} without opening the answer key.",
            "Use winner_variant A or B, confidence from 0 to 1, and a short reason for every case.",
            "Run python3 scripts/yao.py output-review after choices are recorded.",
            "Refresh python3 scripts/yao.py review-studio . before asking for release approval.",
        ],
        "required_fields": {
            "reviewer": "Human reviewer name or review group.",
            "reviewed_at": "Review date or timestamp.",
            "winner_variant": "A or B for every case.",
            "confidence": "Optional numeric confidence from 0 to 1.",
            "reason": "Short rationale based on the rubric, not on hidden labels.",
        },
        "privacy_contract": [
            "The answer key is intentionally withheld from this kit.",
            "Do not inspect hidden labels or expected winners before decisions are recorded.",
            "Do not paste private user data into decision reasons.",
            "Pending decisions must stay pending instead of being counted as human agreement.",
        ],
    }


def render_rubric(rubric: list[dict[str, Any]]) -> list[str]:
    if not rubric:
        return ["- No rubric items found."]
    return [f"- `{item['id']}` ({item['weight']}): {item['description']}" for item in rubric]


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    contract = payload["review_contract"]
    lines = [
        "# Output Review Kit",
        "",
        "This reviewer-facing packet contains the blind A/B cases, decision fields, and command flow. It intentionally does not expose the answer key.",
        "",
        "## Summary",
        "",
        f"- cases: `{summary['case_count']}`",
        f"- ready for adjudication: `{summary['ready_for_adjudication_count']}`",
        f"- pending decisions: `{summary['pending_decision_count']}`",
        f"- invalid decisions: `{summary['invalid_decision_count']}`",
        f"- reviewer metadata present: `{str(summary['reviewer_metadata_present']).lower()}`",
        f"- answer key hidden: `{str(summary['answer_key_hidden']).lower()}`",
        f"- answer key path exposed: `{str(summary['answer_key_path_exposed']).lower()}`",
        "",
        "## Review Flow",
        "",
    ]
    lines.extend(f"{index}. {step}" for index, step in enumerate(contract["reviewer_steps"], start=1))
    lines.extend(["", "## Required Fields", ""])
    lines.extend(f"- `{key}`: {value}" for key, value in contract["required_fields"].items())
    lines.extend(["", "## Privacy Contract", ""])
    lines.extend(f"- {item}" for item in contract["privacy_contract"])
    lines.extend(
        [
            "",
            "## Decision States",
            "",
            "| Case | State | Winner | Confidence | Reason | Blocking Reason |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for case in payload["cases"]:
        state = case["decision_state"]
        lines.append(
            f"| `{case['case_id']}` | `{state['status']}` | `{str(state['winner_variant_recorded']).lower()}` | "
            f"`{str(state['confidence_recorded']).lower()}` | `{str(state['reason_recorded']).lower()}` | {state['blocking_reason']} |"
        )
    lines.extend(["", "## Blind Cases", ""])
    for case in payload["cases"]:
        lines.extend(
            [
                f"### {case['case_id']}",
                "",
                f"Prompt: {case['prompt']}",
                "",
                "Rubric:",
                *render_rubric(case["rubric"]),
                "",
                "#### Variant A",
                "",
                case["variant_a"]["output"] or "_No output found._",
                "",
                "#### Variant B",
                "",
                case["variant_b"]["output"] or "_No output found._",
                "",
            ]
        )
    if payload.get("failures"):
        lines.extend(["## Failures", ""])
        lines.extend(f"- {failure}" for failure in payload["failures"])
    return "\n".join(lines).strip() + "\n"


def html_text(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def status_label(status: str) -> str:
    return {
        "awaiting-decision": "Awaiting",
        "needs-fix": "Needs fix",
        "ready-for-adjudication": "Ready",
    }.get(status, status)


def render_html_rubric(rubric: list[dict[str, Any]]) -> str:
    if not rubric:
        return "<li>No rubric items found.</li>"
    return "".join(
        "<li><span>{id}</span><p>{description}</p><small>{weight}</small></li>".format(
            id=html_text(item.get("id", "")),
            description=html_text(item.get("description", "")),
            weight=html_text(item.get("weight", "")),
        )
        for item in rubric
    )


def render_html_cases(cases: list[dict[str, Any]]) -> str:
    cards = []
    for index, case in enumerate(cases, start=1):
        state = case.get("decision_state", {})
        status = str(state.get("status", "awaiting-decision"))
        cards.append(
            f"""
      <article class="case-card" id="case-{html_text(case.get('case_id', ''))}">
        <header class="case-head">
          <div>
            <span class="case-index">Case {index:02d}</span>
            <h3>{html_text(case.get('case_id', ''))}</h3>
          </div>
          <span class="status-pill {html_text(status)}">{html_text(status_label(status))}</span>
        </header>
        <p class="prompt">{html_text(case.get('prompt', ''))}</p>
        <section class="rubric"><h4>Rubric</h4><ul>{render_html_rubric(case.get('rubric', []))}</ul></section>
        <section class="variants" aria-label="Blind output variants">
          <div class="variant"><h4>Variant A</h4><pre>{html_text(case.get('variant_a', {}).get('output', ''))}</pre></div>
          <div class="variant"><h4>Variant B</h4><pre>{html_text(case.get('variant_b', {}).get('output', ''))}</pre></div>
        </section>
        <footer class="case-foot">
          <span>Winner recorded: {html_text(str(state.get('winner_variant_recorded', False)).lower())}</span>
          <span>Confidence: {html_text(str(state.get('confidence_recorded', False)).lower())}</span>
          <span>Reason: {html_text(str(state.get('reason_recorded', False)).lower())}</span>
          <strong>{html_text(state.get('blocking_reason', ''))}</strong>
        </footer>
      </article>"""
        )
    return "\n".join(cards)


def decision_template_json(cases: list[dict[str, Any]]) -> str:
    template = {
        "schema_version": "1.0",
        "reviewer": "",
        "reviewed_at": "",
        "decisions": [
            {"case_id": case.get("case_id", ""), "winner_variant": "", "confidence": None, "reason": ""}
            for case in cases
        ],
    }
    return json.dumps(template, ensure_ascii=False, indent=2)


def render_html(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    contract = payload["review_contract"]
    stats = [
        ("Cases", summary["case_count"]),
        ("Ready", summary["ready_for_adjudication_count"]),
        ("Pending", summary["pending_decision_count"]),
        ("Invalid", summary["invalid_decision_count"]),
    ]
    stat_html = "".join(f"<div><span>{html_text(label)}</span><strong>{html_text(value)}</strong></div>" for label, value in stats)
    flow_html = "".join(f"<li>{html_text(step)}</li>" for step in contract["reviewer_steps"])
    privacy_html = "".join(f"<li>{html_text(item)}</li>" for item in contract["privacy_contract"])
    decision_json = html_text(decision_template_json(payload["cases"]))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Output Review Kit</title>
  <style>
    :root {{ --ink:#1B365D; --text:#202124; --muted:#6f6a63; --line:#e8e1d8; --soft:#f8f6f2; --warn:#9b4d0f; --ok:#1f6f43; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#fff; color:var(--text); font:16px/1.55 Georgia, "Times New Roman", serif; }}
    .shell {{ max-width:1180px; margin:0 auto; padding:36px 24px 72px; }}
    .topbar {{ position:sticky; top:0; z-index:10; background:rgba(255,255,255,.96); border-bottom:1px solid var(--line); backdrop-filter:blur(8px); }}
    .topbar-inner {{ max-width:1180px; margin:0 auto; padding:12px 24px; display:flex; justify-content:space-between; gap:18px; align-items:center; }}
    .brand {{ color:var(--ink); font-weight:700; letter-spacing:0; }}
    .links {{ display:flex; gap:12px; flex-wrap:wrap; }}
    .links a {{ color:var(--ink); text-decoration:none; border-bottom:1px solid transparent; }}
    .links a:hover {{ border-color:var(--ink); }}
    .hero {{ border-bottom:1px solid var(--line); padding:34px 0 28px; }}
    .eyebrow {{ color:var(--ink); text-transform:uppercase; font-size:12px; letter-spacing:0; font-weight:700; }}
    h1 {{ margin:8px 0 12px; color:var(--ink); font-size:58px; line-height:1.02; letter-spacing:0; }}
    .lede {{ max-width:760px; color:var(--muted); font-size:20px; }}
    .stats {{ display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:12px; margin:28px 0; }}
    .stats div, .panel, .case-card {{ border:1px solid var(--line); border-radius:8px; background:#fff; }}
    .stats div {{ padding:16px; }}
    .stats span {{ display:block; color:var(--muted); font-size:13px; }}
    .stats strong {{ color:var(--ink); font-size:34px; line-height:1; }}
    .grid {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(280px,.42fr); gap:18px; align-items:start; }}
    .panel {{ padding:20px; }}
    h2, h3, h4 {{ color:var(--ink); letter-spacing:0; }}
    h2 {{ margin:0 0 14px; font-size:28px; }}
    h3 {{ margin:0; font-size:24px; }}
    h4 {{ margin:0 0 10px; font-size:16px; }}
    ol, ul {{ padding-left:22px; }}
    code, pre {{ font-family:ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    pre {{ white-space:pre-wrap; overflow-wrap:anywhere; margin:0; color:#2b2b2b; font-size:13px; line-height:1.5; }}
    .case-card {{ margin:22px 0; padding:22px; scroll-margin-top:72px; }}
    .case-head, .case-foot {{ display:flex; gap:14px; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; }}
    .case-index {{ color:var(--muted); font-size:12px; text-transform:uppercase; letter-spacing:0; }}
    .status-pill {{ border:1px solid var(--line); border-radius:999px; padding:4px 10px; color:var(--ink); background:var(--soft); font-size:13px; }}
    .status-pill.ready-for-adjudication {{ color:var(--ok); }}
    .status-pill.needs-fix {{ color:var(--warn); }}
    .prompt {{ color:var(--muted); font-size:18px; }}
    .rubric {{ margin:18px 0; padding:16px; background:var(--soft); border-radius:8px; }}
    .rubric ul {{ list-style:none; padding:0; margin:0; display:grid; gap:8px; }}
    .rubric li {{ display:grid; grid-template-columns:160px 1fr 44px; gap:12px; align-items:start; border-top:1px solid var(--line); padding-top:8px; }}
    .rubric li:first-child {{ border-top:0; padding-top:0; }}
    .rubric span {{ color:var(--ink); font-weight:700; overflow-wrap:anywhere; }}
    .rubric p {{ margin:0; }}
    .rubric small {{ text-align:right; color:var(--muted); }}
    .variants {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
    .variant {{ border:1px solid var(--line); border-radius:8px; padding:16px; min-width:0; }}
    .case-foot {{ margin-top:16px; padding-top:14px; border-top:1px solid var(--line); color:var(--muted); font-size:13px; }}
    .case-foot strong {{ flex-basis:100%; color:var(--text); font-weight:400; }}
    .template {{ background:#101820; color:#f7f2e8; border-radius:8px; padding:16px; }}
    @media (max-width:820px) {{ .stats, .grid, .variants {{ grid-template-columns:1fr; }} .rubric li {{ grid-template-columns:1fr; }} .rubric small {{ text-align:left; }} h1 {{ font-size:38px; }} }}
  </style>
</head>
<body>
  <nav class="topbar"><div class="topbar-inner"><span class="brand">Output Review Kit</span><div class="links"><a href="#flow">Flow</a><a href="#cases">Cases</a><a href="#template">Template</a></div></div></nav>
  <main class="shell">
    <section class="hero">
      <span class="eyebrow">Blind A/B Human Review</span>
      <h1>Reviewer cockpit for output quality decisions</h1>
      <p class="lede">Compare visible Variant A and Variant B outputs, fill the decision file, then run adjudication. The answer key is intentionally hidden from this page.</p>
      <div class="stats">{stat_html}</div>
    </section>
    <section class="grid" id="flow">
      <article class="panel"><h2>Review Flow</h2><ol>{flow_html}</ol></article>
      <aside class="panel"><h2>Privacy</h2><ul>{privacy_html}</ul></aside>
    </section>
    <section id="cases">{render_html_cases(payload["cases"])}</section>
    <section class="panel" id="template"><h2>Decision Template</h2><p>Use this shape in {html_text(payload['artifacts']['decisions'])}; leave a case blank when the reviewer is not ready.</p><pre class="template">{decision_json}</pre></section>
  </main>
</body>
</html>
"""


def prepare_output_review_kit(
    blind_pack_json: Path,
    blind_pack_md: Path,
    decisions_path: Path,
    output_json: Path,
    output_md: Path,
    output_html: Path | None = None,
    write_template: bool = False,
) -> dict[str, Any]:
    blind_pack, failures = load_json(blind_pack_json)
    decisions_payload, decision_failures = load_optional_decisions(decisions_path)
    failures.extend(decision_failures)
    template_written = False
    if write_template and blind_pack and not decisions_path.exists():
        decisions_path.parent.mkdir(parents=True, exist_ok=True)
        decisions_path.write_text(
            json.dumps(build_decision_template(blind_pack), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        template_written = True
        decisions_payload, decision_failures = load_optional_decisions(decisions_path)
        failures.extend(decision_failures)
    decisions, index_failures = decision_index(decisions_payload)
    failures.extend(index_failures)
    case_ids = {str(pair.get("case_id", "")) for pair in pairs_from_pack(blind_pack)}
    for case_id in decisions:
        if case_id not in case_ids:
            failures.append(f"decision references unknown case_id: {case_id}")
    cases = build_cases(blind_pack, decisions)
    summary = build_summary(cases, failures, str(decisions_payload.get("reviewer", "")), str(decisions_payload.get("reviewed_at", "")))
    payload = {
        "schema_version": "1.0",
        "ok": not failures,
        "summary": summary,
        "artifacts": {
            "reviewer_kit_json": display_path(output_json),
            "reviewer_kit_markdown": display_path(output_md),
            "reviewer_kit_html": display_path(output_html) if output_html else "",
            "blind_pack_json": display_path(blind_pack_json),
            "blind_pack_markdown": display_path(blind_pack_md),
            "decisions": display_path(decisions_path),
            "adjudication_json": "reports/output_review_adjudication.json",
            "adjudication_markdown": "reports/output_review_adjudication.md",
        },
        "template_written": template_written,
        "review_contract": build_contract(blind_pack_md, decisions_path),
        "cases": cases,
        "failures": failures,
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    if output_html:
        output_html.parent.mkdir(parents=True, exist_ok=True)
        output_html.write_text(render_html(payload), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a reviewer-facing blind A/B output review kit.")
    parser.add_argument("--blind-pack-json", default=str(DEFAULT_BLIND_PACK_JSON))
    parser.add_argument("--blind-pack-md", default=str(DEFAULT_BLIND_PACK_MD))
    parser.add_argument("--decisions", default=str(DEFAULT_DECISIONS))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--output-html", default=str(DEFAULT_OUTPUT_HTML))
    parser.add_argument("--write-template", action="store_true")
    args = parser.parse_args()

    payload = prepare_output_review_kit(
        Path(args.blind_pack_json).resolve(),
        Path(args.blind_pack_md).resolve(),
        Path(args.decisions).resolve(),
        Path(args.output_json).resolve(),
        Path(args.output_md).resolve(),
        Path(args.output_html).resolve() if args.output_html else None,
        write_template=args.write_template,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["ok"] else 2)


if __name__ == "__main__":
    main()
