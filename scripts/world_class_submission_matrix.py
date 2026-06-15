#!/usr/bin/env python3
"""Build operator-facing readiness matrices for world-class submission kits."""

from collections import defaultdict
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Shared by submission kit rendering to summarize draft, artifact, and source-check readiness."


def _by_key(rows: list[dict[str, Any]], key_name: str = "evidence_key") -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = str(row.get(key_name, "")).strip()
        if key:
            grouped[key].append(row)
    return dict(grouped)


def _draft_status(files_by_key: dict[str, list[dict[str, Any]]], key: str) -> tuple[str, str]:
    rows = files_by_key.get(key, [])
    if not rows:
        return "missing", ""
    row = rows[0]
    return str(row.get("status", "missing")), str(row.get("output_path", ""))


def _first_blocked_action(source_rows: list[dict[str, Any]]) -> str:
    for row in source_rows:
        if row.get("status") != "pass":
            action = str(row.get("next_action", "")).strip()
            if action:
                return action
    return ""


def _stage(
    *,
    draft_status: str,
    artifact_missing_count: int,
    source_blocked_count: int,
    invalid_draft: bool,
) -> str:
    if draft_status == "skipped" or invalid_draft:
        return "fix-draft"
    if draft_status == "missing":
        return "prepare-draft"
    if source_blocked_count:
        return "collect-source"
    if artifact_missing_count:
        return "fix-artifacts"
    return "validate-packet"


def _next_action(
    *,
    stage: str,
    draft_path: str,
    first_blocked_action: str,
    artifact_missing_count: int,
) -> str:
    if stage == "fix-draft":
        return "Fix skipped or invalid draft generation before evidence review."
    if stage == "prepare-draft":
        return "Generate the evidence draft, then keep template_only true until real evidence exists."
    if stage == "collect-source":
        return first_blocked_action or "Complete blocked source checks before ledger review."
    if stage == "fix-artifacts":
        return f"Resolve {artifact_missing_count} missing artifact reference(s) or replace globs with concrete paths."
    if draft_path:
        return f"Edit {draft_path}, set real provenance fields, validate intake, then refresh the ledger."
    return "Validate intake, refresh the ledger, then run the public claim guard."


def build_evidence_matrix(
    evidence_items: list[dict[str, Any]],
    files: list[dict[str, Any]],
    artifact_checklist: list[dict[str, Any]],
    source_checklist: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Combine draft, artifact, and source-check readiness into one operator matrix."""
    files_by_key = _by_key(files)
    artifacts_by_key = _by_key(artifact_checklist)
    sources_by_key = _by_key(source_checklist)
    matrix: list[dict[str, Any]] = []
    for item in evidence_items:
        key = str(item.get("evidence_key", "")).strip()
        if not key:
            continue
        artifact_rows = artifacts_by_key.get(key, [])
        source_rows = sources_by_key.get(key, [])
        draft_status, draft_path = _draft_status(files_by_key, key)
        artifact_ready_count = sum(1 for row in artifact_rows if row.get("artifact_ref_ready"))
        artifact_missing_count = len(artifact_rows) - artifact_ready_count
        source_pass_count = sum(1 for row in source_rows if row.get("status") == "pass")
        source_blocked_count = len(source_rows) - source_pass_count
        invalid_draft = draft_status not in {"written", "exists"}
        stage = _stage(
            draft_status=draft_status,
            artifact_missing_count=artifact_missing_count,
            source_blocked_count=source_blocked_count,
            invalid_draft=invalid_draft,
        )
        first_action = _first_blocked_action(source_rows)
        matrix.append(
            {
                "evidence_key": key,
                "label": item.get("label", key),
                "category": item.get("category", ""),
                "owner": item.get("owner", ""),
                "stage": stage,
                "draft_status": draft_status,
                "draft_path": draft_path,
                "artifact_ready_count": artifact_ready_count,
                "artifact_total_count": len(artifact_rows),
                "artifact_missing_count": artifact_missing_count,
                "source_pass_count": source_pass_count,
                "source_check_count": len(source_rows),
                "source_blocked_count": source_blocked_count,
                "next_action": _next_action(
                    stage=stage,
                    draft_path=draft_path,
                    first_blocked_action=first_action,
                    artifact_missing_count=artifact_missing_count,
                ),
                "counts_as_completion": False,
            }
        )
    return matrix


def summarize_evidence_matrix(matrix: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "evidence_matrix_count": len(matrix),
        "evidence_matrix_collect_source_count": sum(1 for item in matrix if item.get("stage") == "collect-source"),
        "evidence_matrix_prepare_draft_count": sum(1 for item in matrix if item.get("stage") == "prepare-draft"),
        "evidence_matrix_fix_artifacts_count": sum(1 for item in matrix if item.get("stage") == "fix-artifacts"),
        "evidence_matrix_validate_packet_count": sum(1 for item in matrix if item.get("stage") == "validate-packet"),
        "evidence_matrix_counts_as_completion": 0,
    }
