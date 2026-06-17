#!/usr/bin/env python3
"""Shared helpers for cross-report evidence consistency checks."""

import json
from pathlib import Path
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_evidence_consistency.py for shared report loading, comparison, and Markdown rendering helpers."

REQUIRED_REPORTS = {
    "benchmark": "reports/benchmark_reproducibility.json",
    "overview": "reports/skill-overview.json",
    "interpretation": "reports/skill-interpretation.json",
    "adoption": "reports/adoption_drift_report.json",
    "world_class_ledger": "reports/world_class_evidence_ledger.json",
    "world_class_plan": "reports/world_class_evidence_plan.json",
    "world_class_intake": "reports/world_class_evidence_intake.json",
    "world_class_preflight": "reports/world_class_evidence_preflight.json",
    "world_class_submission_review": "reports/world_class_submission_review.json",
    "world_class_operator_runbook": "reports/world_class_operator_runbook.json",
    "skill_os2_coverage": "reports/skill_os2_coverage.json",
    "review_studio": "reports/review-studio.json",
    "package_verification": "reports/package_verification.json",
    "install_simulation": "reports/install_simulation.json",
    "trust": "reports/security_trust_report.json",
    "context_budget": "reports/context_budget.json",
    "world_class_claim_guard": "reports/world_class_claim_guard.json",
}
REQUIRED_TEXT_REPORTS = {
    "skill_os2_review": "reports/skill-os-2-review.md",
}
BENCHMARK_SUMMARY_KEYS = [
    "release_lock_ready",
    "required_artifact_count",
    "missing_artifact_count",
    "source_contract_sha256",
    "archive_sha256",
    "world_class_ledger_pending_count",
    "world_class_source_check_count",
    "world_class_source_pass_count",
    "world_class_source_blocked_count",
    "beta_test_ready",
    "beta_test_blocker_count",
    "beta_test_deferred_evidence_count",
    "public_claim_ready",
    "public_claim_blocker_count",
]
ADOPTION_SUMMARY_KEYS = [
    "event_count",
    "adoption_sample_count",
    "activation_count",
    "accepted_count",
    "adoption_rate",
    "risk_band",
    "event_types",
    "source_types",
]
LEDGER_SUMMARY_KEYS = [
    "ledger_entry_count",
    "accepted_count",
    "pending_count",
    "human_pending_count",
    "external_pending_count",
    "source_check_count",
    "source_pass_count",
    "source_blocked_count",
    "ready_to_claim_world_class",
    "decision",
]
LOCKSTEP_SECTIONS = [
    "scorecard",
    "capability_profile",
    "principle_model",
    "contract_boundary",
    "quality_review",
    "risk_governance",
    "world_class_readiness",
    "package_assets",
    "iteration_roadmap",
]


def load_json(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return {}, "missing"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, f"invalid-json: {exc}"
    if not isinstance(payload, dict):
        return {}, "json-root-not-object"
    return payload, None


def load_text(path: Path) -> tuple[str, str | None]:
    if not path.exists():
        return "", "missing"
    return path.read_text(encoding="utf-8"), None


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def nested(payload: dict[str, Any], path: list[str], default: Any = None) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]
    return current


def scanned_surface_paths(payload: dict[str, Any]) -> set[str]:
    surfaces = payload.get("scanned_surfaces")
    if not isinstance(surfaces, list):
        return set()
    paths: set[str] = set()
    for item in surfaces:
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            paths.add(item["path"])
        elif isinstance(item, str):
            paths.add(item)
    return paths


def as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def add_check(
    checks: list[dict[str, Any]],
    *,
    key: str,
    label: str,
    status: str,
    expected: Any,
    actual: Any,
    paths: list[str],
    detail: str,
) -> None:
    checks.append(
        {
            "key": key,
            "label": label,
            "status": status,
            "expected": expected,
            "actual": actual,
            "paths": paths,
            "detail": detail,
        }
    )


def compare_values(
    checks: list[dict[str, Any]],
    *,
    key: str,
    label: str,
    expected: Any,
    actual: Any,
    paths: list[str],
    detail: str,
) -> None:
    add_check(
        checks,
        key=key,
        label=label,
        status="pass" if expected == actual else "fail",
        expected=expected,
        actual=actual,
        paths=paths,
        detail=detail,
    )


def compare_summary_keys(
    checks: list[dict[str, Any]],
    *,
    key_prefix: str,
    label: str,
    source_summary: dict[str, Any],
    embedded_summary: dict[str, Any],
    keys: list[str],
    paths: list[str],
) -> None:
    expected = {key: source_summary.get(key) for key in keys}
    actual = {key: embedded_summary.get(key) for key in keys}
    compare_values(
        checks,
        key=key_prefix,
        label=label,
        expected=expected,
        actual=actual,
        paths=paths,
        detail="Selected summary fields must match exactly across generated reports.",
    )


def gate_by_key(review_studio: dict[str, Any], key: str) -> dict[str, Any]:
    gates = review_studio.get("gates")
    if not isinstance(gates, list):
        return {}
    for item in gates:
        if isinstance(item, dict) and item.get("key") == key:
            return item
    return {}


def beta_public_claim_split_values(
    benchmark: dict[str, Any],
    ledger: dict[str, Any],
    review_studio: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    benchmark_summary = nested(benchmark, ["summary"], {})
    ledger_summary = nested(ledger, ["summary"], {})
    expected_beta_ready = (
        bool(benchmark_summary.get("reproducibility_ready"))
        and bool(benchmark_summary.get("release_lock_ready"))
        and bool(benchmark_summary.get("provider_evidence_complete"))
    )
    output_review_summary = nested(review_studio, ["data", "output_review_adjudication", "summary"], {})
    review_pair_count = as_int(output_review_summary.get("pair_count")) if isinstance(output_review_summary, dict) else None
    review_pending_count = as_int(output_review_summary.get("pending_count")) if isinstance(output_review_summary, dict) else None
    expected_human_review_complete = (
        review_pair_count is not None and review_pair_count > 0 and review_pending_count == 0
    )
    ledger_entries = ledger.get("entries", []) if isinstance(ledger, dict) else []
    pending_ledger_keys = sorted(
        str(entry.get("key", ""))
        for entry in ledger_entries
        if isinstance(entry, dict) and entry.get("status") == "pending" and str(entry.get("key", ""))
    )
    beta_boundary = {
        "beta_test_ready": expected_beta_ready,
        "public_claim_ready": ledger_summary.get("ready_to_claim_world_class"),
        "human_review_complete": expected_human_review_complete,
        "beta_release_ready": expected_beta_ready,
        "beta_release_scope": "beta/public test release without superiority, fully-reviewed, or world-class claims",
        "deferred_evidence_keys": pending_ledger_keys,
        "deferred_human_review": "human-adjudication" in pending_ledger_keys,
    }
    beta_release = benchmark.get("beta_test_release", {}) if isinstance(benchmark, dict) else {}
    deferred_keys = sorted(
        str(item.get("key", ""))
        for item in beta_release.get("allowed_deferred_evidence", [])
        if isinstance(item, dict) and str(item.get("key", ""))
    )
    actual_beta_boundary = {
        "beta_test_ready": benchmark_summary.get("beta_test_ready") if isinstance(benchmark_summary, dict) else None,
        "public_claim_ready": benchmark_summary.get("public_claim_ready") if isinstance(benchmark_summary, dict) else None,
        "human_review_complete": benchmark_summary.get("human_review_complete")
        if isinstance(benchmark_summary, dict)
        else None,
        "beta_release_ready": beta_release.get("ready") if isinstance(beta_release, dict) else None,
        "beta_release_scope": beta_release.get("scope") if isinstance(beta_release, dict) else None,
        "deferred_evidence_keys": deferred_keys,
        "deferred_human_review": "human-adjudication" in deferred_keys,
    }
    return beta_boundary, actual_beta_boundary


def report_contract(payload: dict[str, Any]) -> dict[str, Any]:
    contract = payload.get("report_contract")
    return contract if isinstance(contract, dict) else {}


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Evidence Consistency",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- checks: `{summary['check_count']}`",
        f"- pass: `{summary['pass_count']}`",
        f"- warn: `{summary['warn_count']}`",
        f"- fail: `{summary['fail_count']}`",
        "",
        "This gate compares generated evidence reports against each other. It does not create provider, human, native-client, or permission-enforcement evidence; it only catches drift between reports that already exist.",
        "",
        "## Checks",
        "",
        "| Check | Status | Detail | Paths |",
        "| --- | --- | --- | --- |",
    ]
    for check in report["checks"]:
        paths = ", ".join(f"`{path}`" for path in check["paths"])
        lines.append(
            "| "
            + " | ".join(
                [
                    check["label"].replace("|", "\\|"),
                    f"`{check['status']}`",
                    check["detail"].replace("|", "\\|"),
                    paths.replace("|", "\\|"),
                ]
            )
            + " |"
        )
    failures = [check for check in report["checks"] if check["status"] == "fail"]
    if failures:
        lines.extend(["", "## Failures", ""])
        for check in failures:
            lines.extend(
                [
                    f"### {check['label']}",
                    "",
                    f"- key: `{check['key']}`",
                    f"- expected: `{json.dumps(check['expected'], ensure_ascii=False, sort_keys=True)}`",
                    f"- actual: `{json.dumps(check['actual'], ensure_ascii=False, sort_keys=True)}`",
                    "",
                ]
            )
    return "\n".join(lines).rstrip() + "\n"
