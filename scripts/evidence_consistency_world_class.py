from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_evidence_consistency.py to isolate world-class evidence workflow consistency checks."


def keyed_items(payload: dict[str, Any], collection_key: str) -> dict[str, dict[str, Any]]:
    collection = payload.get(collection_key)
    if not isinstance(collection, list):
        return {}
    keyed: dict[str, dict[str, Any]] = {}
    for item in collection:
        if not isinstance(item, dict):
            continue
        key = item.get("key") or item.get("evidence_key")
        if isinstance(key, str):
            keyed[key] = item
    return keyed


def command_key_set(item: dict[str, Any]) -> set[str]:
    commands = item.get("commands")
    if isinstance(commands, dict):
        return {key for key, value in commands.items() if isinstance(key, str) and value}
    if isinstance(commands, list):
        keys: set[str] = set()
        for command in commands:
            if isinstance(command, dict) and isinstance(command.get("key"), str) and command.get("command"):
                keys.add(command["key"])
        return keys
    return set()


def world_class_review_action_steps(review_studio: dict[str, Any]) -> dict[str, dict[str, Any]]:
    actions = review_studio.get("review_actions")
    if not isinstance(actions, list):
        return {}
    for action in actions:
        if not isinstance(action, dict) or action.get("gate_key") != "world-class-evidence":
            continue
        steps = action.get("evidence_steps")
        if not isinstance(steps, list):
            return {}
        keyed: dict[str, dict[str, Any]] = {}
        for step in steps:
            if isinstance(step, dict) and isinstance(step.get("key"), str):
                keyed[step["key"]] = step
        return keyed
    return {}


def command_groups_present(command_keys: set[str]) -> dict[str, bool]:
    return {
        "prepare_submission": "prepare_submission" in command_keys,
        "validate_intake": "validate_intake" in command_keys,
        "submission_review": bool({"submission_review", "review_queue"} & command_keys),
        "refresh_ledger": "refresh_ledger" in command_keys,
        "guard_claim": "guard_claim" in command_keys,
    }


def has_next_action(item: dict[str, Any]) -> bool:
    for key in ["next_action", "audit_next_action"]:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return True
    return False


def command_expectations(keys: list[str]) -> dict[str, dict[str, dict[str, bool]]]:
    expected_group = {
        "prepare_submission": True,
        "validate_intake": True,
        "submission_review": True,
        "refresh_ledger": True,
        "guard_claim": True,
    }
    return {
        key: {
            "intake": dict(expected_group),
            "operator_runbook": dict(expected_group),
            "review_studio": dict(expected_group),
        }
        for key in keys
    }


def build_world_class_workflow_check(
    *,
    ledger: dict[str, Any],
    world_class_plan: dict[str, Any],
    world_class_intake: dict[str, Any],
    world_class_submission_review: dict[str, Any],
    world_class_operator_runbook: dict[str, Any],
    review_studio: dict[str, Any],
    report_paths: dict[str, str],
) -> dict[str, Any]:
    ledger_summary = ledger.get("summary") if isinstance(ledger.get("summary"), dict) else {}
    plan_summary = world_class_plan.get("summary") if isinstance(world_class_plan.get("summary"), dict) else {}
    intake_summary = world_class_intake.get("summary") if isinstance(world_class_intake.get("summary"), dict) else {}
    submission_review_summary = (
        world_class_submission_review.get("summary")
        if isinstance(world_class_submission_review.get("summary"), dict)
        else {}
    )
    operator_runbook_summary = (
        world_class_operator_runbook.get("summary")
        if isinstance(world_class_operator_runbook.get("summary"), dict)
        else {}
    )

    ledger_items = keyed_items(ledger, "entries")
    plan_tasks = keyed_items(world_class_plan, "tasks")
    intake_checklist = keyed_items(world_class_intake, "operator_checklist")
    submission_review_items = keyed_items(world_class_submission_review, "items")
    operator_runbook_items = keyed_items(world_class_operator_runbook, "items")
    coordination_plan = (
        world_class_operator_runbook.get("coordination_plan")
        if isinstance(world_class_operator_runbook.get("coordination_plan"), list)
        else []
    )
    release_gate = (
        world_class_operator_runbook.get("release_gate")
        if isinstance(world_class_operator_runbook.get("release_gate"), dict)
        else {}
    )
    review_action_steps = world_class_review_action_steps(review_studio)
    pending_keys = sorted(key for key, item in ledger_items.items() if item.get("status") != "accepted")
    operator_coordination_keys = sorted(
        key
        for key in {str(step.get("evidence_key", "")) for step in coordination_plan if isinstance(step, dict)}
        if key
    )

    actual_command_groups = {
        key: {
            "intake": command_groups_present(command_key_set(intake_checklist.get(key, {}))),
            "operator_runbook": command_groups_present(command_key_set(operator_runbook_items.get(key, {}))),
            "review_studio": command_groups_present(command_key_set(review_action_steps.get(key, {}))),
        }
        for key in pending_keys
    }
    expected = {
        "keys": pending_keys,
        "pending_count": ledger_summary.get("pending_count"),
        "human_pending_count": ledger_summary.get("human_pending_count"),
        "external_pending_count": ledger_summary.get("external_pending_count"),
        "source_check_count": ledger_summary.get("source_check_count"),
        "source_pass_count": ledger_summary.get("source_pass_count"),
        "source_blocked_count": ledger_summary.get("source_blocked_count"),
        "plan_keys": pending_keys,
        "intake_keys": pending_keys,
        "submission_review_keys": pending_keys,
        "operator_runbook_keys": pending_keys,
        "operator_coordination_keys": pending_keys,
        "operator_coordination_counts_as_completion": False,
        "operator_release_gate_ready": ledger_summary.get("ready_to_claim_world_class") is True,
        "operator_release_gate_counts_as_completion": False,
        "review_studio_keys": pending_keys,
        "intake_ready_to_claim_world_class": False,
        "submission_review_ready_to_claim_world_class": False,
        "submission_review_counts_as_completion": False,
        "operator_runbook_ready_to_claim_world_class": False,
        "operator_runbook_counts_as_completion": False,
        "next_actions_present": {key: True for key in pending_keys},
        "commands": command_expectations(pending_keys),
    }
    actual = {
        "keys": pending_keys,
        "pending_count": plan_summary.get("task_count"),
        "human_pending_count": plan_summary.get("human_task_count"),
        "external_pending_count": plan_summary.get("external_task_count"),
        "source_check_count": submission_review_summary.get("source_check_count"),
        "source_pass_count": submission_review_summary.get("source_pass_count"),
        "source_blocked_count": submission_review_summary.get("source_blocked_count"),
        "plan_keys": sorted(plan_tasks),
        "intake_keys": sorted(intake_checklist),
        "submission_review_keys": sorted(submission_review_items),
        "operator_runbook_keys": sorted(operator_runbook_items),
        "operator_coordination_keys": operator_coordination_keys,
        "operator_coordination_counts_as_completion": operator_runbook_summary.get(
            "coordination_counts_as_completion"
        ),
        "operator_release_gate_ready": release_gate.get("ready"),
        "operator_release_gate_counts_as_completion": release_gate.get("counts_as_completion"),
        "review_studio_keys": sorted(review_action_steps),
        "intake_ready_to_claim_world_class": intake_summary.get("ready_to_claim_world_class"),
        "submission_review_ready_to_claim_world_class": submission_review_summary.get("ready_to_claim_world_class"),
        "submission_review_counts_as_completion": submission_review_summary.get(
            "review_counts_submission_as_completion"
        ),
        "operator_runbook_ready_to_claim_world_class": operator_runbook_summary.get("ready_to_claim_world_class"),
        "operator_runbook_counts_as_completion": operator_runbook_summary.get("runbook_counts_as_completion"),
        "next_actions_present": {
            key: all(
                has_next_action(collection.get(key, {}))
                for collection in [plan_tasks, intake_checklist, submission_review_items, review_action_steps]
            )
            for key in pending_keys
        },
        "commands": actual_command_groups,
    }
    return {
        "key": "world-class-evidence-workflow-coverage",
        "label": "World-class evidence workflows cover every pending ledger entry",
        "status": "pass" if expected == actual else "fail",
        "expected": expected,
        "actual": actual,
        "paths": [
            report_paths["world_class_ledger"],
            report_paths["world_class_plan"],
            report_paths["world_class_intake"],
            report_paths["world_class_submission_review"],
            report_paths["world_class_operator_runbook"],
            report_paths["review_studio"],
        ],
        "detail": (
            "Every pending world-class evidence key must have matching plan, intake, submission review, "
            "operator runbook, and Review Studio actions without counting planned work as completion."
        ),
    }
