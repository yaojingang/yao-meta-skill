"""Helper functions for Review Studio gate evaluation."""

import json
import os
from pathlib import Path
from typing import Any

try:
    from trust_check import permission_governance_status as compute_permission_governance_status
    from trust_check import script_inventory as trust_script_inventory
except ImportError:  # pragma: no cover
    compute_permission_governance_status = None
    trust_script_inventory = None

from review_studio_gate_contract import min_output_cases


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by review_studio_gates.py to keep reusable Review Studio gate helpers out of the main gate sequence."


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def link_from(output_html: Path, target: Path) -> str:
    return os.path.relpath(target.resolve(), output_html.parent.resolve())


def report_link(output_html: Path, skill_dir: Path, rel_path: str) -> str:
    return link_from(output_html, skill_dir / rel_path)


def gate(key: str, label: str, status: str, detail: str, evidence: str, link: str = "") -> dict[str, str]:
    return {
        "key": key,
        "label": label,
        "status": status,
        "detail": detail,
        "evidence": evidence,
        "link": link,
    }


def target_maturity(skill_dir: Path, overview: dict[str, Any]) -> str:
    manifest = load_json(skill_dir / "manifest.json")
    if manifest.get("maturity_tier"):
        return str(manifest["maturity_tier"])
    metadata = overview.get("metadata", {}) if isinstance(overview, dict) else {}
    if metadata.get("maturity_tier"):
        return str(metadata["maturity_tier"])
    return "scaffold"


def fallback_permission_governance(skill_dir: Path) -> dict[str, Any]:
    if compute_permission_governance_status is None or trust_script_inventory is None:
        return {}
    try:
        scripts = trust_script_inventory(skill_dir)
        return compute_permission_governance_status(skill_dir, scripts)
    except Exception:
        return {}


def build_output_lab_gate(
    skill_dir: Path,
    output_html: Path,
    maturity: str,
    output: dict[str, Any],
    output_execution: dict[str, Any],
    output_blind: dict[str, Any],
    output_review: dict[str, Any],
) -> dict[str, str]:
    output_summary = output.get("summary", {})
    output_execution_summary = output_execution.get("summary", {})
    output_blind_summary = output_blind.get("summary", {})
    output_review_summary = output_review.get("summary", {})
    required_cases = min_output_cases(maturity)
    case_count = int(output_summary.get("case_count", 0) or 0)
    file_backed = int(output_summary.get("file_backed_case_count", 0) or 0)
    near_neighbor = int(output_summary.get("near_neighbor_case_count", 0) or 0)
    boundary = int(output_summary.get("boundary_case_count", 0) or 0)
    blind_pair_count = int(output_blind_summary.get("pair_count", 0) or 0)
    execution_variant_count = int(output_execution_summary.get("variant_run_count", 0) or 0)
    execution_command_count = int(output_execution_summary.get("command_executed_count", 0) or 0)
    execution_model_count = int(output_execution_summary.get("model_executed_count", 0) or 0)
    execution_recorded_count = int(output_execution_summary.get("recorded_fixture_count", 0) or 0)
    review_pair_count = int(output_review_summary.get("pair_count", 0) or 0)
    review_judgment_count = int(output_review_summary.get("judgment_count", 0) or 0)
    review_pending_count = int(output_review_summary.get("pending_count", 0) or 0)
    review_invalid_count = int(output_review_summary.get("invalid_decision_count", 0) or 0)
    production_like = maturity in {"production", "library", "governed"}
    blind_missing = production_like and (not output_blind or blind_pair_count < case_count)
    review_missing = production_like and case_count > 0 and not output_review
    review_pending = production_like and bool(output_review) and review_pending_count > 0
    execution_failed = bool(output_execution) and (
        not output_execution.get("ok", True) or int(output_execution_summary.get("failure_count", 0) or 0) > 0
    )
    review_invalid = bool(output_review) and (not output_review.get("ok", True) or review_invalid_count > 0)
    output_blocked = (
        not output.get("ok", False)
        or not output_summary.get("gate_pass", False)
        or case_count < required_cases
        or execution_failed
        or review_invalid
    )
    output_warn = file_backed == 0 or near_neighbor == 0 or boundary == 0 or blind_missing or review_missing or review_pending
    if not output:
        output_status = "warn"
        output_detail = "output eval scorecard is missing; generate it before production review"
    else:
        output_status = "block" if output_blocked else ("warn" if output_warn else "pass")
        output_detail = (
            f"{case_count}/{required_cases} cases; with-skill {output_summary.get('with_skill_pass_rate', 0)}; "
            f"baseline {output_summary.get('baseline_pass_rate', 0)}; file-backed {file_backed}; near-neighbor {near_neighbor}; "
            f"blind A/B {blind_pair_count}"
            + (
                f"; exec {execution_variant_count}; command {execution_command_count}; "
                f"model {execution_model_count}; recorded {execution_recorded_count}"
                if output_execution
                else ""
            )
            + (f"; reviewed {review_judgment_count}/{review_pair_count}" if output_review else "")
            + (f"; review pending {review_pending_count}" if review_pending else "")
            + ("; review adjudication missing" if review_missing else "")
        )
    return gate(
        "output-lab",
        "输出实验",
        output_status,
        output_detail,
        "reports/output_quality_scorecard.json",
        report_link(output_html, skill_dir, "reports/output_quality_scorecard.md"),
    )
