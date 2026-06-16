#!/usr/bin/env python3
import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from adjudicate_output_review import (
    DEFAULT_ANSWER_KEY,
    DEFAULT_BLIND_PACK,
    DEFAULT_DECISIONS,
    DEFAULT_OUTPUT_JSON,
    DEFAULT_OUTPUT_MD,
    adjudicate_output_review,
    build_decision_template,
    normalize_variant,
    pair_index,
)


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Imports human blind A/B reviewer decisions into the canonical output-review decision file."

RAW_CONTENT_FIELDS = {
    "api_key",
    "prompt",
    "prompts",
    "input",
    "inputs",
    "output",
    "outputs",
    "transcript",
    "transcripts",
    "message",
    "messages",
    "user_message",
    "user_messages",
    "assistant_message",
    "assistant_messages",
    "model_output",
    "baseline_output",
    "with_skill_output",
    "raw_content",
    "raw_prompt",
    "raw_provider_prompt",
    "raw_user_content",
    "raw_output",
    "credential",
    "credentials",
    "secret",
    "secrets",
    "token",
}

ANSWER_KEY_FIELDS = {
    "expected",
    "expected_winner",
    "expected_winner_role",
    "expected_winner_variant",
    "answer_key",
    "label",
    "variant_label",
    "baseline_label",
    "with_skill_label",
}


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def load_json(path: Path) -> tuple[Any, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [f"Invalid JSON file {display_path(path)}: {exc}"]


def detect_format(path: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return "jsonl"
    if suffix == ".csv":
        return "csv"
    return "json"


def read_decision_source(path: Path, source_format: str) -> tuple[dict[str, Any], list[dict[str, Any]], list[str]]:
    if not path.exists():
        return {}, [], [f"Missing decision source: {display_path(path)}"]
    if source_format == "json":
        payload, failures = load_json(path)
        if failures:
            return {}, [], failures
        if isinstance(payload, list):
            return {}, payload, []
        if not isinstance(payload, dict):
            return {}, [], ["JSON decision source must be an object or list"]
        decisions = payload.get("decisions", [])
        if not isinstance(decisions, list):
            return payload, [], ["decisions must be a list"]
        return payload, decisions, []
    if source_format == "jsonl":
        decisions: list[dict[str, Any]] = []
        failures: list[str] = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                failures.append(f"JSONL line {line_number} is invalid: {exc}")
                continue
            if not isinstance(item, dict):
                failures.append(f"JSONL line {line_number} must be an object")
                continue
            decisions.append(item)
        return {}, decisions, failures
    if source_format == "csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return {}, [dict(row) for row in csv.DictReader(handle)], []
    return {}, [], [f"Unsupported decision source format: {source_format}"]


def known_case_ids(blind_pack_path: Path) -> tuple[set[str], list[str]]:
    payload, failures = load_json(blind_pack_path)
    if failures:
        return set(), failures
    if not isinstance(payload, dict):
        return set(), [f"Blind pack root must be an object: {display_path(blind_pack_path)}"]
    pairs = pair_index(payload)
    if not pairs:
        return set(), [f"Blind pack has no pairs: {display_path(blind_pack_path)}"]
    return set(pairs), []


def parse_confidence(value: Any, case_id: str) -> tuple[float | None, str | None]:
    if value is None or str(value).strip() == "":
        return None, None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None, f"{case_id}: confidence must be numeric"
    if parsed < 0 or parsed > 1:
        return None, f"{case_id}: confidence must be between 0 and 1"
    return round(parsed, 3), None


def forbidden_field_paths(value: Any, prefix: str) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).strip()
            child_path = f"{prefix}.{key_text}"
            normalized_key = key_text.casefold()
            if normalized_key in RAW_CONTENT_FIELDS or normalized_key in ANSWER_KEY_FIELDS:
                found.append(child_path)
            found.extend(forbidden_field_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(forbidden_field_paths(child, f"{prefix}[{index}]"))
    return found


def normalize_decisions(
    source_items: list[dict[str, Any]],
    case_ids: set[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    failures: list[str] = []
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(source_items, start=1):
        if not isinstance(item, dict):
            failures.append(f"decision #{index} must be an object")
            continue
        blocked_fields = forbidden_field_paths(item, f"decision #{index}")
        if blocked_fields:
            failures.append(f"decision #{index} contains forbidden raw or answer-key fields: {', '.join(blocked_fields)}")
        case_id = str(item.get("case_id", "")).strip()
        if not case_id:
            failures.append(f"decision #{index} is missing case_id")
            continue
        if case_id not in case_ids:
            failures.append(f"decision #{index} references unknown case_id: {case_id}")
        if case_id in seen:
            failures.append(f"duplicate decision for case_id: {case_id}")
        seen.add(case_id)
        winner = normalize_variant(item.get("winner_variant", item.get("winner", item.get("reviewer_winner_variant", ""))))
        if winner and winner not in {"A", "B"}:
            failures.append(f"{case_id}: winner_variant must be A or B")
        confidence, confidence_failure = parse_confidence(item.get("confidence"), case_id)
        if confidence_failure:
            failures.append(confidence_failure)
        normalized.append(
            {
                "case_id": case_id,
                "winner_variant": winner,
                "confidence": confidence,
                "reason": str(item.get("reason", "")).strip(),
            }
        )
    return normalized, failures


def canonical_payload(
    blind_pack_path: Path,
    source_path: Path,
    source_format: str,
    reviewer: str,
    reviewed_at: str,
    decisions: list[dict[str, Any]],
) -> dict[str, Any]:
    template = build_decision_template(json.loads(blind_pack_path.read_text(encoding="utf-8")))
    completed = sum(1 for item in decisions if item.get("winner_variant") in {"A", "B"})
    return {
        "schema_version": "1.0",
        "reviewer": reviewer,
        "reviewed_at": reviewed_at,
        "decision_contract": template["decision_contract"],
        "import_contract": {
            "schema_version": "1.0",
            "source_path": display_path(source_path),
            "source_format": source_format,
            "raw_content_allowed": False,
            "answer_key_fields_allowed": False,
            "answer_key_opened_by_importer": False,
            "all_or_nothing_write": True,
            "decision_count": len(decisions),
            "completed_decision_count": completed,
            "pending_decision_count": len(decisions) - completed,
        },
        "decisions": decisions,
    }


def import_output_review_decisions(
    source_path: Path,
    blind_pack_path: Path,
    output_json: Path,
    source_format: str = "auto",
    reviewer: str = "",
    reviewed_at: str = "",
    run_adjudication: bool = False,
    answer_key_path: Path = DEFAULT_ANSWER_KEY,
    adjudication_json: Path = DEFAULT_OUTPUT_JSON,
    adjudication_md: Path = DEFAULT_OUTPUT_MD,
) -> dict[str, Any]:
    detected_format = detect_format(source_path, source_format)
    source_meta, source_items, failures = read_decision_source(source_path, detected_format)
    reviewer = reviewer or str(source_meta.get("reviewer", "")).strip()
    reviewed_at = reviewed_at or str(source_meta.get("reviewed_at", "")).strip()
    if not reviewer:
        failures.append("reviewer is required for imported human decisions")
    if not reviewed_at:
        failures.append("reviewed_at is required for imported human decisions")
    case_ids, case_failures = known_case_ids(blind_pack_path)
    failures.extend(case_failures)
    decisions, decision_failures = normalize_decisions(source_items, case_ids)
    failures.extend(decision_failures)
    payload: dict[str, Any] = {
        "schema_version": "1.0",
        "ok": not failures,
        "summary": {
            "decision_count": len(decisions),
            "completed_decision_count": sum(1 for item in decisions if item.get("winner_variant") in {"A", "B"}),
            "pending_decision_count": sum(1 for item in decisions if not item.get("winner_variant")),
            "failure_count": len(failures),
            "canonical_written": False,
            "adjudication_run": False,
        },
        "artifacts": {
            "source": display_path(source_path),
            "blind_pack": display_path(blind_pack_path),
            "decisions": display_path(output_json),
            "adjudication_json": display_path(adjudication_json),
            "adjudication_markdown": display_path(adjudication_md),
        },
        "failures": failures,
    }
    if failures:
        return payload
    canonical = canonical_payload(blind_pack_path, source_path, detected_format, reviewer, reviewed_at, decisions)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(canonical, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["summary"]["canonical_written"] = True
    payload["canonical"] = canonical
    if run_adjudication:
        adjudication = adjudicate_output_review(
            blind_pack_path=blind_pack_path,
            answer_key_path=answer_key_path,
            decisions_path=output_json,
            output_json=adjudication_json,
            output_md=adjudication_md,
        )
        payload["summary"]["adjudication_run"] = True
        payload["summary"]["adjudication_ok"] = adjudication["ok"]
        payload["summary"]["adjudication_pending_count"] = adjudication["summary"]["pending_count"]
        payload["summary"]["adjudication_invalid_decision_count"] = adjudication["summary"]["invalid_decision_count"]
        payload["adjudication_summary"] = adjudication["summary"]
        if not adjudication["ok"]:
            payload["ok"] = False
            payload["failures"] = list(adjudication.get("failures", []))
            payload["summary"]["failure_count"] = len(payload["failures"])
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Import blind A/B reviewer decisions into the canonical output-review decision file.")
    parser.add_argument("--input", required=True, help="Reviewer decision source in JSON, JSONL, or CSV format.")
    parser.add_argument("--format", choices=["auto", "json", "jsonl", "csv"], default="auto")
    parser.add_argument("--blind-pack", default=str(DEFAULT_BLIND_PACK))
    parser.add_argument("--output-json", default=str(DEFAULT_DECISIONS))
    parser.add_argument("--reviewer")
    parser.add_argument("--reviewed-at", default=date.today().isoformat())
    parser.add_argument("--run-adjudication", action="store_true")
    parser.add_argument("--answer-key", default=str(DEFAULT_ANSWER_KEY))
    parser.add_argument("--adjudication-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--adjudication-md", default=str(DEFAULT_OUTPUT_MD))
    args = parser.parse_args()
    payload = import_output_review_decisions(
        source_path=Path(args.input).resolve(),
        blind_pack_path=Path(args.blind_pack).resolve(),
        output_json=Path(args.output_json).resolve(),
        source_format=args.format,
        reviewer=args.reviewer or "",
        reviewed_at=args.reviewed_at or "",
        run_adjudication=args.run_adjudication,
        answer_key_path=Path(args.answer_key).resolve(),
        adjudication_json=Path(args.adjudication_json).resolve(),
        adjudication_md=Path(args.adjudication_md).resolve(),
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if payload["ok"] else 2)


if __name__ == "__main__":
    main()
