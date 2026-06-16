#!/usr/bin/env python3
"""Gate evaluation contract for Review Studio 2.0."""

from pathlib import Path
from typing import Any

from review_studio_gate_contract import (
    GATE_WEIGHTS,
    REVIEW_STUDIO_GATE_KEYS,
    add_blockers_from_gate,
    gate_contract,
    min_output_cases,
    status_label,
    weighted_score,
)
from review_studio_gate_helpers import (
    build_output_lab_gate,
    fallback_permission_governance,
    gate,
    report_link,
    target_maturity,
)


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_review_studio.py to keep Review Studio gate evaluation separate from HTML rendering."


ROOT = Path(__file__).resolve().parent.parent


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
            report_link(output_html, skill_dir, "reports/intent-confidence.md"),
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
            report_link(output_html, skill_dir, "reports/route_scorecard.md"),
        )
    )

    gates.append(
        build_output_lab_gate(
            skill_dir,
            output_html,
            maturity,
            data["output_quality"],
            data["output_execution"],
            data["output_blind_review"],
            data["output_review_adjudication"],
        )
    )

    context = data["context_budget"]
    context_stats = context.get("stats", {})
    context_status = "pass" if context.get("ok") else "block"
    if context.get("warnings"):
        context_status = "warn" if context_status == "pass" else context_status
    if not context:
        context_status = "warn"
    large_deferred_dirs = context_stats.get("large_deferred_resource_dirs", []) or []
    top_deferred = "none"
    if large_deferred_dirs:
        first = large_deferred_dirs[0]
        top_deferred = f"{first.get('path', 'resource')} {first.get('estimated_tokens', 'n/a')}"
    deferred_governance = context_stats.get("deferred_resource_governance", {}) if isinstance(context_stats, dict) else {}
    governance_status = deferred_governance.get("status", "unknown") if isinstance(deferred_governance, dict) else "unknown"
    context_detail = (
        f"initial load {context_stats.get('estimated_initial_load_tokens', 'n/a')}/"
        f"{context_stats.get('context_budget_limit', 'n/a')}; "
        f"deferred {context_stats.get('deferred_resource_tokens', 'n/a')}/"
        f"{context_stats.get('deferred_resource_warn_threshold', 'n/a')}; "
        f"top deferred {top_deferred}; "
        f"resource governance {governance_status}; "
        f"quality density {context_stats.get('quality_density', 'n/a')}"
    )
    gates.append(
        gate(
            "context-budget",
            "上下文",
            context_status,
            context_detail,
            "reports/context_budget.json",
            report_link(output_html, skill_dir, "reports/context_budget.md"),
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
            report_link(output_html, skill_dir, "reports/conformance_matrix.md"),
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
            report_link(output_html, skill_dir, "reports/security_trust_report.md"),
        )
    )

    python_compat = data["python_compatibility"]
    python_compat_summary = python_compat.get("summary", {})
    if not python_compat:
        python_compat_status = "warn"
        python_compat_detail = "Python compatibility report is missing"
    else:
        issue_count = int(python_compat_summary.get("issue_count", 0) or 0)
        syntax_error_count = int(python_compat_summary.get("syntax_error_count", 0) or 0)
        fstring_violation_count = int(python_compat_summary.get("fstring_311_violation_count", 0) or 0)
        python_compat_status = (
            "block"
            if not python_compat.get("ok", True) or issue_count or syntax_error_count or fstring_violation_count
            else "pass"
        )
        python_compat_detail = (
            f"Python {python_compat_summary.get('target_python', '3.11')}; "
            f"{python_compat_summary.get('file_count', 0)} files; "
            f"{issue_count} compatibility issues; "
            f"{syntax_error_count} syntax; "
            f"{fstring_violation_count} f-string 3.11 hazards"
        )
    gates.append(
        gate(
            "python-compat",
            "Python 兼容",
            python_compat_status,
            python_compat_detail,
            "reports/python_compatibility.json",
            report_link(output_html, skill_dir, "reports/python_compatibility.md"),
        )
    )

    architecture = data["architecture_maintainability"]
    architecture_summary = architecture.get("summary", {})
    if not architecture:
        if maturity in {"library", "governed"}:
            architecture_status = "warn"
            architecture_detail = "architecture maintainability report is missing for a reusable package"
        else:
            architecture_status = "pass"
            architecture_detail = "architecture maintainability report is optional until code surface grows"
    else:
        hotspot_count = int(architecture_summary.get("hotspot_count", 0) or 0)
        watchlist_count = int(architecture_summary.get("watchlist_count", 0) or 0)
        early_watchlist_count = int(architecture_summary.get("early_watchlist_count", 0) or 0)
        blocker_count = int(architecture_summary.get("blocker_count", 0) or 0)
        architecture_status = "block" if not architecture.get("ok", True) or blocker_count else ("warn" if hotspot_count else "pass")
        hotspot_label = "hotspot" if hotspot_count == 1 else "hotspots"
        watchlist_label = "watchlist file" if watchlist_count == 1 else "watchlist files"
        early_label = "early watch file" if early_watchlist_count == 1 else "early watch files"
        blocker_label = "blocker" if blocker_count == 1 else "blockers"
        architecture_detail = (
            f"{architecture_summary.get('python_file_count', 0)} Python files; "
            f"{hotspot_count} {hotspot_label}; "
            f"{watchlist_count} {watchlist_label}; "
            f"{early_watchlist_count} {early_label}; "
            f"{blocker_count} {blocker_label}; "
            f"largest {architecture_summary.get('largest_file_lines', 0)} lines; "
            f"{architecture_summary.get('command_handler_count', 0)} CLI handlers; "
            f"{architecture_summary.get('entrypoint_command_handler_count', 0)} in entrypoint"
        )
    gates.append(
        gate(
            "architecture-maintainability",
            "架构维护",
            architecture_status,
            architecture_detail,
            "reports/architecture_maintainability.json",
            report_link(output_html, skill_dir, "reports/architecture_maintainability.md"),
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
            report_link(output_html, skill_dir, "security/permission_policy.md"),
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
            f"installer {runtime_permissions_summary.get('installer_enforcement_pass_count', 0)}; "
            f"residual risks {runtime_permissions_summary.get('residual_risk_count', 0)}"
        )
    gates.append(
        gate(
            "permission-runtime",
            "权限探针",
            runtime_permission_status,
            runtime_permission_detail,
            "reports/runtime_permission_probes.json",
            report_link(output_html, skill_dir, "reports/runtime_permission_probes.md"),
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
            report_link(output_html, skill_dir, "reports/skill_atlas.html"),
        )
    )

    adoption = data["adoption_drift"]
    adoption_summary = adoption.get("summary", {})
    daily_skillops = data.get("daily_skillops", {})
    weekly_curator = data.get("weekly_curator", {})
    daily_summary = daily_skillops.get("summary", {}) if isinstance(daily_skillops, dict) else {}
    weekly_summary = weekly_curator.get("summary", {}) if isinstance(weekly_curator, dict) else {}
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
    skillops_parts = []
    skillops_blocked = False
    for label, report, summary in [
        ("daily", daily_skillops, daily_summary),
        ("weekly", weekly_curator, weekly_summary),
    ]:
        if not report:
            continue
        writes_source = bool(summary.get("writes_source_files") or report.get("writes_source_files"))
        auto_patch = bool(summary.get("auto_patch_enabled") or report.get("auto_patch_enabled"))
        failure_count = int(summary.get("failure_count", 0) or 0)
        if writes_source or auto_patch or failure_count:
            skillops_blocked = True
        if label == "daily":
            skillops_parts.append(
                f"daily proposals {summary.get('proposal_count', 0)}; "
                f"daily decision {summary.get('decision', report.get('decision', 'unknown'))}; "
                f"daily release lock {str(summary.get('release_lock_ready', False)).lower()}"
            )
        else:
            skillops_parts.append(
                f"weekly queue {summary.get('unique_opportunity_count', 0)} unique; "
                f"weekly ready {summary.get('ready_for_approval_review_count', 0)}; "
                f"weekly top {summary.get('top_score', 0)}; "
                f"weekly release lock {str(summary.get('release_lock_ready', False)).lower()}"
            )
    if skillops_blocked:
        adoption_status = "block"
    if skillops_parts:
        adoption_detail = adoption_detail + "; " + "; ".join(skillops_parts)
    gates.append(
        gate(
            "operations-loop",
            "运营回路",
            adoption_status,
            adoption_detail,
            "reports/adoption_drift_report.json + reports/skillops/daily + reports/skillops/weekly",
            report_link(output_html, skill_dir, "reports/adoption_drift_report.md"),
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
            report_link(output_html, skill_dir, "reports/review_waivers.md"),
        )
    )

    world_class_ledger = data.get("world_class_evidence_ledger", {})
    world_class_summary = world_class_ledger.get("summary", {}) if isinstance(world_class_ledger, dict) else {}
    source_check_count = int(world_class_summary.get("source_check_count", 0) or 0)
    source_pass_count = int(world_class_summary.get("source_pass_count", 0) or 0)
    source_blocked_count = int(world_class_summary.get("source_blocked_count", 0) or 0)
    source_check_detail = (
        f"source checks {source_pass_count}/{source_check_count} pass; {source_blocked_count} blocked"
        if source_check_count
        else "source checks unavailable"
    )
    if not world_class_ledger and maturity == "governed":
        world_class_status = "warn"
        world_class_detail = "world-class evidence ledger is missing; public world-class readiness cannot be claimed"
    elif not world_class_ledger:
        world_class_status = "pass"
        world_class_detail = "world-class evidence ledger is optional until governed or public world-class readiness is claimed"
    elif world_class_summary.get("ready_to_claim_world_class") is True:
        world_class_status = "pass"
        world_class_detail = (
            f"{world_class_summary.get('accepted_count', 0)} accepted evidence entries; "
            f"{world_class_summary.get('pending_count', 0)} pending; "
            f"{source_check_detail}"
        )
    else:
        world_class_status = "warn"
        world_class_detail = (
            f"{world_class_summary.get('pending_count', 0)} pending world-class evidence entries; "
            f"{world_class_summary.get('human_pending_count', 0)} human pending; "
            f"{world_class_summary.get('external_pending_count', 0)} external pending; "
            f"{source_check_detail}; "
            f"overclaim guard {str(world_class_summary.get('overclaim_guard_active', False)).lower()}"
        )
    gates.append(
        gate(
            "world-class-evidence",
            "世界证据",
            world_class_status,
            world_class_detail,
            "reports/world_class_evidence_ledger.json",
            report_link(output_html, skill_dir, "reports/world_class_evidence_ledger.md"),
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
            report_link(output_html, skill_dir, "reports/registry_audit.md"),
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
            report_link(output_html, skill_dir, "reports/promotion_decisions.md") if promotion else str(migration_path),
        )
    )

    return gates
