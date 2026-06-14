#!/usr/bin/env python3
"""Shared source-evidence checks for world-class evidence workflows."""

from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by world-class evidence reports to keep source-evidence readiness checks consistent."


SOURCE_CHECK_SPECS = {
    "provider-holdout": [
        ("Provider model run", "model_executed_count", ">0", "Run provider-backed output-exec with real credentials."),
        ("Timing observed", "timing_observed_count", ">0", "Provider execution should record timing metadata."),
        ("Token usage observed", "token_observed_count", ">0", "Provider execution should return non-estimated token usage."),
    ],
    "human-adjudication": [
        ("Review pairs exist", "pair_count", ">0", "Generate the blind A/B review pack."),
        ("No pending decisions", "pending_count", "==0", "Record a reviewer choice for every pair."),
        ("Judgments complete", "judgment_count", "==pair_count", "Every pair needs one valid human judgment."),
        ("No invalid decisions", "invalid_decision_count", "==0", "Fix malformed winner/confidence entries."),
    ],
    "native-permission-enforcement": [
        ("Native enforcement", "native_enforcement_count", ">0", "Collect real target-client or external runtime guard proof."),
        ("Probe failures", "failure_count", "==0", "Runtime permission probes must stay clean."),
        ("Installer support", "installer_enforcement_ready", "true", "Installer enforcement is supporting evidence, not native proof."),
    ],
    "native-client-telemetry": [
        ("External events", "external_source_events", ">0", "Import at least one metadata-only event from a real client."),
        ("Adoption sample", "adoption_sample_count", ">0", "Telemetry must include adoption outcome evidence."),
        ("Raw content blocked", "raw_content_allowed", "false", "Telemetry must stay metadata-only."),
    ],
}


def source_check_passed(actual: Any, expected: str, observed_state: dict[str, Any]) -> bool:
    if expected == ">0":
        return isinstance(actual, (int, float)) and actual > 0
    if expected == "==0":
        return actual == 0
    if expected == "true":
        return actual is True
    if expected == "false":
        return actual is False
    if expected == "==pair_count":
        return actual == observed_state.get("pair_count") and isinstance(actual, (int, float)) and actual > 0
    return False


def item_evidence_key(item: dict[str, Any]) -> str:
    return str(item.get("evidence_key") or item.get("key") or "")


def item_observed_state(item: dict[str, Any]) -> dict[str, Any]:
    observed = item.get("observed_state", {})
    return observed if isinstance(observed, dict) else {}


def item_source_accepted(item: dict[str, Any], observed_state: dict[str, Any]) -> bool:
    return item.get("source_accepted") is True or observed_state.get("accepted") is True


def build_source_checklist(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in items:
        key = item_evidence_key(item)
        observed_state = item_observed_state(item)
        for label, field, expected, next_action in SOURCE_CHECK_SPECS.get(key, []):
            actual = observed_state.get(field)
            passed = source_check_passed(actual, expected, observed_state)
            rows.append(
                {
                    "evidence_key": key,
                    "label": label,
                    "field": field,
                    "expected": expected,
                    "actual": actual,
                    "status": "pass" if passed else "blocked",
                    "source_accepted": item_source_accepted(item, observed_state),
                    "next_action": next_action,
                }
            )
    return rows


def summarize_source_checklist(rows: list[dict[str, Any]]) -> dict[str, int]:
    pass_count = sum(1 for item in rows if item.get("status") == "pass")
    blocked_count = sum(1 for item in rows if item.get("status") != "pass")
    return {
        "source_check_count": len(rows),
        "source_pass_count": pass_count,
        "source_blocked_count": blocked_count,
    }
