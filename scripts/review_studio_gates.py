#!/usr/bin/env python3
"""Gate evaluation contract for Review Studio 2.0."""

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


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_review_studio.py to keep Review Studio gate evaluation separate from HTML rendering."


ROOT = Path(__file__).resolve().parent.parent


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _link_from(output_html: Path, target: Path) -> str:
    return os.path.relpath(target.resolve(), output_html.parent.resolve())


def _report_link(output_html: Path, skill_dir: Path, rel_path: str) -> str:
    return _link_from(output_html, skill_dir / rel_path)


def gate(key: str, label: str, status: str, detail: str, evidence: str, link: str = "") -> dict[str, str]:
    return {
        "key": key,
        "label": label,
        "status": status,
        "detail": detail,
        "evidence": evidence,
        "link": link,
    }


def status_label(status: str) -> str:
    return {"pass": "通过", "warn": "关注", "block": "阻断"}.get(status, status)


def add_blockers_from_gate(gates: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    blockers = [item for item in gates if item["status"] == "block"]
    warnings = [item for item in gates if item["status"] == "warn"]
    return blockers, warnings


def target_maturity(skill_dir: Path, overview: dict[str, Any]) -> str:
    manifest = _load_json(skill_dir / "manifest.json")
    if manifest.get("maturity_tier"):
        return str(manifest["maturity_tier"])
    metadata = overview.get("metadata", {}) if isinstance(overview, dict) else {}
    if metadata.get("maturity_tier"):
        return str(metadata["maturity_tier"])
    return "scaffold"


def min_output_cases(maturity: str) -> int:
    if maturity in {"library", "governed"}:
        return 5
    if maturity == "production":
        return 3
    return 1


def fallback_permission_governance(skill_dir: Path) -> dict[str, Any]:
    if compute_permission_governance_status is None or trust_script_inventory is None:
        return {}
    try:
        scripts = trust_script_inventory(skill_dir)
        return compute_permission_governance_status(skill_dir, scripts)
    except Exception:
        return {}


def build_gates(skill_dir: Path, output_html: Path, data: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    overview = data["overview"]
    maturity = target_maturity(skill_dir, overview)
    gates: list[dict[str, str]] = []

    intent = data["intent_confidence"]
    intent_score = int(intent.get("score", 0) or 0)
    intent_status = "pass" if intent.get("gate_passed") or intent_score >= 75 else "warn"
    gates.append(
        gate(
            "intent-canvas",
            "意图画布",
            intent_status,
            f"intent confidence {intent_score}/100; {intent.get('recommended_action', 'review current intent frame')}",
            "reports/intent-confidence.json",
            _report_link(output_html, skill_dir, "reports/intent-confidence.md"),
        )
    )

    route = data["route_scorecard"]
    route_summary = route.get("summary", {})
    misroutes = int(route_summary.get("misroute_count", len(route.get("misroutes", []))) or 0)
    ambiguous = int(route_summary.get("ambiguous_case_count", len(route.get("ambiguous_cases", []))) or 0)
    if not route:
        route_status = "warn"
        route_detail = "route scorecard is missing; run route-scorecard before release review"
    else:
        route_status = "block" if misroutes else ("warn" if ambiguous else "pass")
        route_detail = f"{route_summary.get('total_cases', 0)} trigger cases; {misroutes} misroutes; {ambiguous} ambiguous"
    gates.append(
        gate(
            "trigger-lab",
            "触发实验",
            route_status,
            route_detail,
            "reports/route_scorecard.json",
            _report_link(output_html, skill_dir, "reports/route_scorecard.md"),
        )
    )

    output = data["output_quality"]
    output_execution = data["output_execution"]
    output_blind = data["output_blind_review"]
    output_review = data["output_review_adjudication"]
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
    blind_missing = maturity in {"production", "library", "governed"} and (not output_blind or blind_pair_count < case_count)
    review_missing = maturity in {"production", "library", "governed"} and case_count > 0 and not output_review
    review_pending = maturity in {"production", "library", "governed"} and bool(output_review) and review_pending_count > 0
    execution_failed = bool(output_execution) and (not output_execution.get("ok", True) or int(output_execution_summary.get("failure_count", 0) or 0) > 0)
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
    gates.append(
        gate(
            "output-lab",
            "输出实验",
            output_status,
            output_detail,
            "reports/output_quality_scorecard.json",
            _report_link(output_html, skill_dir, "reports/output_quality_scorecard.md"),
        )
    )

    context = data["context_budget"]
    context_stats = context.get("stats", {})
    context_status = "pass" if context.get("ok") else "block"
    if context.get("warnings"):
        context_status = "warn" if context_status == "pass" else context_status
    if not context:
        context_status = "warn"
    context_detail = (
        f"initial load {context_stats.get('estimated_initial_load_tokens', 'n/a')}/"
        f"{context_stats.get('context_budget_limit', 'n/a')}; quality density {context_stats.get('quality_density', 'n/a')}"
    )
    gates.append(
        gate(
            "context-budget",
            "上下文",
            context_status,
            context_detail,
            "reports/context_budget.json",
            _report_link(output_html, skill_dir, "reports/context_budget.md"),
        )
    )

    conformance = data["conformance"]
    conformance_summary = conformance.get("summary", {})
    fail_count = int(conformance_summary.get("fail_count", 0) or 0)
    if not conformance:
        conformance_status = "warn"
        conformance_detail = "runtime conformance matrix is missing"
    else:
        conformance_status = "block" if fail_count else "pass"
        conformance_detail = f"{conformance_summary.get('pass_count', 0)} / {conformance_summary.get('target_count', 0)} targets pass"
    gates.append(
        gate(
            "runtime-matrix",
            "运行矩阵",
            conformance_status,
            conformance_detail,
            "reports/conformance_matrix.json",
            _report_link(output_html, skill_dir, "reports/conformance_matrix.md"),
        )
    )

    trust = data["trust"]
    trust_summary = trust.get("summary", {})
    if not trust:
        trust_status = "warn"
        trust_detail = "security trust report is missing"
    else:
        trust_status = "block" if trust.get("failures") else ("warn" if trust.get("warnings") else "pass")
        trust_detail = (
            f"{trust_summary.get('secret_findings', 0)} secrets; "
            f"{trust_summary.get('script_count', 0)} scripts; "
            f"{trust_summary.get('network_script_count', 0)} network-capable scripts; "
            f"{trust_summary.get('help_smoke_failed_count', 0)} help smoke failures"
        )
    gates.append(
        gate(
            "trust-report",
            "信任报告",
            trust_status,
            trust_detail,
            "reports/security_trust_report.json",
            _report_link(output_html, skill_dir, "reports/security_trust_report.md"),
        )
    )

    permission_governance = trust.get("permission_governance", {}) if isinstance(trust.get("permission_governance", {}), dict) else {}
    if trust and not permission_governance:
        permission_governance = fallback_permission_governance(skill_dir)
    if not trust:
        permission_status = "warn"
        permission_detail = "permission governance evidence is missing because trust report is missing"
    elif not permission_governance:
        permission_status = "warn"
        permission_detail = "permission governance evidence is missing from trust report"
    else:
        required = int(permission_governance.get("required_count", 0) or 0)
        approved = int(permission_governance.get("approval_count", 0) or 0)
        gaps = (
            int(permission_governance.get("missing_count", 0) or 0)
            + int(permission_governance.get("invalid_count", 0) or 0)
            + int(permission_governance.get("expired_count", 0) or 0)
        )
        if gaps:
            permission_status = "block" if maturity == "governed" else "warn"
        else:
            permission_status = "pass"
        required_names = ", ".join(permission_governance.get("required_capabilities", []) or []) or "none"
        permission_detail = f"{approved}/{required} permissions approved; gaps {gaps}; required {required_names}"
    gates.append(
        gate(
            "permission-gates",
            "权限批准",
            permission_status,
            permission_detail,
            "reports/security_trust_report.json + security/permission_policy.json",
            _report_link(output_html, skill_dir, "security/permission_policy.md"),
        )
    )

    runtime_permissions = data["runtime_permissions"]
    runtime_permissions_summary = runtime_permissions.get("summary", {})
    if not runtime_permissions:
        runtime_permission_status = "block" if maturity == "governed" else "warn"
        runtime_permission_detail = "runtime permission probe report is missing"
    elif runtime_permissions.get("failures"):
        runtime_permission_status = "block"
        runtime_permission_detail = f"{runtime_permissions_summary.get('failure_count', len(runtime_permissions.get('failures', [])))} runtime permission probe failures"
    else:
        runtime_permission_status = "pass"
        runtime_permission_detail = (
            f"{runtime_permissions_summary.get('pass_count', 0)}/{runtime_permissions_summary.get('target_count', 0)} targets probed; "
            f"native {runtime_permissions_summary.get('native_enforcement_count', 0)}; "
            f"metadata fallback {runtime_permissions_summary.get('metadata_fallback_count', 0)}; "
            f"residual risks {runtime_permissions_summary.get('residual_risk_count', 0)}"
        )
    gates.append(
        gate(
            "permission-runtime",
            "权限探针",
            runtime_permission_status,
            runtime_permission_detail,
            "reports/runtime_permission_probes.json",
            _report_link(output_html, skill_dir, "reports/runtime_permission_probes.md"),
        )
    )

    atlas = data["atlas"]
    atlas_summary = atlas.get("summary", {})
    actionable_route_collisions = int(
        atlas_summary.get("actionable_route_collision_count", atlas_summary.get("route_collision_count", 0)) or 0
    )
    actionable_owner_gaps = int(atlas_summary.get("actionable_owner_gap_count", atlas_summary.get("owner_gap_count", 0)) or 0)
    actionable_stale = int(atlas_summary.get("actionable_stale_count", atlas_summary.get("stale_count", 0)) or 0)
    actionable_drift = int(atlas_summary.get("actionable_drift_signal_count", atlas_summary.get("drift_signal_count", 0)) or 0)
    atlas_issues = actionable_route_collisions + actionable_owner_gaps + actionable_stale + actionable_drift
    if not atlas:
        atlas_status = "warn"
        atlas_detail = "skill atlas is missing; portfolio-level conflicts are unknown"
    else:
        atlas_status = "warn" if atlas_issues else "pass"
        atlas_detail = (
            f"{atlas_summary.get('skill_count', 0)} skills, "
            f"{atlas_summary.get('actionable_skill_count', atlas_summary.get('skill_count', 0))} actionable; "
            f"{actionable_route_collisions} actionable route collisions; "
            f"{actionable_owner_gaps} actionable owner gaps; "
            f"{actionable_stale} actionable stale; "
            f"{actionable_drift} actionable drift; "
            f"{atlas_summary.get('non_actionable_issue_count', 0)} scoped non-actionable issues"
        )
    gates.append(
        gate(
            "skill-atlas",
            "组合治理",
            atlas_status,
            atlas_detail,
            "reports/skill_atlas.json",
            _report_link(output_html, skill_dir, "reports/skill_atlas.html"),
        )
    )

    adoption = data["adoption_drift"]
    adoption_summary = adoption.get("summary", {})
    if not adoption:
        adoption_status = "warn"
        adoption_detail = "adoption drift report is missing; real usage impact is unknown"
    elif adoption.get("failures"):
        adoption_status = "block"
        adoption_detail = f"telemetry privacy or schema failures: {len(adoption.get('failures', []))}"
    else:
        risk_band = adoption_summary.get("risk_band", "no-data")
        adoption_status = "warn" if risk_band in {"no-data", "medium", "high"} else "pass"
        adoption_detail = (
            f"{adoption_summary.get('event_count', 0)} metadata events; "
            f"adoption {adoption_summary.get('adoption_rate', 0)}; "
            f"missed {adoption_summary.get('missed_trigger_count', 0)}; "
            f"bad-output {adoption_summary.get('bad_output_count', 0)}; "
            f"risk {risk_band}"
        )
    gates.append(
        gate(
            "operations-loop",
            "运营回路",
            adoption_status,
            adoption_detail,
            "reports/adoption_drift_report.json",
            _report_link(output_html, skill_dir, "reports/adoption_drift_report.md"),
        )
    )

    waiver = data["review_waivers"]
    waiver_summary = waiver.get("summary", {})
    active_covered = set(waiver_summary.get("covered_gate_keys", []) or [])
    prior_blockers = [item for item in gates if item["status"] == "block"]
    prior_warnings = [item for item in gates if item["status"] == "warn"]
    unwaived_warnings = [item for item in prior_warnings if item["key"] not in active_covered]
    if not waiver:
        waiver_status = "warn"
        waiver_detail = "review waiver ledger is missing; warning acceptance is not auditable"
    elif waiver.get("failures"):
        waiver_status = "block"
        waiver_detail = f"{len(waiver.get('failures', []))} invalid waiver records"
    elif prior_blockers:
        waiver_status = "block"
        waiver_detail = f"{len(prior_blockers)} blocker gates cannot be waived in v0"
    elif unwaived_warnings:
        waiver_status = "warn"
        waiver_detail = (
            f"{waiver_summary.get('active_count', 0)} active waivers; "
            f"{len(unwaived_warnings)} warning gates still need reviewer decision"
        )
    else:
        waiver_status = "pass"
        waiver_detail = f"{waiver_summary.get('active_count', 0)} active waivers cover current warnings"
    gates.append(
        gate(
            "review-waivers",
            "人工批准",
            waiver_status,
            waiver_detail,
            "reports/review_waivers.json",
            _report_link(output_html, skill_dir, "reports/review_waivers.md"),
        )
    )

    registry = data["registry"]
    install = data["install_simulation"]
    if not registry:
        if maturity in {"library", "governed"}:
            registry_status = "warn"
            registry_detail = "registry audit is missing; package metadata is not reviewable"
        else:
            registry_status = "pass"
            registry_detail = "registry audit is optional until team distribution is required"
    else:
        compatibility = registry.get("package", {}).get("compatibility", {})
        pass_count = sum(1 for status in compatibility.values() if status == "pass")
        registry_status = "block" if registry.get("failures") else ("warn" if registry.get("warnings") else "pass")
        registry_detail = (
            f"{registry.get('package', {}).get('name', 'package')} "
            f"{registry.get('package', {}).get('version', 'n/a')}; "
            f"{pass_count}/{len(compatibility)} compatibility entries pass"
        )
    if install:
        install_summary = install.get("summary", {})
        permission_failures = int(install_summary.get("installer_permission_failure_count", 0) or 0)
        if install.get("failures") or permission_failures:
            registry_status = "block"
        registry_detail += (
            f"; install {'pass' if install.get('ok') else 'fail'}"
            f" with {install_summary.get('adapter_count', 0)} adapters"
            f"; installer permissions {install_summary.get('installer_permission_enforced_count', 0)} enforced"
            f" / {permission_failures} failures"
        )
    gates.append(
        gate(
            "registry-audit",
            "注册审计",
            registry_status,
            registry_detail,
            "reports/registry_audit.json + reports/install_simulation.json",
            _report_link(output_html, skill_dir, "reports/registry_audit.md"),
        )
    )

    promotion = data["promotion"]
    migration_path = ROOT / "docs" / "migration-v2.md"
    if promotion:
        promotion_summary = promotion.get("summary", {})
        blocked = int(promotion_summary.get("blocked", 0) or 0)
        release_status = "block" if blocked else "pass"
        release_detail = f"{promotion_summary.get('promote', 0)} promote; {promotion_summary.get('keep_current', 0)} keep current; {blocked} blocked"
    else:
        release_status = "warn"
        release_detail = "promotion decisions are missing; release notes need reviewer confirmation"
    upgrade = data["upgrade_check"]
    if upgrade:
        upgrade_summary = upgrade.get("summary", {})
        if upgrade.get("failures"):
            release_status = "block"
        elif upgrade.get("warnings") and release_status == "pass":
            release_status = "warn"
        release_detail += (
            f"; upgrade {upgrade_summary.get('declared_bump', 'n/a')}"
            f" declared / {upgrade_summary.get('recommended_bump', 'n/a')} recommended"
        )
    gates.append(
        gate(
            "release-notes",
            "发布路线",
            release_status,
            release_detail,
            "reports/promotion_decisions.json + reports/upgrade_check.json + docs/migration-v2.md",
            _report_link(output_html, skill_dir, "reports/promotion_decisions.md") if promotion else str(migration_path),
        )
    )

    return gates


def weighted_score(gates: list[dict[str, str]]) -> int:
    weights = {
        "trigger-lab": 15,
        "output-lab": 20,
        "context-budget": 10,
        "runtime-matrix": 10,
        "trust-report": 10,
        "permission-gates": 10,
        "permission-runtime": 10,
        "skill-atlas": 10,
        "operations-loop": 10,
        "review-waivers": 10,
        "registry-audit": 10,
        "release-notes": 10,
        "intent-canvas": 10,
    }
    earned = 0.0
    total = 0.0
    for item in gates:
        weight = weights.get(item["key"], 5)
        total += weight
        if item["status"] == "pass":
            earned += weight
        elif item["status"] == "warn":
            earned += weight * 0.6
    return int(round(earned / total * 100)) if total else 0
