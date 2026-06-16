#!/usr/bin/env python3
"""Compare world-class phase queues across generated reports."""

from typing import Any

from evidence_consistency_world_class import world_class_review_action_steps
from world_class_phase_queue import build_phase_queue, summarize_phase_queue


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_evidence_consistency.py to prevent preflight and Review Studio phase-queue drift."


def phase_queue_signature(queue: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signature: list[dict[str, Any]] = []
    for item in queue:
        if not isinstance(item, dict):
            continue
        signature.append(
            {
                "phase": item.get("phase"),
                "priority": item.get("priority"),
                "status": item.get("status"),
                "blocked_count": item.get("blocked_count"),
                "row_count": item.get("row_count"),
                "owners": sorted(str(owner) for owner in item.get("owners", [])),
                "evidence_keys": sorted(str(key) for key in item.get("evidence_keys", [])),
                "next_action_id": item.get("next_action_id"),
                "verification_command": item.get("verification_command"),
                "counts_as_completion": item.get("counts_as_completion"),
            }
        )
    return signature


def summary_signature(summary: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "phase_queue_count",
        "phase_queue_blocked_count",
        "phase_queue_row_count",
        "phase_queue_next_phase",
        "phase_queue_next_action_id",
        "phase_queue_next_command",
        "phase_queue_counts_as_completion",
    ]
    return {key: summary.get(key) for key in keys}


def keyed_preflight_items(world_class_preflight: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = world_class_preflight.get("items", []) if isinstance(world_class_preflight, dict) else []
    keyed: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        key = str(item.get("evidence_key", "")).strip()
        if key:
            keyed[key] = item
    return keyed


def keyed_phase_queue_signatures_from_repair_rows(items: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    signatures: dict[str, list[dict[str, Any]]] = {}
    for key, item in items.items():
        rows = item.get("repair_checklist", []) if isinstance(item.get("repair_checklist", []), list) else []
        signatures[key] = phase_queue_signature(build_phase_queue(rows))
    return signatures


def keyed_phase_queue_signatures_from_items(items: dict[str, dict[str, Any]], queue_key: str) -> dict[str, list[dict[str, Any]]]:
    signatures: dict[str, list[dict[str, Any]]] = {}
    for key, item in items.items():
        queue = item.get(queue_key, []) if isinstance(item.get(queue_key, []), list) else []
        signatures[key] = phase_queue_signature(queue)
    return signatures


def any_phase_queue_counts_as_completion(
    *queues: list[dict[str, Any]],
    item_maps: dict[str, dict[str, Any]] | None = None,
) -> bool:
    item_maps = item_maps or {}
    for queue in queues:
        for item in queue:
            if isinstance(item, dict) and item.get("counts_as_completion") is True:
                return True
    for item in item_maps.values():
        queue = item.get("phase_queue", []) if isinstance(item.get("phase_queue", []), list) else []
        for row in queue:
            if isinstance(row, dict) and row.get("counts_as_completion") is True:
                return True
    return False


def build_phase_queue_consistency_check(
    *,
    world_class_preflight: dict[str, Any],
    world_class_operator_runbook: dict[str, Any],
    review_studio: dict[str, Any],
    report_paths: dict[str, str],
) -> dict[str, Any]:
    repair_rows = (
        world_class_preflight.get("repair_checklist", [])
        if isinstance(world_class_preflight.get("repair_checklist", []), list)
        else []
    )
    expected_queue = build_phase_queue(repair_rows)
    expected_summary = summarize_phase_queue(expected_queue)
    preflight_items = keyed_preflight_items(world_class_preflight)
    operator_runbook_items = keyed_preflight_items(world_class_operator_runbook)
    review_steps = world_class_review_action_steps(review_studio)
    expected = {
        "summary": summary_signature(expected_summary),
        "top_level_phase_queue": phase_queue_signature(expected_queue),
        "item_phase_queues": keyed_phase_queue_signatures_from_repair_rows(preflight_items),
        "phase_queue_counts_as_completion": False,
    }
    actual = {
        "summary": summary_signature(
            world_class_preflight.get("summary", {})
            if isinstance(world_class_preflight.get("summary", {}), dict)
            else {}
        ),
        "top_level_phase_queue": phase_queue_signature(
            world_class_preflight.get("phase_queue", [])
            if isinstance(world_class_preflight.get("phase_queue", []), list)
            else []
        ),
        "operator_runbook_summary": summary_signature(
            world_class_operator_runbook.get("summary", {})
            if isinstance(world_class_operator_runbook.get("summary", {}), dict)
            else {}
        ),
        "operator_runbook_top_level_phase_queue": phase_queue_signature(
            world_class_operator_runbook.get("phase_queue", [])
            if isinstance(world_class_operator_runbook.get("phase_queue", []), list)
            else []
        ),
        "item_phase_queues": keyed_phase_queue_signatures_from_items(preflight_items, "phase_queue"),
        "operator_runbook_phase_queues": keyed_phase_queue_signatures_from_items(
            operator_runbook_items,
            "phase_queue",
        ),
        "review_studio_phase_queues": keyed_phase_queue_signatures_from_items(review_steps, "phase_queue"),
        "phase_queue_counts_as_completion": any_phase_queue_counts_as_completion(
            world_class_preflight.get("phase_queue", [])
            if isinstance(world_class_preflight.get("phase_queue", []), list)
            else [],
            world_class_operator_runbook.get("phase_queue", [])
            if isinstance(world_class_operator_runbook.get("phase_queue", []), list)
            else [],
            item_maps={**preflight_items, **operator_runbook_items, **review_steps},
        ),
    }
    expected["operator_runbook_summary"] = expected["summary"]
    expected["operator_runbook_top_level_phase_queue"] = expected["top_level_phase_queue"]
    expected["operator_runbook_phase_queues"] = expected["item_phase_queues"]
    expected["review_studio_phase_queues"] = expected["item_phase_queues"]
    return {
        "key": "world-class-phase-queue-consistency",
        "label": "World-class phase queues mirror repair rows",
        "status": "pass" if expected == actual else "fail",
        "expected": expected,
        "actual": actual,
        "paths": [
            report_paths["world_class_preflight"],
            report_paths["world_class_operator_runbook"],
            report_paths["review_studio"],
        ],
        "detail": (
            "Phase queues must be derived from repair rows in preflight and mirrored into the operator runbook "
            "and Review Studio without counting queue guidance as completion evidence."
        ),
    }
