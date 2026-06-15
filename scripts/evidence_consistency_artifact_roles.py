#!/usr/bin/env python3
"""Compare artifact-role handoffs across world-class evidence reports."""

from pathlib import Path
from typing import Any


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_evidence_consistency.py to compare preflight and Review Studio artifact-role contracts."


def _compare_check(
    *,
    key: str,
    label: str,
    expected: Any,
    actual: Any,
    paths: list[str],
    detail: str,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "status": "pass" if expected == actual else "fail",
        "expected": expected,
        "actual": actual,
        "paths": paths,
        "detail": detail,
    }


def role_contract_signature(contract: dict[str, Any]) -> dict[str, Any]:
    roles = {
        str(item.get("role", "")): item
        for item in contract.get("roles", [])
        if isinstance(item, dict) and str(item.get("role", "")).strip()
    }
    return {
        "role_source": contract.get("role_source"),
        "counts_as_evidence": contract.get("counts_as_evidence"),
        "artifact_prefill_counts_as_evidence": contract.get("artifact_prefill_counts_as_evidence"),
        "submission_ref_total_count": contract.get("submission_ref_total_count"),
        "submission_ref_ready_count": contract.get("submission_ref_ready_count"),
        "supporting_evidence_total_count": contract.get("supporting_evidence_total_count"),
        "supporting_evidence_ready_count": contract.get("supporting_evidence_ready_count"),
        "submission_ref_copy_to_artifact_refs": roles.get("submission-ref", {}).get("copy_to_artifact_refs"),
        "supporting_evidence_copy_to_artifact_refs": roles.get("supporting-evidence", {}).get(
            "copy_to_artifact_refs"
        ),
    }


def preflight_role_signatures(world_class_preflight: dict[str, Any]) -> dict[str, dict[str, Any]]:
    signatures: dict[str, dict[str, Any]] = {}
    items = world_class_preflight.get("items", []) if isinstance(world_class_preflight, dict) else []
    for item in items:
        if not isinstance(item, dict):
            continue
        key = str(item.get("evidence_key", "")).strip()
        submission_kit = item.get("submission_kit", {}) if isinstance(item.get("submission_kit", {}), dict) else {}
        contract = (
            submission_kit.get("artifact_role_contract", {})
            if isinstance(submission_kit.get("artifact_role_contract", {}), dict)
            else {}
        )
        if key and contract:
            signatures[key] = role_contract_signature(contract)
    return signatures


def review_studio_role_signatures(review_studio: dict[str, Any]) -> dict[str, dict[str, Any]]:
    actions = review_studio.get("review_actions", []) if isinstance(review_studio, dict) else []
    for action in actions:
        if not isinstance(action, dict) or action.get("gate_key") != "world-class-evidence":
            continue
        signatures: dict[str, dict[str, Any]] = {}
        for step in action.get("evidence_steps", []):
            if not isinstance(step, dict):
                continue
            key = str(step.get("key", "")).strip()
            contract = (
                step.get("artifact_role_contract", {})
                if isinstance(step.get("artifact_role_contract", {}), dict)
                else {}
            )
            if key and contract:
                signatures[key] = role_contract_signature(contract)
        return signatures
    return {}


def build_preflight_artifact_role_handoff_checks(
    *,
    skill_dir: Path,
    world_class_preflight: dict[str, Any],
    review_studio: dict[str, Any],
    report_paths: dict[str, str],
) -> list[dict[str, Any]]:
    preflight_submissions = (
        world_class_preflight.get("submissions", {})
        if isinstance(world_class_preflight.get("submissions", {}), dict)
        else {}
    )
    preflight_commands = (
        preflight_submissions.get("commands", {})
        if isinstance(preflight_submissions.get("commands", {}), dict)
        else {}
    )
    preflight_role_contract = (
        preflight_submissions.get("artifact_role_contract", {})
        if isinstance(preflight_submissions.get("artifact_role_contract", {}), dict)
        else {}
    )
    preflight_roles = {
        str(item.get("role", "")): item for item in preflight_role_contract.get("roles", []) if isinstance(item, dict)
    }
    default_submissions_dir = "evidence/world_class/submissions"
    expected_preflight_handoff = {
        "directory": default_submissions_dir,
        "drafts_count_as_evidence": False,
        "preflight_counts_submission_as_completion": False,
        "html_report": "reports/world_class_evidence_preflight.html",
        "html_exists": True,
        "prepare_submission": f"python3 scripts/yao.py world-class-submission-kit . --output-dir {default_submissions_dir}",
        "prepare_prefilled_submission": (
            f"python3 scripts/yao.py world-class-submission-kit . --output-dir {default_submissions_dir} "
            "--prefill-artifacts"
        ),
        "validate_intake": f"python3 scripts/yao.py world-class-intake . --submissions-dir {default_submissions_dir}",
        "submission_review": f"python3 scripts/yao.py world-class-submission-review . --submissions-dir {default_submissions_dir}",
        "refresh_ledger": f"python3 scripts/yao.py world-class-ledger . --submissions-dir {default_submissions_dir}",
        "guard_claim": "python3 scripts/yao.py world-class-claim-guard .",
        "artifact_prefill_counts_as_evidence": False,
        "artifact_role_source": "world-class-submission-kit",
        "artifact_role_counts_as_evidence": False,
        "artifact_role_prefill_counts_as_evidence": False,
        "submission_ref_role_present": True,
        "supporting_evidence_role_present": True,
        "submission_ref_copy_to_artifact_refs": True,
        "supporting_evidence_copy_to_artifact_refs": False,
        "submission_ref_total_present": True,
        "supporting_evidence_total_present": True,
    }
    actual_preflight_handoff = {
        "directory": preflight_submissions.get("directory"),
        "drafts_count_as_evidence": preflight_submissions.get("drafts_count_as_evidence"),
        "preflight_counts_submission_as_completion": preflight_submissions.get(
            "preflight_counts_submission_as_completion"
        ),
        "html_report": world_class_preflight.get("artifacts", {}).get("html")
        if isinstance(world_class_preflight.get("artifacts", {}), dict)
        else None,
        "html_exists": (skill_dir / "reports" / "world_class_evidence_preflight.html").exists(),
        "prepare_submission": preflight_commands.get("prepare_submission"),
        "prepare_prefilled_submission": preflight_commands.get("prepare_prefilled_submission"),
        "validate_intake": preflight_commands.get("validate_intake"),
        "submission_review": preflight_commands.get("submission_review"),
        "refresh_ledger": preflight_commands.get("refresh_ledger"),
        "guard_claim": preflight_commands.get("guard_claim"),
        "artifact_prefill_counts_as_evidence": preflight_submissions.get("artifact_prefill_counts_as_evidence"),
        "artifact_role_source": preflight_role_contract.get("role_source"),
        "artifact_role_counts_as_evidence": preflight_role_contract.get("counts_as_evidence"),
        "artifact_role_prefill_counts_as_evidence": preflight_role_contract.get(
            "artifact_prefill_counts_as_evidence"
        ),
        "submission_ref_role_present": "submission-ref" in preflight_roles,
        "supporting_evidence_role_present": "supporting-evidence" in preflight_roles,
        "submission_ref_copy_to_artifact_refs": preflight_roles.get("submission-ref", {}).get(
            "copy_to_artifact_refs"
        ),
        "supporting_evidence_copy_to_artifact_refs": preflight_roles.get("supporting-evidence", {}).get(
            "copy_to_artifact_refs"
        ),
        "submission_ref_total_present": int(preflight_role_contract.get("submission_ref_total_count", 0)) > 0,
        "supporting_evidence_total_present": int(preflight_role_contract.get("supporting_evidence_total_count", 0))
        > 0,
    }
    return [
        _compare_check(
            key="preflight-submission-kit-handoff",
            label="Preflight exposes a safe submission-kit handoff",
            expected=expected_preflight_handoff,
            actual=actual_preflight_handoff,
            paths=[report_paths["world_class_preflight"], "reports/world_class_evidence_preflight.html"],
            detail=(
                "Preflight must give operators the exact draft, SHA-prefill, intake, review, ledger, "
                "and claim-guard commands without letting drafts, prefill, or submissions count as accepted evidence."
            ),
        ),
        _compare_check(
            key="review-studio-preflight-artifact-role-handoff",
            label="Review Studio mirrors preflight artifact roles",
            expected=preflight_role_signatures(world_class_preflight),
            actual=review_studio_role_signatures(review_studio),
            paths=[report_paths["world_class_preflight"], report_paths["review_studio"]],
            detail=(
                "The Review Studio world-class action card must carry the same submission-ref versus "
                "supporting-evidence contract as the preflight handoff."
            ),
        ),
    ]
