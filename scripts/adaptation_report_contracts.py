"""Shared report contracts for approval-gated skill adaptation."""

from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Shared adaptation approval and regression report contract decoration helpers."

APPROVAL_SUMMARY_FIELDS = [
    "approval_count",
    "active_approval_count",
    "pending_review_count",
    "applied_count",
    "rollback_count",
]
APPROVAL_CONTRACT_FIELDS = [
    "approval_required",
    "patch_sha256_required",
    "allowlisted_targets_required",
    "target_file_sha256_required",
    "approval_draft_supported",
    "dry_run_default",
    "writes_repository_files_only_with_apply",
    "rollback_required",
]
REGRESSION_SUMMARY_FIELDS = [
    "apply_supported",
    "attempt_count",
    "approval_draft_count",
    "applied_count",
    "dry_run_count",
    "rollback_count",
    "regression_run_count",
    "regression_pass_count",
    "failure_count",
]
APPLY_CONTRACT_FIELDS = [
    *APPROVAL_CONTRACT_FIELDS,
    "safe_regression_commands_only",
    "rollback_on_failure_default",
]
APPROVAL_CONTRACT = {
    "approval_required": True,
    "patch_sha256_required": True,
    "allowlisted_targets_required": True,
    "target_file_sha256_required": True,
    "approval_draft_supported": True,
    "dry_run_default": True,
    "writes_repository_files_only_with_apply": True,
    "rollback_required": True,
}
APPLY_CONTRACT = {
    **APPROVAL_CONTRACT,
    "safe_regression_commands_only": True,
    "rollback_on_failure_default": True,
}


def top_level_mirrors(
    summary: dict[str, Any],
    contract: dict[str, Any],
    summary_fields: list[str],
    contract_fields: list[str],
) -> dict[str, Any]:
    mirrored = {key: summary[key] for key in summary_fields if key in summary}
    mirrored.update({key: contract[key] for key in contract_fields if key in contract})
    return mirrored


def report_contract(name: str, contract_key: str, summary_fields: list[str], contract_fields: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "contract": name,
        "top_level_mirrors_summary": True,
        f"top_level_mirrors_{contract_key}": True,
        "summary_fields": summary_fields,
        f"{contract_key}_fields": contract_fields,
        "source_of_truth": ["summary", contract_key],
    }


def decorate_approval_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    summary = ledger.get("summary", {}) if isinstance(ledger.get("summary"), dict) else {}
    approval_contract = (
        ledger.get("approval_contract", {}) if isinstance(ledger.get("approval_contract"), dict) else {}
    ) or dict(APPROVAL_CONTRACT)
    ledger.update(top_level_mirrors(summary, approval_contract, APPROVAL_SUMMARY_FIELDS, APPROVAL_CONTRACT_FIELDS))
    ledger["approval_contract"] = approval_contract
    ledger["report_contract"] = report_contract(
        "adaptation-approval-ledger",
        "approval_contract",
        APPROVAL_SUMMARY_FIELDS,
        APPROVAL_CONTRACT_FIELDS,
    )
    return ledger


def decorate_regression_report(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    apply_contract = (
        report.get("apply_contract", {}) if isinstance(report.get("apply_contract"), dict) else {}
    ) or dict(APPLY_CONTRACT)
    report.update(top_level_mirrors(summary, apply_contract, REGRESSION_SUMMARY_FIELDS, APPLY_CONTRACT_FIELDS))
    report["apply_contract"] = apply_contract
    report["report_contract"] = report_contract(
        "adaptation-regression-report",
        "apply_contract",
        REGRESSION_SUMMARY_FIELDS,
        APPLY_CONTRACT_FIELDS,
    )
    return report
