#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BLIND_PACK = ROOT / "reports" / "output_blind_review_pack.json"
DEFAULT_ANSWER_KEY = ROOT / "reports" / "output_blind_answer_key.json"
DEFAULT_DECISIONS = ROOT / "reports" / "output_review_decisions.json"
DEFAULT_OUTPUT_JSON = ROOT / "reports" / "output_review_adjudication.json"
DEFAULT_OUTPUT_MD = ROOT / "reports" / "output_review_adjudication.md"


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"Missing JSON file: {display_path(path)}"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"Invalid JSON file {display_path(path)}: {exc}"]
    if not isinstance(payload, dict):
        return {}, [f"JSON root must be an object: {display_path(path)}"]
    return payload, []


def load_optional_decisions(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {"schema_version": "1.0", "decisions": []}, []
    return load_json(path)


def normalize_variant(value: Any) -> str:
    normalized = str(value or "").strip().upper()
    if normalized in {"VARIANT A", "A"}:
        return "A"
    if normalized in {"VARIANT B", "B"}:
        return "B"
    return normalized


def confidence_value(value: Any) -> tuple[float | None, str | None]:
    if value is None or value == "":
        return None, None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, f"confidence must be numeric, got {value!r}"
    if parsed < 0 or parsed > 1:
        return None, f"confidence must be between 0 and 1, got {parsed}"
    return round(parsed, 3), None


def answer_index(answer_key: dict[str, Any]) -> dict[str, dict[str, Any]]:
    answers = answer_key.get("answers", [])
    if not isinstance(answers, list):
        return {}
    return {str(item.get("case_id", "")): item for item in answers if isinstance(item, dict) and item.get("case_id")}


def pair_index(blind_pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pairs = blind_pack.get("pairs", [])
    if not isinstance(pairs, list):
        return {}
    return {str(item.get("case_id", "")): item for item in pairs if isinstance(item, dict) and item.get("case_id")}


def decision_index(decisions_payload: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    decisions = decisions_payload.get("decisions", [])
    failures: list[str] = []
    indexed: dict[str, dict[str, Any]] = {}
    if not isinstance(decisions, list):
        return {}, ["decisions must be a list"]
    for index, item in enumerate(decisions, start=1):
        if not isinstance(item, dict):
            failures.append(f"decision #{index} must be an object")
            continue
        case_id = str(item.get("case_id", "")).strip()
        if not case_id:
            failures.append(f"decision #{index} is missing case_id")
            continue
        if case_id in indexed:
            failures.append(f"duplicate decision for case_id: {case_id}")
            continue
        indexed[case_id] = item
    return indexed, failures


def build_decision_template(blind_pack: dict[str, Any]) -> dict[str, Any]:
    pairs = blind_pack.get("pairs", [])
    template_decisions = []
    if isinstance(pairs, list):
        for pair in pairs:
            if not isinstance(pair, dict):
                continue
            template_decisions.append(
                {
                    "case_id": str(pair.get("case_id", "")),
                    "winner_variant": "",
                    "confidence": None,
                    "reason": "",
                }
            )
    return {
        "schema_version": "1.0",
        "reviewer": "",
        "reviewed_at": "",
        "decision_contract": {
            "winner_variant": "Use A or B after reading the blind review pack. Leave blank when pending.",
            "confidence": "Optional number from 0 to 1.",
            "reason": "Short reviewer rationale. Do not reveal baseline or with-skill labels before adjudication.",
        },
        "decisions": template_decisions,
    }


def adjudicate_pair(
    case_id: str,
    pair: dict[str, Any],
    answer: dict[str, Any] | None,
    decision: dict[str, Any] | None,
) -> tuple[dict[str, Any], list[str]]:
    failures: list[str] = []
    expected = normalize_variant(answer.get("expected_winner_variant", "") if answer else "")
    if expected not in {"A", "B"}:
        failures.append(f"{case_id}: answer key is missing expected_winner_variant")
    if decision is None:
        return (
            {
                "case_id": case_id,
                "status": "pending",
                "expected_winner_variant": "",
                "expected_revealed": False,
                "reviewer_winner_variant": "",
                "confidence": None,
                "reason": "",
                "prompt": str(pair.get("prompt", "")),
            },
            failures,
        )

    reviewer = normalize_variant(
        decision.get("winner_variant", decision.get("reviewer_winner_variant", decision.get("winner", "")))
    )
    confidence, confidence_failure = confidence_value(decision.get("confidence"))
    reason = str(decision.get("reason", "")).strip()
    if not reviewer:
        return (
            {
                "case_id": case_id,
                "status": "pending",
                "expected_winner_variant": "",
                "expected_revealed": False,
                "reviewer_winner_variant": "",
                "confidence": confidence,
                "reason": reason,
                "prompt": str(pair.get("prompt", "")),
            },
            failures,
        )
    if expected not in {"A", "B"}:
        status = "invalid"
    elif reviewer not in {"A", "B"}:
        failures.append(f"{case_id}: winner_variant must be A or B")
        status = "invalid"
    elif confidence_failure:
        failures.append(f"{case_id}: {confidence_failure}")
        status = "invalid"
    else:
        status = "match" if reviewer == expected else "disagree"
    expected_revealed = status in {"match", "disagree"}
    return (
        {
            "case_id": case_id,
            "status": status,
            "expected_winner_variant": expected if expected_revealed else "",
            "expected_revealed": expected_revealed,
            "reviewer_winner_variant": reviewer,
            "confidence": confidence,
            "reason": reason,
            "prompt": str(pair.get("prompt", "")),
        },
        failures,
    )


def build_summary(pairs: list[dict[str, Any]], failures: list[str]) -> dict[str, Any]:
    pair_count = len(pairs)
    judgment_count = sum(1 for item in pairs if item["status"] in {"match", "disagree"})
    pending_count = sum(1 for item in pairs if item["status"] == "pending")
    agreement_count = sum(1 for item in pairs if item["status"] == "match")
    disagreement_count = sum(1 for item in pairs if item["status"] == "disagree")
    invalid_decision_count = sum(1 for item in pairs if item["status"] == "invalid")
    answer_revealed_count = sum(1 for item in pairs if item.get("expected_revealed"))
    agreement_rate = round(agreement_count / judgment_count * 100, 2) if judgment_count else None
    return {
        "pair_count": pair_count,
        "judgment_count": judgment_count,
        "pending_count": pending_count,
        "agreement_count": agreement_count,
        "disagreement_count": disagreement_count,
        "invalid_decision_count": invalid_decision_count,
        "answer_revealed_count": answer_revealed_count,
        "pending_answer_hidden_count": sum(1 for item in pairs if item["status"] in {"pending", "invalid"} and not item.get("expected_revealed")),
        "agreement_rate": agreement_rate,
        "needs_review": pending_count > 0,
        "failure_count": len(failures),
    }


def checklist_readiness(pair: dict[str, Any]) -> tuple[str, str]:
    status = pair.get("status")
    if status in {"match", "disagree"}:
        return "adjudicated", "Reviewer decision is valid; answer key is revealed for this case."
    if status == "invalid":
        return "fix-decision", "Reviewer decision exists but failed validation; answer key remains hidden."
    return "awaiting-decision", "Reviewer has not selected A or B yet; answer key remains hidden."


def build_reviewer_checklist(
    pairs: list[dict[str, Any]],
    blind_pack_path: Path,
    decisions_path: Path,
) -> list[dict[str, Any]]:
    checklist = []
    for pair in pairs:
        readiness, blocking_reason = checklist_readiness(pair)
        checklist.append(
            {
                "case_id": pair.get("case_id", ""),
                "readiness": readiness,
                "blocking_reason": blocking_reason,
                "status": pair.get("status", "pending"),
                "reviewer_winner_variant": pair.get("reviewer_winner_variant", ""),
                "answer_key_visible": bool(pair.get("expected_revealed")),
                "prompt": pair.get("prompt", ""),
                "blind_pack_path": display_path(blind_pack_path),
                "decisions_path": display_path(decisions_path),
                "commands": {
                    "prepare_review_kit": "python3 scripts/yao.py output-review-kit",
                    "write_template": "python3 scripts/adjudicate_output_review.py --write-template",
                    "adjudicate": "python3 scripts/yao.py output-review",
                    "refresh_review_studio": "python3 scripts/yao.py review-studio .",
                },
                "required_fields": {
                    "winner_variant": "A or B after reading only the blind review pack.",
                    "confidence": "Optional number from 0 to 1.",
                    "reason": "Short rationale; do not reveal baseline or with-skill labels before adjudication.",
                },
                "privacy_contract": [
                    "Do not paste raw private user data into the decision reason.",
                    "Do not open the answer key before reviewer choices are recorded.",
                    "Leave winner_variant blank when the reviewer is not ready to decide.",
                ],
            }
        )
    return checklist


def add_checklist_summary(summary: dict[str, Any], checklist: list[dict[str, Any]]) -> dict[str, Any]:
    enriched = dict(summary)
    enriched["reviewer_checklist_count"] = len(checklist)
    enriched["reviewer_checklist_pending_count"] = sum(1 for item in checklist if item["readiness"] == "awaiting-decision")
    enriched["reviewer_checklist_invalid_count"] = sum(1 for item in checklist if item["readiness"] == "fix-decision")
    enriched["reviewer_checklist_ready_count"] = sum(1 for item in checklist if item["readiness"] == "adjudicated")
    return enriched


def render_reviewer_checklist(checklist: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Reviewer Checklist",
        "",
        "| Case | Readiness | Answer key | Decision file |",
        "| --- | --- | --- | --- |",
    ]
    if not checklist:
        lines.append("| `none` | `adjudicated` | n/a | none |")
        return lines
    for item in checklist:
        answer_key = "visible" if item.get("answer_key_visible") else "hidden"
        lines.append(
            f"| `{item['case_id']}` | `{item['readiness']}` | `{answer_key}` | `{item['decisions_path']}` |"
        )
    for item in checklist:
        lines.extend(["", f"### {item['case_id']}", ""])
        lines.append(f"- readiness: `{item['readiness']}`")
        lines.append(f"- blocking reason: {item['blocking_reason']}")
        lines.append(f"- answer key visible: `{str(item['answer_key_visible']).lower()}`")
        lines.append(f"- blind pack: `{item['blind_pack_path']}`")
        lines.append(f"- decisions: `{item['decisions_path']}`")
        lines.extend(["", "#### Commands", ""])
        for label, command in item.get("commands", {}).items():
            lines.append(f"- {label}: `{command}`")
        lines.extend(["", "#### Required Fields", ""])
        for label, description in item.get("required_fields", {}).items():
            lines.append(f"- {label}: {description}")
        lines.extend(["", "#### Privacy Contract", ""])
        lines.extend(f"- {contract}" for contract in item.get("privacy_contract", []))
    return lines


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Output Review Adjudication",
        "",
        "This report adjudicates reviewer choices from the blind A/B output review pack against the separate answer key.",
        "",
        f"- Pairs: `{summary['pair_count']}`",
        f"- Judgments: `{summary['judgment_count']}`",
        f"- Pending: `{summary['pending_count']}`",
        f"- Agreement rate: `{summary['agreement_rate'] if summary['agreement_rate'] is not None else 'n/a'}`",
        f"- Invalid decisions: `{summary['invalid_decision_count']}`",
        f"- Answer keys revealed: `{summary['answer_revealed_count']}`",
        f"- Pending/invalid answers hidden: `{summary['pending_answer_hidden_count']}`",
        f"- Reviewer checklist: `{summary['reviewer_checklist_ready_count']}` ready / `{summary['reviewer_checklist_count']}` total",
        "",
    ]
    if summary["judgment_count"] == 0:
        lines.extend(
            [
                "No reviewer decisions recorded yet.",
                "",
                "Generate a template with `--write-template`, fill `winner_variant` with `A` or `B`, then rerun adjudication.",
                "Expected winners stay hidden until a valid reviewer decision is recorded.",
                "",
            ]
        )
    lines.extend(
        [
            "## Case Adjudication",
            "",
            "| Case | Reviewer | Expected | Status | Confidence | Reason |",
            "| --- | --- | --- | --- | ---: | --- |",
        ]
    )
    for item in payload["pairs"]:
        confidence = "" if item.get("confidence") is None else str(item["confidence"])
        reason = str(item.get("reason", "")).replace("|", "\\|") or ""
        expected = item.get("expected_winner_variant", "") if item.get("expected_revealed") else "hidden"
        lines.append(
            f"| {item['case_id']} | {item.get('reviewer_winner_variant', '') or 'pending'} | "
            f"{expected} | {item['status']} | {confidence} | {reason} |"
        )
    if payload.get("failures"):
        lines.extend(["", "## Failures", ""])
        for failure in payload["failures"]:
            lines.append(f"- {failure}")
    lines.extend(["", *render_reviewer_checklist(payload.get("reviewer_checklist", []))])
    lines.extend(
        [
            "",
            "## Next Fixes",
            "",
            "- Keep the blind review pack separate from the answer key until decisions are recorded.",
            "- Treat disagreement cases as prompts for rubric tuning or output improvement.",
            "- Add model-executed holdout runs after this human adjudication harness is stable.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def adjudicate_output_review(
    blind_pack_path: Path,
    answer_key_path: Path,
    decisions_path: Path,
    output_json: Path,
    output_md: Path,
    write_template: bool = False,
) -> dict[str, Any]:
    blind_pack, failures = load_json(blind_pack_path)
    answer_key, answer_failures = load_json(answer_key_path)
    failures.extend(answer_failures)
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

    pairs_by_id = pair_index(blind_pack)
    answers_by_id = answer_index(answer_key)
    decisions_by_id, index_failures = decision_index(decisions_payload)
    failures.extend(index_failures)

    for case_id in decisions_by_id:
        if case_id not in pairs_by_id:
            failures.append(f"decision references unknown case_id: {case_id}")

    adjudicated_pairs: list[dict[str, Any]] = []
    for case_id, pair in pairs_by_id.items():
        adjudicated, pair_failures = adjudicate_pair(case_id, pair, answers_by_id.get(case_id), decisions_by_id.get(case_id))
        adjudicated_pairs.append(adjudicated)
        failures.extend(pair_failures)

    summary = build_summary(adjudicated_pairs, failures)
    reviewer_checklist = build_reviewer_checklist(adjudicated_pairs, blind_pack_path, decisions_path)
    summary = add_checklist_summary(summary, reviewer_checklist)
    payload = {
        "schema_version": "1.0",
        "ok": not failures,
        "summary": summary,
        "reviewer": decisions_payload.get("reviewer", ""),
        "reviewed_at": decisions_payload.get("reviewed_at", ""),
        "artifacts": {
            "blind_pack": display_path(blind_pack_path),
            "answer_key": display_path(answer_key_path),
            "decisions": display_path(decisions_path),
            "json": display_path(output_json),
            "markdown": display_path(output_md),
        },
        "template_written": template_written,
        "pairs": adjudicated_pairs,
        "reviewer_checklist": reviewer_checklist,
        "failures": failures,
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(payload), encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Adjudicate blind A/B output review decisions against the answer key.")
    parser.add_argument("--blind-pack", default=str(DEFAULT_BLIND_PACK))
    parser.add_argument("--answer-key", default=str(DEFAULT_ANSWER_KEY))
    parser.add_argument("--decisions", default=str(DEFAULT_DECISIONS))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--write-template", action="store_true")
    args = parser.parse_args()

    payload = adjudicate_output_review(
        Path(args.blind_pack).resolve(),
        Path(args.answer_key).resolve(),
        Path(args.decisions).resolve(),
        Path(args.output_json).resolve(),
        Path(args.output_md).resolve(),
        write_template=args.write_template,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["ok"] else 2)


if __name__ == "__main__":
    main()
