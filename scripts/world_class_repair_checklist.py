#!/usr/bin/env python3
"""Build machine-readable repair checklists for world-class submission kits."""

from collections import defaultdict
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Shared by submission kit generation to turn readiness blockers into actionable repair rows."


def _by_key(rows: list[dict[str, Any]], key_name: str = "evidence_key") -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = str(row.get(key_name, "")).strip()
        if key:
            grouped[key].append(row)
    return dict(grouped)


def _repair_row(
    *,
    evidence_key: str,
    repair_type: str,
    target: str,
    status: str,
    blocking_reason: str,
    next_action: str,
    source: str,
) -> dict[str, Any]:
    return {
        "evidence_key": evidence_key,
        "repair_type": repair_type,
        "target": target,
        "status": status,
        "blocking_reason": blocking_reason,
        "next_action": next_action,
        "source": source,
        "counts_as_completion": False,
    }


def build_repair_checklist(
    evidence_items: list[dict[str, Any]],
    files: list[dict[str, Any]],
    artifact_checklist: list[dict[str, Any]],
    source_checklist: list[dict[str, Any]],
    unknown_keys: list[str],
) -> list[dict[str, Any]]:
    """Return concrete repair rows for every draft, artifact, and source blocker."""
    files_by_key = _by_key(files)
    artifacts_by_key = _by_key(artifact_checklist)
    sources_by_key = _by_key(source_checklist)
    rows: list[dict[str, Any]] = []
    known_keys = [str(item.get("evidence_key", "")).strip() for item in evidence_items]

    for key in known_keys:
        if not key:
            continue
        draft_rows = files_by_key.get(key, [])
        if not draft_rows:
            rows.append(
                _repair_row(
                    evidence_key=key,
                    repair_type="draft",
                    target=key,
                    status="blocked",
                    blocking_reason="Submission draft was not generated.",
                    next_action="Run the submission kit command again for this evidence key.",
                    source="files",
                )
            )
        for draft in draft_rows:
            draft_status = str(draft.get("status", "")).strip()
            if draft_status not in {"written", "exists"}:
                target = str(draft.get("output_path") or draft.get("template_path") or key)
                errors = draft.get("errors", [])
                error_text = "; ".join(str(error) for error in errors) if isinstance(errors, list) else ""
                rows.append(
                    _repair_row(
                        evidence_key=key,
                        repair_type="draft",
                        target=target,
                        status="blocked",
                        blocking_reason=error_text or f"Draft status is {draft_status or 'unknown'}.",
                        next_action="Fix template generation before asking for ledger review.",
                        source="files",
                    )
                )

        for artifact in artifacts_by_key.get(key, []):
            if artifact.get("artifact_ref_ready"):
                continue
            target = str(artifact.get("path") or artifact.get("source_pattern") or key)
            artifact_status = str(artifact.get("status", "missing"))
            role = str(artifact.get("artifact_role", "supporting-evidence"))
            if artifact.get("concrete_reference_required"):
                action = "Replace the glob with concrete files, then reference the generated SHA-256 digests."
            elif artifact.get("submission_ref_required"):
                action = "Create the required submission artifact or update artifact_refs to a concrete existing aggregate file."
            else:
                action = "Add the supporting artifact if it is needed for reviewer audit."
            rows.append(
                _repair_row(
                    evidence_key=key,
                    repair_type="artifact",
                    target=target,
                    status="blocked",
                    blocking_reason=f"{role} artifact is {artifact_status}.",
                    next_action=action,
                    source="artifact_checklist",
                )
            )

        for source in sources_by_key.get(key, []):
            if source.get("status") == "pass":
                continue
            field = str(source.get("field") or source.get("label") or key)
            rows.append(
                _repair_row(
                    evidence_key=key,
                    repair_type="source-check",
                    target=field,
                    status="blocked",
                    blocking_reason=f"Current value {source.get('actual')!r} does not satisfy {source.get('expected')!r}.",
                    next_action=str(source.get("next_action") or "Collect the required source evidence."),
                    source="source_checklist",
                )
            )

    for key in unknown_keys:
        rows.append(
            _repair_row(
                evidence_key=key,
                repair_type="unknown-key",
                target=key,
                status="blocked",
                blocking_reason="Requested evidence key is not present in the operator checklist.",
                next_action="Use one of the evidence keys listed by world-class-intake.",
                source="unknown_evidence_keys",
            )
        )

    return rows


def summarize_repair_checklist(rows: list[dict[str, Any]]) -> dict[str, Any]:
    blocked_count = sum(1 for row in rows if row.get("status") != "ready")
    return {
        "repair_checklist_count": len(rows),
        "repair_blocked_count": blocked_count,
        "repair_ready_count": len(rows) - blocked_count,
        "repair_counts_as_completion": False,
    }
