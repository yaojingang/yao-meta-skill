#!/usr/bin/env python3
"""Data loading and insight card helpers for Review Studio."""

import json
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


SCRIPT_INTERFACE = "internal-module"
SCRIPT_INTERFACE_REASON = "Imported by render_review_studio.py to load Review Studio source reports and metric cards."

ROOT = Path(__file__).resolve().parent.parent


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists() or yaml is None:
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def parse_frontmatter(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    try:
        end_index = lines[1:].index("---") + 1
    except ValueError:
        return {}
    text = "\n".join(lines[1:end_index])
    if yaml is not None:
        payload = yaml.safe_load(text) or {}
        return payload if isinstance(payload, dict) else {}
    data = {}
    for line in text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip().strip('"')
    return data


def evidence_paths(skill_dir: Path) -> dict[str, str]:
    rels = {
        "skill_overview": "reports/skill-overview.html",
        "review_viewer": "reports/review-viewer.html",
        "output_eval": "reports/output_quality_scorecard.md",
        "output_execution": "reports/output_execution_runs.md",
        "output_blind_review": "reports/output_blind_review_pack.md",
        "output_review_kit": "reports/output_review_kit.md",
        "output_review_kit_html": "reports/output_review_kit.html",
        "output_review_decisions": "reports/output_review_decisions.json",
        "output_review_adjudication": "reports/output_review_adjudication.md",
        "benchmark_reproducibility": "reports/benchmark_reproducibility.md",
        "skill_os2_coverage": "reports/skill_os2_coverage.md",
        "runtime_conformance": "reports/conformance_matrix.md",
        "trust_report": "reports/security_trust_report.md",
        "python_compatibility": "reports/python_compatibility.md",
        "architecture_maintainability": "reports/architecture_maintainability.md",
        "permission_policy": "security/permission_policy.md",
        "runtime_permissions": "reports/runtime_permission_probes.md",
        "skill_atlas": "reports/skill_atlas.html",
        "compiled_targets": "reports/compiled_targets.md",
        "adoption_drift": "reports/adoption_drift_report.md",
        "review_waivers": "reports/review_waivers.md",
        "review_annotations": "reports/review_annotations.md",
        "world_class_evidence_plan": "reports/world_class_evidence_plan.md",
        "world_class_evidence_ledger": "reports/world_class_evidence_ledger.md",
        "world_class_evidence_intake": "reports/world_class_evidence_intake.md",
        "world_class_submission_review": "reports/world_class_submission_review.md",
        "world_class_operator_runbook": "reports/world_class_operator_runbook.md",
        "world_class_operator_runbook_html": "reports/world_class_operator_runbook.html",
        "world_class_claim_guard": "reports/world_class_claim_guard.md",
        "registry_audit": "reports/registry_audit.md",
        "package_verification": "reports/package_verification.md",
        "install_simulation": "reports/install_simulation.md",
        "upgrade_check": "reports/upgrade_check.md",
        "migration": "docs/migration-v2.md",
        "skill_ir": "reports/skill-ir.json",
    }
    return {key: rel for key, rel in rels.items() if (skill_dir / rel).exists() or (ROOT / rel).exists()}


def load_review_data(skill_dir: Path) -> dict[str, dict[str, Any]]:
    reports = skill_dir / "reports"
    return {
        "overview": load_json(reports / "skill-overview.json"),
        "intent_confidence": load_json(reports / "intent-confidence.json"),
        "intent_dialogue": load_json(reports / "intent-dialogue.json"),
        "route_scorecard": load_json(reports / "route_scorecard.json"),
        "output_quality": load_json(reports / "output_quality_scorecard.json"),
        "output_execution": load_json(reports / "output_execution_runs.json"),
        "output_blind_review": load_json(reports / "output_blind_review_pack.json"),
        "output_review_kit": load_json(reports / "output_review_kit.json"),
        "output_review_adjudication": load_json(reports / "output_review_adjudication.json"),
        "benchmark_reproducibility": load_json(reports / "benchmark_reproducibility.json"),
        "skill_os2_coverage": load_json(reports / "skill_os2_coverage.json"),
        "compiled_targets": load_json(reports / "compiled_targets.json"),
        "conformance": load_json(reports / "conformance_matrix.json"),
        "runtime_permissions": load_json(reports / "runtime_permission_probes.json"),
        "trust": load_json(reports / "security_trust_report.json"),
        "python_compatibility": load_json(reports / "python_compatibility.json"),
        "architecture_maintainability": load_json(reports / "architecture_maintainability.json"),
        "context_budget": load_json(reports / "context_budget.json"),
        "promotion": load_json(reports / "promotion_decisions.json"),
        "atlas": load_json(reports / "skill_atlas.json"),
        "adoption_drift": load_json(reports / "adoption_drift_report.json"),
        "review_waivers": load_json(reports / "review_waivers.json"),
        "review_annotations": load_json(reports / "review_annotations.json"),
        "world_class_evidence_ledger": load_json(reports / "world_class_evidence_ledger.json"),
        "world_class_evidence_intake": load_json(reports / "world_class_evidence_intake.json"),
        "world_class_submission_review": load_json(reports / "world_class_submission_review.json"),
        "world_class_operator_runbook": load_json(reports / "world_class_operator_runbook.json"),
        "world_class_claim_guard": load_json(reports / "world_class_claim_guard.json"),
        "registry": load_json(reports / "registry_audit.json"),
        "package_verification": load_json(reports / "package_verification.json"),
        "install_simulation": load_json(reports / "install_simulation.json"),
        "upgrade_check": load_json(reports / "upgrade_check.json"),
        "manifest": load_json(skill_dir / "manifest.json"),
        "frontmatter": parse_frontmatter(skill_dir / "SKILL.md"),
        "interface": load_yaml(skill_dir / "agents" / "interface.yaml"),
    }


def insight_cards(data: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    overview = data["overview"]
    output = data["output_quality"].get("summary", {})
    output_execution = data["output_execution"].get("summary", {})
    output_blind = data["output_blind_review"].get("summary", {})
    output_review_kit = data["output_review_kit"].get("summary", {})
    output_review = data["output_review_adjudication"].get("summary", {})
    benchmark = data["benchmark_reproducibility"].get("summary", {})
    blueprint = data["skill_os2_coverage"].get("summary", {})
    compiled = data["compiled_targets"].get("summary", {})
    conformance = data["conformance"].get("summary", {})
    runtime_permissions = data["runtime_permissions"].get("summary", {})
    trust = data["trust"].get("summary", {})
    python_compat = data["python_compatibility"].get("summary", {})
    architecture = data["architecture_maintainability"].get("summary", {})
    atlas = data["atlas"].get("summary", {})
    adoption = data["adoption_drift"].get("summary", {})
    waivers = data["review_waivers"].get("summary", {})
    annotations = data["review_annotations"].get("summary", {})
    intake = data["world_class_evidence_intake"].get("summary", {})
    claim_guard = data["world_class_claim_guard"].get("summary", {})
    registry = data["registry"].get("package", {})
    package_verification = data["package_verification"].get("summary", {})
    install_simulation = data["install_simulation"].get("summary", {})
    upgrade = data["upgrade_check"].get("summary", {})
    cards = [
        {
            "label": "Skill IR",
            "value": str(overview.get("skill_ir", {}).get("schema_version", "missing")),
            "detail": f"{overview.get('skill_ir', {}).get('target_count', 0)} targets in platform-neutral contract",
        },
        {
            "label": "Compiler",
            "value": f"{compiled.get('pass_count', 0)}/{compiled.get('target_count', 0)}",
            "detail": "target contracts compiled from Skill IR",
        },
        {
            "label": "Output Delta",
            "value": str(output.get("delta", "n/a")),
            "detail": f"{output.get('case_count', 0)} cases; {output.get('file_backed_case_count', 0)} file-backed",
        },
        {
            "label": "Exec Runs",
            "value": str(output_execution.get("variant_run_count", 0)),
            "detail": (
                f"command {output_execution.get('command_executed_count', 0)}; "
                f"model {output_execution.get('model_executed_count', 0)}; "
                f"recorded {output_execution.get('recorded_fixture_count', 0)}"
            ),
        },
        {
            "label": "Blind A/B",
            "value": str(output_blind.get("pair_count", 0)),
            "detail": "review pairs hide baseline vs with-skill labels",
        },
        {
            "label": "Review Kit",
            "value": f"{output_review_kit.get('ready_for_adjudication_count', 0)}/{output_review_kit.get('case_count', 0)}",
            "detail": f"pending {output_review_kit.get('pending_decision_count', 0)}; answer key hidden",
        },
        {
            "label": "Review A/B",
            "value": f"{output_review.get('judgment_count', 0)}/{output_review.get('pair_count', 0)}",
            "detail": f"adjudication decisions; pending {output_review.get('pending_count', 0)}",
        },
        {
            "label": "Public Claim",
            "value": "ready" if benchmark.get("public_claim_ready") is True else "blocked",
            "detail": f"{benchmark.get('public_claim_blocker_count', 0)} blockers; local reproducible {str(benchmark.get('reproducibility_ready', False)).lower()}",
        },
        {
            "label": "Blueprint",
            "value": f"{blueprint.get('pass_count', 0)}/{blueprint.get('item_count', 0)}",
            "detail": f"2.0 coverage; evidence pending {blueprint.get('world_class_evidence_pending_count', 0)}",
        },
        {
            "label": "Runtime",
            "value": f"{conformance.get('pass_count', 0)}/{conformance.get('target_count', 0)}",
            "detail": "target conformance pass rate",
        },
        {
            "label": "Perm Probe",
            "value": f"{runtime_permissions.get('metadata_fallback_count', 0)}/{runtime_permissions.get('target_count', 0)}",
            "detail": (
                f"{runtime_permissions.get('native_enforcement_count', 0)} native; "
                f"{runtime_permissions.get('installer_enforcement_pass_count', 0)} installer-enforced"
            ),
        },
        {
            "label": "Trust",
            "value": str(trust.get("secret_findings", 0)),
            "detail": f"{trust.get('script_count', 0)} scripts scanned; secrets found",
        },
        {
            "label": "Py Compat",
            "value": str(python_compat.get("issue_count", 0)),
            "detail": f"{python_compat.get('file_count', 0)} files scanned for Python {python_compat.get('target_python', '3.11')}",
        },
        {
            "label": "Arch Debt",
            "value": str(architecture.get("hotspot_count", 0)),
            "detail": (
                f"{architecture.get('largest_file_lines', 0)} largest lines; "
                f"{architecture.get('command_handler_count', 0)} CLI handlers"
            ),
        },
        {
            "label": "Atlas",
            "value": str(atlas.get("route_collision_count", 0)),
            "detail": f"{atlas.get('skill_count', 0)} scanned skills; route collisions",
        },
        {
            "label": "Drift",
            "value": str(adoption.get("risk_band", "n/a")),
            "detail": f"{adoption.get('event_count', 0)} metadata events; {adoption.get('missed_trigger_count', 0)} missed triggers",
        },
        {
            "label": "Waivers",
            "value": str(waivers.get("active_count", 0)),
            "detail": f"{waivers.get('covered_gate_count', 0)} gates covered; human risk decisions",
        },
        {
            "label": "Intake",
            "value": f"{intake.get('template_pass_count', 0)}/{intake.get('template_count', 0)}",
            "detail": (
                f"{intake.get('valid_submission_count', 0)} valid submissions; "
                f"{intake.get('invalid_submission_count', 0)} invalid"
            ),
        },
        {
            "label": "Claim Guard",
            "value": str(claim_guard.get("violation_count", 0)),
            "detail": f"{claim_guard.get('claim_surface_count', 0)} public surfaces scanned",
        },
        {
            "label": "Notes",
            "value": f"{annotations.get('open_count', 0)}/{annotations.get('annotation_count', 0)}",
            "detail": f"{annotations.get('open_blocker_count', 0)} open blocker annotations",
        },
        {
            "label": "Registry",
            "value": str(registry.get("version", "n/a")),
            "detail": f"{len(registry.get('targets', []))} targets; {registry.get('license', 'no license')} license",
        },
        {
            "label": "Archive",
            "value": "pass" if data["package_verification"].get("ok") else "n/a",
            "detail": f"{package_verification.get('archive_entry_count', 0)} zip entries; package verification",
        },
        {
            "label": "Install",
            "value": "pass" if data["install_simulation"].get("ok") else "n/a",
            "detail": (
                f"{install_simulation.get('adapter_count', 0)} adapters; "
                f"{install_simulation.get('installer_permission_enforced_count', 0)} permissions enforced; "
                f"{install_simulation.get('installer_permission_failure_count', 0)} permission failures"
            ),
        },
        {
            "label": "Upgrade",
            "value": str(upgrade.get("recommended_bump", "n/a")),
            "detail": f"declared {upgrade.get('declared_bump', 'n/a')}; {upgrade.get('breaking_change_count', 0)} breaking changes",
        },
    ]
    return cards
