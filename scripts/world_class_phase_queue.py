#!/usr/bin/env python3
"""Build phase-ordered operator queues for world-class evidence collection."""

from collections import defaultdict
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by prepare_world_class_submission_kit.py to group repair rows into an operator execution queue."


PHASE_LABELS = {
    "select-evidence": "Select evidence",
    "prepare-draft": "Prepare draft",
    "unblock-access": "Unblock access",
    "attach-artifacts": "Attach artifacts",
    "collect-source": "Collect source",
    "repair": "Repair",
}


def _phase_sort_key(row: dict[str, Any]) -> tuple[int, str, str]:
    return (
        int(row.get("priority", 90) or 90),
        str(row.get("evidence_key", "")),
        str(row.get("target", "")),
    )


def build_phase_queue(repair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group repair rows by execution phase without changing evidence acceptance."""
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in sorted(repair_rows, key=_phase_sort_key):
        phase = str(row.get("phase", "repair") or "repair")
        grouped[phase].append(row)

    queue: list[dict[str, Any]] = []
    for phase_rows in sorted(grouped.values(), key=lambda rows: _phase_sort_key(rows[0])):
        first = phase_rows[0]
        phase = str(first.get("phase", "repair") or "repair")
        blocked_rows = [row for row in phase_rows if row.get("status") != "ready"]
        owners = sorted({str(row.get("owner", "")).strip() for row in phase_rows if str(row.get("owner", "")).strip()})
        evidence_keys = sorted(
            {str(row.get("evidence_key", "")).strip() for row in phase_rows if str(row.get("evidence_key", "")).strip()}
        )
        queue.append(
            {
                "phase": phase,
                "label": PHASE_LABELS.get(phase, phase.replace("-", " ").title()),
                "priority": int(first.get("priority", 90) or 90),
                "status": "blocked" if blocked_rows else "ready",
                "blocked_count": len(blocked_rows),
                "row_count": len(phase_rows),
                "owners": owners,
                "evidence_keys": evidence_keys,
                "next_action_id": first.get("action_id", ""),
                "next_action": first.get("next_action", ""),
                "verification_command": first.get("verification_command", ""),
                "counts_as_completion": False,
                "rows": phase_rows,
            }
        )
    return queue


def summarize_phase_queue(queue: list[dict[str, Any]]) -> dict[str, Any]:
    next_item = next((item for item in queue if item.get("status") != "ready"), queue[0] if queue else {})
    return {
        "phase_queue_count": len(queue),
        "phase_queue_blocked_count": sum(1 for item in queue if item.get("status") != "ready"),
        "phase_queue_row_count": sum(int(item.get("row_count", 0) or 0) for item in queue),
        "phase_queue_next_phase": next_item.get("phase", ""),
        "phase_queue_next_action_id": next_item.get("next_action_id", ""),
        "phase_queue_next_command": next_item.get("verification_command", ""),
        "phase_queue_counts_as_completion": False,
    }
