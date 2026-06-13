#!/usr/bin/env python3
"""Prepare a reviewer-facing blind A/B output review kit."""

import argparse
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


def prepare_output_review_kit(
    blind_pack_json: Path,
    blind_pack_md: Path,
    decisions_path: Path,
    output_json: Path,
    output_md: Path,
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
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a reviewer-facing blind A/B output review kit.")
    parser.add_argument("--blind-pack-json", default=str(DEFAULT_BLIND_PACK_JSON))
    parser.add_argument("--blind-pack-md", default=str(DEFAULT_BLIND_PACK_MD))
    parser.add_argument("--decisions", default=str(DEFAULT_DECISIONS))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--write-template", action="store_true")
    args = parser.parse_args()

    payload = prepare_output_review_kit(
        Path(args.blind_pack_json).resolve(),
        Path(args.blind_pack_md).resolve(),
        Path(args.decisions).resolve(),
        Path(args.output_json).resolve(),
        Path(args.output_md).resolve(),
        write_template=args.write_template,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["ok"] else 2)


if __name__ == "__main__":
    main()
