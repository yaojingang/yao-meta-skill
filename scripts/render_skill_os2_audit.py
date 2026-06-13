#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
STATUS_LABELS = {
    "pass": "pass",
    "warn": "warn",
    "human_required": "human-required",
    "external_required": "external-required",
    "missing": "missing",
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def rel_path(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def evidence(skill_dir: Path, *paths: str) -> list[dict[str, Any]]:
    items = []
    for rel in paths:
        path = skill_dir / rel
        items.append({"path": rel, "exists": path.exists()})
    return items


def status_from(condition: bool, fallback: str = "missing") -> str:
    return "pass" if condition else fallback


def audit_item(
    key: str,
    label: str,
    status: str,
    current: str,
    target: str,
    evidence_items: list[dict[str, Any]],
    next_action: str,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "status": status,
        "current": current,
        "target": target,
        "evidence": evidence_items,
        "next_action": next_action,
    }


def count_sources(events_summary: dict[str, Any]) -> dict[str, int]:
    values = events_summary.get("source_types", {})
    return values if isinstance(values, dict) else {}


def build_audit(skill_dir: Path, generated_at: str) -> dict[str, Any]:
    reports = skill_dir / "reports"
    skill_ir = load_json(skill_dir / "skill-ir" / "examples" / "yao-meta-skill.json")
    compiled = load_json(reports / "compiled_targets.json")
    output_quality = load_json(reports / "output_quality_scorecard.json")
    output_execution = load_json(reports / "output_execution_runs.json")
    output_review = load_json(reports / "output_review_adjudication.json")
    conformance = load_json(reports / "conformance_matrix.json")
    trust = load_json(reports / "security_trust_report.json")
    runtime_permissions = load_json(reports / "runtime_permission_probes.json")
    atlas = load_json(reports / "skill_atlas.json")
    registry = load_json(reports / "registry_audit.json")
    package_verification = load_json(reports / "package_verification.json")
    install = load_json(reports / "install_simulation.json")
    review_studio = load_json(reports / "review-studio.json")
    adoption = load_json(reports / "adoption_drift_report.json")
    telemetry_hooks = load_json(reports / "telemetry_hook_recipes.json")

    compiled_summary = compiled.get("summary", {})
    output_summary = output_quality.get("summary", {})
    execution_summary = output_execution.get("summary", {})
    review_summary = output_review.get("summary", {})
    conformance_summary = conformance.get("summary", {})
    trust_summary = trust.get("summary", {})
    permission_summary = runtime_permissions.get("summary", {})
    atlas_summary = atlas.get("summary", {})
    package_summary = package_verification.get("summary", {})
    install_summary = install.get("summary", {})
    studio_summary = review_studio.get("summary", {})
    adoption_summary = adoption.get("summary", {})
    telemetry_summary = telemetry_hooks.get("summary", {})
    sources = count_sources(adoption_summary)

    items = [
        audit_item(
            "skill-ir",
            "Skill IR",
            status_from(
                skill_ir.get("schema_version") == "2.0.0"
                and bool((skill_dir / "skill-ir" / "schema.json").exists())
                and bool((skill_dir / "skill-ir" / "examples" / "yao-meta-skill.json").exists())
            ),
            f"schema {skill_ir.get('schema_version', 'missing')}; targets {len(skill_ir.get('targets', []))}",
            "2.0 schema, root export, and target-neutral contract evidence",
            evidence(skill_dir, "skill-ir/schema.json", "skill-ir/examples/yao-meta-skill.json", "references/skill-ir-method.md"),
            "Keep IR as the source before target packaging.",
        ),
        audit_item(
            "target-compiler",
            "Target Compiler",
            status_from(compiled_summary.get("target_count", 0) >= 5 and compiled_summary.get("pass_count") == compiled_summary.get("target_count")),
            f"{compiled_summary.get('pass_count', 0)}/{compiled_summary.get('target_count', 0)} targets pass",
            "OpenAI, Claude, generic, Agent Skills compatible, and VS Code contracts generated from IR",
            evidence(skill_dir, "scripts/compile_skill.py", "reports/compiled_targets.json", "tests/verify_compile_skill.py"),
            "Deepen target-native transforms when provider clients expose stronger runtime APIs.",
        ),
        audit_item(
            "output-eval-lab",
            "Output Eval Lab",
            status_from(
                output_summary.get("case_count", 0) >= 5
                and output_summary.get("gate_pass") is True
                and execution_summary.get("variant_run_count", 0) >= 10
                and output_summary.get("blind_pair_count", 0) >= 5
            ),
            (
                f"{output_summary.get('case_count', 0)} cases; "
                f"delta {output_summary.get('delta', 'n/a')}; "
                f"exec {execution_summary.get('variant_run_count', 0)}; "
                f"blind {output_summary.get('blind_pair_count', 0)}"
            ),
            "with-skill/baseline, assertions, execution evidence, blind A/B, failure taxonomy",
            evidence(
                skill_dir,
                "evals/output/cases.jsonl",
                "scripts/run_output_eval.py",
                "scripts/run_output_execution.py",
                "reports/output_quality_scorecard.json",
                "reports/output_execution_runs.json",
                "reports/output_blind_review_pack.json",
            ),
            "Add more real-file and adversarial holdout cases as usage grows.",
        ),
        audit_item(
            "provider-holdout",
            "Provider Holdout",
            "pass" if execution_summary.get("model_executed_count", 0) > 0 else "external_required",
            f"model-executed {execution_summary.get('model_executed_count', 0)}; token-observed {execution_summary.get('token_observed_count', 0)}",
            "At least one real provider-backed holdout run with observed model/timing/token metadata",
            evidence(skill_dir, "scripts/provider_output_eval_runner.py", "reports/output_execution_runs.json"),
            "Run provider-backed holdout cases with real credentials and commit only aggregate evidence.",
        ),
        audit_item(
            "human-adjudication",
            "Human Adjudication",
            "pass" if review_summary.get("pair_count", 0) > 0 and review_summary.get("pending_count", 0) == 0 else "human_required",
            f"{review_summary.get('judgment_count', 0)}/{review_summary.get('pair_count', 0)} decisions; pending {review_summary.get('pending_count', 0)}",
            "Real reviewer decisions recorded before claiming output review completion",
            evidence(skill_dir, "reports/output_review_decisions.json", "reports/output_review_adjudication.json", "scripts/adjudicate_output_review.py"),
            "Record real A/B choices in the decision template, then regenerate adjudication.",
        ),
        audit_item(
            "runtime-conformance",
            "Runtime Conformance",
            status_from(conformance_summary.get("target_count", 0) >= 5 and conformance_summary.get("pass_count") == conformance_summary.get("target_count")),
            f"{conformance_summary.get('pass_count', 0)}/{conformance_summary.get('target_count', 0)} targets pass",
            "Target package structure, metadata, relative paths, and degradation notes pass",
            evidence(skill_dir, "runtime/conformance/schema.json", "scripts/run_conformance_suite.py", "reports/conformance_matrix.json"),
            "Keep target conformance fixtures updated as platform contracts change.",
        ),
        audit_item(
            "trust-security",
            "Trust Security",
            status_from(
                trust.get("ok") is True
                and trust_summary.get("secret_findings", 1) == 0
                and trust_summary.get("help_smoke_failed_count", 1) == 0
                and trust_summary.get("permission_missing_count", 1) == 0
            ),
            (
                f"secrets {trust_summary.get('secret_findings', 'n/a')}; "
                f"scripts {trust_summary.get('script_count', 'n/a')}; "
                f"help failures {trust_summary.get('help_smoke_failed_count', 'n/a')}"
            ),
            "Secrets, scripts, dependencies, permissions, and package hash are reviewable",
            evidence(skill_dir, "scripts/trust_check.py", "reports/security_trust_report.json", "security/permission_policy.json"),
            "Keep high-permission approvals scoped, expiring, and target-mapped.",
        ),
        audit_item(
            "runtime-permission-metadata",
            "Permission Metadata",
            status_from(permission_summary.get("target_count", 0) >= 4 and permission_summary.get("fail_count", 1) == 0),
            f"{permission_summary.get('pass_count', 0)}/{permission_summary.get('target_count', 0)} target probes pass; metadata fallback {permission_summary.get('metadata_fallback_count', 0)}",
            "Packaged adapters expose explicit permission metadata and residual risks",
            evidence(skill_dir, "scripts/probe_runtime_permissions.py", "reports/runtime_permission_probes.json"),
            "Preserve residual-risk notes until real native enforcement exists.",
        ),
        audit_item(
            "native-permission-enforcement",
            "Native Permission Enforcement",
            "pass" if permission_summary.get("native_enforcement_count", 0) > 0 else "external_required",
            f"native-enforced targets {permission_summary.get('native_enforcement_count', 0)}",
            "At least one target/client enforces approved permissions at runtime",
            evidence(skill_dir, "reports/runtime_permission_probes.json", "security/permission_policy.json"),
            "Integrate a real client or installer runtime guard before claiming native permission enforcement.",
        ),
        audit_item(
            "skill-atlas",
            "Skill Atlas",
            status_from(
                atlas_summary.get("actionable_skill_count", 0) >= 1
                and atlas_summary.get("actionable_route_collision_count", 1) == 0
                and atlas_summary.get("actionable_owner_gap_count", 1) == 0
            ),
            f"{atlas_summary.get('skill_count', 0)} skills; actionable collisions {atlas_summary.get('actionable_route_collision_count', 0)}",
            "Workspace catalog, route overlap, stale/owner gaps, drift, and no-route opportunities",
            evidence(skill_dir, "scripts/build_skill_atlas.py", "skill_atlas/catalog.json", "reports/skill_atlas.json", "skill_atlas/policy.json"),
            "Feed real drift data into Atlas once client telemetry is installed.",
        ),
        audit_item(
            "registry-distribution",
            "Registry Distribution",
            status_from(
                registry.get("ok") is True
                and package_verification.get("ok") is True
                and install.get("ok") is True
                and package_summary.get("archive_entry_count", 0) > 0
                and install_summary.get("installer_permission_failure_count", 1) == 0
            ),
            (
                f"zip entries {package_summary.get('archive_entry_count', 0)}; "
                f"install failures {install_summary.get('failure_count', 0)}; "
                f"permission failures {install_summary.get('installer_permission_failure_count', 0)}"
            ),
            "Package metadata, archive checksum, package verification, and install simulation pass",
            evidence(skill_dir, "registry/packages/yao-meta-skill.json", "reports/package_verification.json", "reports/install_simulation.json"),
            "Regenerate registry after package verification so checksums stay aligned.",
        ),
        audit_item(
            "review-studio",
            "Review Studio",
            status_from(studio_summary.get("gate_count", 0) >= 13 and studio_summary.get("blocker_count", 1) == 0),
            f"decision {studio_summary.get('decision', 'missing')}; warnings {studio_summary.get('warning_count', 0)}; score {studio_summary.get('world_class_score', 'n/a')}",
            "One page shows gates, evidence paths, blockers, warnings, actions, waivers, and annotations",
            evidence(skill_dir, "scripts/render_review_studio.py", "reports/review-studio.json", "reports/review-studio.html"),
            "Resolve human/external warning gates before claiming full release readiness.",
        ),
        audit_item(
            "telemetry-drift",
            "Telemetry Drift",
            status_from(
                adoption.get("ok") is True
                and adoption.get("privacy_contract", {}).get("raw_content_allowed") is False
                and telemetry_summary.get("recipe_count", 0) >= 5
            ),
            f"events {adoption_summary.get('event_count', 0)}; risk {adoption_summary.get('risk_band', 'missing')}; recipes {telemetry_summary.get('recipe_count', 0)}",
            "Local-first metadata-only event contract, aggregate drift report, hook recipes, and import path",
            evidence(skill_dir, "reports/adoption_drift_report.json", "reports/telemetry_hook_recipes.json", "scripts/import_telemetry_events.py"),
            "Keep raw JSONL out of distributed packages and use aggregate reports for Atlas.",
        ),
        audit_item(
            "native-client-telemetry",
            "Native Client Telemetry",
            "pass" if sources.get("external", 0) > 0 and adoption_summary.get("adoption_sample_count", 0) > 0 else "external_required",
            f"external source events {sources.get('external', 0)}; adoption samples {adoption_summary.get('adoption_sample_count', 0)}",
            "A real Browser/Chrome/provider client sends production metadata events",
            evidence(skill_dir, "scripts/telemetry_native_host.py", "reports/adoption_drift_report.json"),
            "Install a real client against the native host and import production metadata-only events.",
        ),
    ]

    counts: dict[str, int] = {key: 0 for key in STATUS_LABELS}
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    open_gap_count = sum(counts.get(key, 0) for key in ("warn", "human_required", "external_required", "missing"))
    local_foundation_ready = counts.get("missing", 0) == 0 and counts.get("warn", 0) == 0
    world_class_ready = open_gap_count == 0
    summary = {
        "item_count": len(items),
        "pass_count": counts.get("pass", 0),
        "warn_count": counts.get("warn", 0),
        "human_required_count": counts.get("human_required", 0),
        "external_required_count": counts.get("external_required", 0),
        "missing_count": counts.get("missing", 0),
        "open_gap_count": open_gap_count,
        "local_foundation_ready": local_foundation_ready,
        "world_class_ready": world_class_ready,
        "decision": "world-class-ready" if world_class_ready else "continue-iteration",
    }
    return {
        "schema_version": "1.0",
        "ok": counts.get("missing", 0) == 0,
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        "summary": summary,
        "status_counts": counts,
        "items": items,
        "next_highest_leverage": [
            item for item in items if item["status"] in {"human_required", "external_required", "warn", "missing"}
        ][:5],
        "artifacts": {
            "json": "reports/skill_os2_audit.json",
            "markdown": "reports/skill_os2_audit.md",
            "world_class_evidence_plan": "reports/world_class_evidence_plan.md",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Skill OS 2.0 Audit",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- pass: `{summary['pass_count']}` / `{summary['item_count']}`",
        f"- human required: `{summary['human_required_count']}`",
        f"- external required: `{summary['external_required_count']}`",
        f"- missing: `{summary['missing_count']}`",
        f"- world-class ready: `{str(summary['world_class_ready']).lower()}`",
        "- evidence plan: `reports/world_class_evidence_plan.md`",
        "",
        "## Audit Items",
        "",
        "| Area | Status | Current | Target | Next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["items"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    item["label"],
                    STATUS_LABELS.get(item["status"], item["status"]),
                    item["current"].replace("|", "\\|"),
                    item["target"].replace("|", "\\|"),
                    item["next_action"].replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(["", "## Open Highest-Leverage Gaps", ""])
    for item in report["next_highest_leverage"]:
        lines.append(f"- `{item['key']}` ({STATUS_LABELS.get(item['status'], item['status'])}): {item['next_action']}")
    if not report["next_highest_leverage"]:
        lines.append("- None.")
    lines.extend(["", "## Evidence", ""])
    for item in report["items"]:
        paths = [entry["path"] for entry in item["evidence"] if entry.get("exists")]
        missing = [entry["path"] for entry in item["evidence"] if not entry.get("exists")]
        lines.append(f"### {item['label']}")
        lines.append("")
        lines.append(f"- existing evidence: {', '.join(f'`{path}`' for path in paths) if paths else '`none`'}")
        if missing:
            lines.append(f"- missing evidence: {', '.join(f'`{path}`' for path in missing)}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a requirement-by-requirement Skill OS 2.0 audit.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-json", default="reports/skill_os2_audit.json")
    parser.add_argument("--output-md", default="reports/skill_os2_audit.md")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    report = build_audit(skill_dir, args.generated_at)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    if not output_json.is_absolute():
        output_json = skill_dir / output_json
    if not output_md.is_absolute():
        output_md = skill_dir / output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output_md.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
