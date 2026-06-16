#!/usr/bin/env python3
import re
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by world_class_evidence_contract.py to validate blind A/B human adjudication evidence from decision rows."

REVIEWED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}:\d{2}Z)?$")
RAW_CONTENT_FIELDS = {
    "assistant_message",
    "assistant_messages",
    "baseline_output",
    "input",
    "inputs",
    "message",
    "messages",
    "model_output",
    "output",
    "outputs",
    "prompt",
    "prompts",
    "raw_content",
    "raw_output",
    "raw_prompt",
    "transcript",
    "transcripts",
    "user_message",
    "user_messages",
    "with_skill_output",
}
ANSWER_KEY_FIELDS = {
    "answer_key",
    "baseline_label",
    "expected",
    "expected_winner",
    "expected_winner_role",
    "expected_winner_variant",
    "label",
    "variant_label",
    "with_skill_label",
}


def add_error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def real_int(value: Any) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def require_real_text(errors: list[str], value: Any, field: str) -> None:
    add_error(errors, bool(str(value or "").strip()), f"{field} is required")


def object_list(value: Any) -> list[dict[str, Any]]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def case_ids(items: list[dict[str, Any]]) -> list[str]:
    return [str(item.get("case_id", "")).strip() for item in items]


def duplicate_case_ids(ids: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for case_id in ids:
        if case_id in seen and case_id not in duplicates:
            duplicates.append(case_id)
        seen.add(case_id)
    return duplicates


def forbidden_decision_field_paths(value: Any, prefix: str) -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).strip()
            child_path = f"{prefix}.{key_text}"
            if key_text.lower() in RAW_CONTENT_FIELDS or key_text.lower() in ANSWER_KEY_FIELDS:
                found.append(child_path)
            found.extend(forbidden_decision_field_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(forbidden_decision_field_paths(child, f"{prefix}[{index}]"))
    return found


def confidence_valid(value: Any) -> bool:
    if value is None or value == "":
        return True
    if isinstance(value, bool):
        return False
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return False
    return 0 <= parsed <= 1


def validate_decision_rows(
    decisions: list[dict[str, Any]],
    expected_case_ids: set[str],
    errors: list[str],
) -> None:
    decision_ids = case_ids(decisions)
    add_error(errors, not any(not case_id for case_id in decision_ids), "human-adjudication decisions must include case_id for every row")
    duplicates = duplicate_case_ids([case_id for case_id in decision_ids if case_id])
    add_error(errors, not duplicates, "human-adjudication decisions must not contain duplicate case_id values")
    add_error(
        errors,
        set(decision_ids) == expected_case_ids,
        "human-adjudication decisions case_id set must match adjudication pairs",
    )
    for index, item in enumerate(decisions, start=1):
        blocked = forbidden_decision_field_paths(item, f"decisions[{index}]")
        add_error(
            errors,
            not blocked,
            "human-adjudication decisions must not include raw content or answer-key fields: "
            + ", ".join(blocked[:8]),
        )
        winner = str(item.get("winner_variant", "")).strip().upper()
        add_error(errors, winner in {"A", "B"}, "human-adjudication decisions must include A/B winner_variant for every case")
        add_error(errors, confidence_valid(item.get("confidence")), "human-adjudication decisions confidence must be between 0 and 1")
        add_error(errors, bool(str(item.get("reason", "")).strip()), "human-adjudication decisions must include reviewer reason for every case")


def validate_adjudicated_pairs(
    pairs: list[dict[str, Any]],
    expected_count: int,
    errors: list[str],
) -> set[str]:
    pair_ids = case_ids(pairs)
    add_error(errors, len(pairs) == expected_count, "human-adjudication adjudication pairs length must equal summary.pair_count")
    add_error(errors, not any(not case_id for case_id in pair_ids), "human-adjudication adjudication pairs must include case_id")
    duplicates = duplicate_case_ids([case_id for case_id in pair_ids if case_id])
    add_error(errors, not duplicates, "human-adjudication adjudication pairs must not contain duplicate case_id values")
    for item in pairs:
        case_id = str(item.get("case_id", "")).strip()
        status = str(item.get("status", "")).strip()
        add_error(
            errors,
            status in {"match", "disagree"},
            f"human-adjudication adjudication pair {case_id or '<missing>'} must be match or disagree",
        )
        add_error(
            errors,
            item.get("expected_revealed") is True,
            f"human-adjudication adjudication pair {case_id or '<missing>'} must reveal expected winner only after valid decision",
        )
        add_error(
            errors,
            str(item.get("reviewer_winner_variant", "")).strip().upper() in {"A", "B"},
            f"human-adjudication adjudication pair {case_id or '<missing>'} must include reviewer_winner_variant",
        )
    return {case_id for case_id in pair_ids if case_id}


def validate_human_adjudication_report(
    adjudication: dict[str, Any],
    decisions: dict[str, Any],
    provenance: dict[str, Any],
    errors: list[str],
) -> None:
    summary = adjudication.get("summary", {}) if isinstance(adjudication.get("summary", {}), dict) else {}
    pair_count = real_int(summary.get("pair_count"))
    judgment_count = real_int(summary.get("judgment_count"))
    pending_count = real_int(summary.get("pending_count"))
    invalid_decision_count = real_int(summary.get("invalid_decision_count"))
    answer_revealed_count = real_int(summary.get("answer_revealed_count"))
    pending_answer_hidden_count = real_int(summary.get("pending_answer_hidden_count"))
    checklist_ready_count = real_int(summary.get("reviewer_checklist_ready_count"))
    checklist_count = real_int(summary.get("reviewer_checklist_count"))

    add_error(errors, adjudication.get("ok") is True, "human-adjudication adjudication report ok must be true")
    add_error(errors, bool(pair_count and pair_count > 0), "human-adjudication adjudication summary.pair_count must be >0")
    add_error(
        errors,
        bool(pair_count and judgment_count == pair_count),
        "human-adjudication adjudication summary.judgment_count must equal summary.pair_count",
    )
    add_error(errors, pending_count == 0, "human-adjudication adjudication summary.pending_count must be 0")
    add_error(errors, invalid_decision_count == 0, "human-adjudication adjudication summary.invalid_decision_count must be 0")
    add_error(
        errors,
        bool(pair_count and answer_revealed_count == pair_count),
        "human-adjudication adjudication summary.answer_revealed_count must equal summary.pair_count",
    )
    add_error(errors, pending_answer_hidden_count == 0, "human-adjudication adjudication summary.pending_answer_hidden_count must be 0")
    add_error(errors, summary.get("needs_review") is False, "human-adjudication adjudication summary.needs_review must be false")
    if checklist_count is not None or checklist_ready_count is not None:
        add_error(
            errors,
            bool(pair_count and checklist_count == pair_count and checklist_ready_count == pair_count),
            "human-adjudication reviewer checklist must be ready for every pair",
        )
    add_error(errors, not adjudication.get("failures"), "human-adjudication adjudication failures must be empty")

    decision_rows = object_list(decisions.get("decisions", []))
    add_error(errors, decisions.get("schema_version") == "1.0", "human-adjudication decisions.schema_version must be 1.0")
    reviewer = str(decisions.get("reviewer", "")).strip()
    reviewed_at = str(decisions.get("reviewed_at", "")).strip()
    require_real_text(errors, reviewer, "human-adjudication decisions.reviewer")
    add_error(
        errors,
        bool(REVIEWED_AT_RE.match(reviewed_at)),
        "human-adjudication decisions.reviewed_at must use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ",
    )
    add_error(
        errors,
        bool(pair_count and len(decision_rows) == pair_count),
        "human-adjudication decisions count must equal adjudication summary.pair_count",
    )

    expected_case_ids = validate_adjudicated_pairs(object_list(adjudication.get("pairs", [])), int(pair_count or 0), errors)
    validate_decision_rows(decision_rows, expected_case_ids, errors)

    provenance_reviewer = str(provenance.get("reviewer", "")).strip()
    add_error(
        errors,
        bool(reviewer and provenance_reviewer and reviewer == provenance_reviewer),
        "human-adjudication provenance.reviewer must match decisions.reviewer",
    )
    add_error(errors, adjudication.get("reviewer") == reviewer, "human-adjudication adjudication reviewer must match decisions.reviewer")
    add_error(
        errors,
        adjudication.get("reviewed_at") == reviewed_at,
        "human-adjudication adjudication reviewed_at must match decisions.reviewed_at",
    )
