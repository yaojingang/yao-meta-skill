#!/usr/bin/env python3
import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
SCRIPT_INTERFACE = "cli"
SCRIPT_INTERFACE_REASON = "Renders a Skill OS 2.0 blueprint-to-evidence coverage audit."
RECOMMENDED_PR_LABELS = {
    "benchmark-methodology": "Benchmark Methodology",
    "output-eval-schema": "Output Eval Schema",
    "output-eval-runner": "Output Eval Runner",
    "output-quality-scorecard": "Output Quality Scorecard",
    "skill-ir-v0": "Skill IR V0",
    "compiler-refactor": "Compiler Refactor",
    "agent-skills-conformance": "Agent Skills Conformance",
    "trust-check": "Trust Check",
    "skill-atlas-generator": "Skill Atlas Generator",
    "registry-package-format": "Registry Package Format",
    "review-studio-2": "Review Studio 2.0",
    "migration-v2-docs": "Migration V2 Docs",
    "evidence-consistency": "Evidence Consistency",
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


def evidence(skill_dir: Path, paths: list[str]) -> list[dict[str, Any]]:
    return [{"path": item, "exists": (skill_dir / item).exists()} for item in paths]


def all_exist(items: list[dict[str, Any]]) -> bool:
    return all(item["exists"] for item in items)


def paths_exist(skill_dir: Path, paths: list[str]) -> bool:
    return all((skill_dir / item).exists() for item in paths)


def condition_status(condition: bool, evidence_items: list[dict[str, Any]]) -> str:
    if not all_exist(evidence_items):
        return "missing"
    return "pass" if condition else "warn"


def build_item(
    *,
    key: str,
    category: str,
    label: str,
    objective: str,
    artifact_paths: list[str],
    command: str,
    test: str,
    current: str,
    condition: bool,
    next_action: str,
    skill_dir: Path,
) -> dict[str, Any]:
    evidence_items = evidence(skill_dir, artifact_paths)
    status = condition_status(condition, evidence_items)
    return {
        "key": key,
        "category": category,
        "label": label,
        "status": status,
        "objective": objective,
        "current": current,
        "command": command,
        "test": test,
        "evidence": evidence_items,
        "next_action": next_action,
    }


def build_extension_track(
    *,
    key: str,
    label: str,
    status: str,
    objective: str,
    current: str,
    target: str,
    artifact_paths: list[str],
    next_action: str,
    skill_dir: Path,
) -> dict[str, Any]:
    return {
        "key": key,
        "label": label,
        "status": status,
        "objective": objective,
        "current": current,
        "target": target,
        "evidence": evidence(skill_dir, artifact_paths),
        "next_action": next_action,
    }


def summary_value(payload: dict[str, Any], key: str, default: Any = 0) -> Any:
    summary = payload.get("summary", {})
    return summary.get(key, default) if isinstance(summary, dict) else default


def target_names(payload: dict[str, Any]) -> set[str]:
    names = set()
    for item in payload.get("targets", []) or payload.get("results", []):
        if isinstance(item, dict):
            value = item.get("target") or item.get("platform") or item.get("name")
            if value:
                names.add(str(value))
    return names


def build_coverage(skill_dir: Path, generated_at: str) -> dict[str, Any]:
    reports = skill_dir / "reports"
    skill_ir = load_json(skill_dir / "skill-ir" / "examples" / "yao-meta-skill.json")
    output_quality = load_json(reports / "output_quality_scorecard.json")
    output_execution = load_json(reports / "output_execution_runs.json")
    compiled = load_json(reports / "compiled_targets.json")
    conformance = load_json(reports / "conformance_matrix.json")
    trust = load_json(reports / "security_trust_report.json")
    atlas = load_json(reports / "skill_atlas.json")
    registry = load_json(reports / "registry_audit.json")
    package_verification = load_json(reports / "package_verification.json")
    install = load_json(reports / "install_simulation.json")
    review_studio = load_json(reports / "review-studio.json")
    adoption = load_json(reports / "adoption_drift_report.json")
    telemetry_hooks = load_json(reports / "telemetry_hook_recipes.json")
    benchmark = load_json(reports / "benchmark_reproducibility.json")
    world_class_ledger = load_json(reports / "world_class_evidence_ledger.json")
    evidence_consistency = load_json(reports / "evidence_consistency.json")

    output_case_count = summary_value(output_quality, "case_count")
    output_delta = summary_value(output_quality, "delta", "n/a")
    execution_count = summary_value(output_execution, "variant_run_count")
    compiled_count = summary_value(compiled, "target_count")
    compiled_pass = summary_value(compiled, "pass_count")
    conformance_count = summary_value(conformance, "target_count")
    conformance_pass = summary_value(conformance, "pass_count")
    script_count = summary_value(trust, "script_count")
    atlas_skill_count = summary_value(atlas, "skill_count")
    package_entries = summary_value(package_verification, "archive_entry_count")
    install_failures = summary_value(install, "failure_count")
    studio_gates = summary_value(review_studio, "gate_count")
    telemetry_recipe_count = summary_value(telemetry_hooks, "recipe_count")
    benchmark_artifacts = summary_value(benchmark, "required_artifact_count")
    pending_world_class = summary_value(world_class_ledger, "pending_count")

    modules = [
        build_item(
            key="skill-ir",
            category="core-module",
            label="Skill IR",
            objective="Platform-neutral capability contract exists before platform-specific packaging.",
            artifact_paths=["skill-ir/schema.json", "skill-ir/examples/yao-meta-skill.json", "scripts/export_skill_ir.py", "tests/verify_skill_ir.py"],
            command="python3 scripts/yao.py skill-ir .",
            test="python3 tests/verify_skill_ir.py",
            current=f"schema {skill_ir.get('schema_version', 'missing')}; targets {len(skill_ir.get('targets', []))}",
            condition=skill_ir.get("schema_version") == "2.0.0" and len(skill_ir.get("targets", [])) >= 5,
            next_action="Keep all target packages compiled from IR rather than hand-maintained per target.",
            skill_dir=skill_dir,
        ),
        build_item(
            key="output-eval-lab",
            category="core-module",
            label="Output Eval Lab",
            objective="with-skill/baseline output quality is measured with assertions, execution evidence, and blind review packs.",
            artifact_paths=["evals/output/schema.json", "evals/output/cases.jsonl", "scripts/run_output_eval.py", "scripts/run_output_execution.py", "reports/output_quality_scorecard.json", "tests/verify_output_eval_lab.py"],
            command="python3 scripts/yao.py output-exec . && python3 scripts/yao.py output-review .",
            test="python3 tests/verify_output_eval_lab.py",
            current=f"{output_case_count} cases; delta {output_delta}; execution {execution_count}",
            condition=output_case_count >= 5 and execution_count >= 10 and summary_value(output_quality, "gate_pass") is True,
            next_action="Add more real-file and adversarial holdout cases as adoption data grows.",
            skill_dir=skill_dir,
        ),
        build_item(
            key="runtime-conformance",
            category="core-module",
            label="Runtime Conformance",
            objective="Target packages can be consumed by OpenAI, Claude, Agent Skills, VS Code, and generic targets.",
            artifact_paths=["runtime/conformance/schema.json", "scripts/run_conformance_suite.py", "reports/conformance_matrix.json", "tests/verify_conformance_suite.py"],
            command="python3 scripts/yao.py conformance .",
            test="python3 tests/verify_conformance_suite.py",
            current=f"{conformance_pass}/{conformance_count} targets pass",
            condition=conformance_count >= 5 and conformance_pass == conformance_count and "agent-skills" in target_names(conformance),
            next_action="Keep conformance cases aligned with current platform metadata rules.",
            skill_dir=skill_dir,
        ),
        build_item(
            key="trust-security",
            category="core-module",
            label="Trust Security",
            objective="Scripts, dependencies, permissions, secrets, and package hash are reviewable for team distribution.",
            artifact_paths=["scripts/trust_check.py", "security/trust_policy.md", "security/script_policy.md", "security/permission_policy.json", "reports/security_trust_report.json", "tests/verify_trust_check.py"],
            command="python3 scripts/yao.py trust .",
            test="python3 tests/verify_trust_check.py",
            current=f"{script_count} scripts; secrets {summary_value(trust, 'secret_findings', 'n/a')}; help failures {summary_value(trust, 'help_smoke_failed_count', 'n/a')}",
            condition=trust.get("ok") is True and summary_value(trust, "secret_findings", 1) == 0 and summary_value(trust, "help_smoke_failed_count", 1) == 0,
            next_action="Keep high-permission approvals scoped, expiring, and mapped to target enforcement.",
            skill_dir=skill_dir,
        ),
        build_item(
            key="skill-atlas",
            category="core-module",
            label="Skill Atlas",
            objective="Team skill portfolio reveals route collisions, stale ownership, dependency graph, and no-route opportunities.",
            artifact_paths=["scripts/build_skill_atlas.py", "skill_atlas/catalog.json", "skill_atlas/route_overlap_matrix.csv", "skill_atlas/dependency_graph.json", "reports/skill_atlas.json", "tests/verify_skill_atlas.py"],
            command="python3 scripts/yao.py skill-atlas --workspace-root .",
            test="python3 tests/verify_skill_atlas.py",
            current=f"{atlas_skill_count} scanned skills; actionable collisions {summary_value(atlas, 'actionable_route_collision_count')}",
            condition=atlas_skill_count >= 1 and summary_value(atlas, "actionable_route_collision_count", 1) == 0,
            next_action="Use real telemetry to rank stale or drifting skills by impact, not only by static metadata.",
            skill_dir=skill_dir,
        ),
        build_item(
            key="registry-distribution",
            category="core-module",
            label="Registry Distribution",
            objective="Skill packages are installable, versioned, checksumed, and upgrade-reviewable.",
            artifact_paths=["registry/index.schema.json", "registry/package.schema.json", "registry/packages/yao-meta-skill.json", "scripts/registry_audit.py", "reports/package_verification.json", "reports/install_simulation.json", "tests/verify_registry_audit.py"],
            command="python3 scripts/yao.py package . --platform openai --platform claude --platform generic --platform vscode --output-dir dist --zip && python3 scripts/yao.py registry-audit .",
            test="python3 tests/verify_registry_audit.py",
            current=f"archive entries {package_entries}; install failures {install_failures}",
            condition=registry.get("ok") is True and package_verification.get("ok") is True and install.get("ok") is True and package_entries > 0 and install_failures == 0,
            next_action="Regenerate registry metadata after package verification so source and archive checksums stay aligned.",
            skill_dir=skill_dir,
        ),
        build_item(
            key="review-studio",
            category="core-module",
            label="Review Studio",
            objective="One HTML page supports first-pass production review across trigger, output, runtime, trust, release, and evidence actions.",
            artifact_paths=["scripts/render_review_studio.py", "reports/review-studio.html", "reports/review-studio.json", "tests/verify_review_studio.py"],
            command="python3 scripts/yao.py review-studio .",
            test="python3 tests/verify_review_studio.py",
            current=f"{studio_gates} gates; decision {summary_value(review_studio, 'decision', 'missing')}; warnings {summary_value(review_studio, 'warning_count')}",
            condition=review_studio.get("ok") is True and studio_gates >= 14 and summary_value(review_studio, "blocker_count", 1) == 0,
            next_action="Close pending human and external evidence before claiming full release readiness.",
            skill_dir=skill_dir,
        ),
        build_item(
            key="telemetry-drift",
            category="core-module",
            label="Telemetry Drift",
            objective="Real usage feedback is captured as metadata-only local-first drift signals.",
            artifact_paths=["scripts/emit_telemetry_event.py", "scripts/import_telemetry_events.py", "scripts/telemetry_native_host.py", "reports/adoption_drift_report.json", "reports/telemetry_hook_recipes.json", "tests/verify_telemetry_hooks.py"],
            command="python3 scripts/yao.py telemetry-hooks . && python3 scripts/yao.py adoption-drift .",
            test="python3 tests/verify_telemetry_hooks.py",
            current=f"events {summary_value(adoption, 'event_count')}; recipes {telemetry_recipe_count}; risk {summary_value(adoption, 'risk_band', 'missing')}",
            condition=adoption.get("ok") is True and adoption.get("privacy_contract", {}).get("raw_content_allowed") is False and telemetry_recipe_count >= 5,
            next_action="Install a real client and import production metadata-only events into the local drift loop.",
            skill_dir=skill_dir,
        ),
    ]

    recommended_prs = [
        ("benchmark-methodology", "reports/benchmark_methodology.md", "reports/benchmark_reproducibility.json", "tests/verify_benchmark_reproducibility.py", benchmark.get("ok") is True and summary_value(benchmark, "methodology_complete") is True, f"{benchmark_artifacts} required artifacts checked"),
        ("output-eval-schema", "evals/output/schema.json", "evals/output/cases.jsonl", "tests/verify_output_eval_lab.py", output_case_count >= 5, f"{output_case_count} output cases"),
        ("output-eval-runner", "scripts/run_output_eval.py", "reports/output_quality_scorecard.json", "tests/verify_output_eval_lab.py", output_quality.get("ok") is True, f"delta {output_delta}"),
        ("output-quality-scorecard", "reports/output_quality_scorecard.md", "reports/output_quality_scorecard.json", "tests/verify_output_eval_lab.py", summary_value(output_quality, "gate_pass") is True, f"gate pass {summary_value(output_quality, 'gate_pass', False)}"),
        ("skill-ir-v0", "skill-ir/schema.json", "skill-ir/examples/yao-meta-skill.json", "tests/verify_skill_ir.py", skill_ir.get("schema_version") == "2.0.0", f"schema {skill_ir.get('schema_version', 'missing')}"),
        ("compiler-refactor", "scripts/compile_skill.py", "reports/compiled_targets.json", "tests/verify_compile_skill.py", compiled_count >= 5 and compiled_pass == compiled_count, f"{compiled_pass}/{compiled_count} compiled targets"),
        ("agent-skills-conformance", "runtime/conformance/schema.json", "reports/conformance_matrix.json", "tests/verify_conformance_suite.py", "agent-skills" in target_names(conformance), "agent-skills target present"),
        ("trust-check", "scripts/trust_check.py", "reports/security_trust_report.json", "tests/verify_trust_check.py", trust.get("ok") is True, f"secret findings {summary_value(trust, 'secret_findings', 'n/a')}"),
        ("skill-atlas-generator", "scripts/build_skill_atlas.py", "reports/skill_atlas.json", "tests/verify_skill_atlas.py", atlas.get("ok") is True, f"{atlas_skill_count} scanned skills"),
        ("registry-package-format", "registry/package.schema.json", "reports/registry_audit.json", "tests/verify_registry_audit.py", registry.get("ok") is True, f"registry ok {registry.get('ok') is True}"),
        ("review-studio-2", "scripts/render_review_studio.py", "reports/review-studio.html", "tests/verify_review_studio.py", review_studio.get("ok") is True and studio_gates >= 14, f"{studio_gates} review gates"),
        ("migration-v2-docs", "docs/migration-v2.md", "reports/skill-os-2-review.md", "README.md", (skill_dir / "docs" / "migration-v2.md").exists(), "migration guide present"),
        ("evidence-consistency", "scripts/render_evidence_consistency.py", "reports/evidence_consistency.json", "tests/verify_evidence_consistency.py", evidence_consistency.get("ok") is True and summary_value(evidence_consistency, "fail_count") == 0, f"{summary_value(evidence_consistency, 'check_count')} consistency checks"),
    ]
    pr_items = [
        build_item(
            key=key,
            category="recommended-pr",
            label=RECOMMENDED_PR_LABELS[key],
            objective="Recommended Skill OS 2.0 implementation PR from the upgrade plan.",
            artifact_paths=[path_a, path_b, path_c],
            command="make ci-test",
            test=path_c if path_c.startswith("tests/") else "docs review",
            current=current,
            condition=condition,
            next_action="Keep this item covered as the implementation evolves.",
            skill_dir=skill_dir,
        )
        for key, path_a, path_b, path_c, condition, current in recommended_prs
    ]

    interpretation_paths = [
        "reports/skill-overview.html",
        "reports/skill-overview.json",
        "scripts/render_skill_overview.py",
        "scripts/render_skill_interpretation.py",
        "schemas/skill-interpretation.schema.json",
        "tests/verify_skill_interpretation.py",
    ]
    interpretation_ready = paths_exist(skill_dir, interpretation_paths)
    interpretation_status = "covered" if interpretation_ready else "partial"
    interpretation_current = (
        "Skill Overview v2 is canonical and mirrored as first-class skill-interpretation HTML/JSON with schema and tests."
        if interpretation_ready
        else "Skill Overview v2 already covers much of the explainer experience, but dedicated skill-interpretation JSON/HTML artifacts are not first-class yet."
    )
    interpretation_next_action = (
        "Keep overview and interpretation contracts in lockstep when report sections, metrics, or layout semantics change."
        if interpretation_ready
        else "Decide whether overview v2 is the canonical interpretation surface; if not, add a dedicated schema, renderer, and CJK/path-safety tests."
    )
    extension_tracks = [
        build_extension_track(
            key="skill-interpretation-report",
            label="Skill Interpretation Report",
            status=interpretation_status,
            objective="User-facing deep interpretation report explains use cases, triggers, inputs, outputs, workflow, principles, boundaries, quality gates, examples, and next iterations.",
            current=interpretation_current,
            target="Either keep skill-overview as the canonical interpretation report with an explicit contract, or split a dedicated reports/skill-interpretation.* renderer and tests.",
            artifact_paths=interpretation_paths,
            next_action=interpretation_next_action,
            skill_dir=skill_dir,
        ),
    ]
    adaptive_foundation_paths = [
        "references/autonomous-adaptation.md",
        "references/user-memory-policy.md",
        "schemas/adaptation-proposal.schema.json",
        "scripts/summarize_user_signals.py",
        "scripts/propose_adaptation.py",
        "tests/verify_adaptation_safety.py",
    ]
    adaptive_apply_paths = [
        "scripts/apply_adaptation.py",
        "reports/adaptation_approval_ledger.json",
        "reports/adaptation_regression_report.json",
    ]
    adaptive_foundation_ready = paths_exist(skill_dir, adaptive_foundation_paths)
    adaptive_apply_ready = paths_exist(skill_dir, adaptive_apply_paths)
    adaptive_status = "covered" if adaptive_foundation_ready and adaptive_apply_ready else ("partial" if adaptive_foundation_ready else "planned")
    adaptive_current = (
        "Proposal-only adapt-scan/adapt-propose foundation exists with policy, schema, and safety tests; approval-gated patch application is not implemented yet."
        if adaptive_status == "partial"
        else (
            "Full adaptive loop includes proposal, approval, patch application, regression evidence, and rollback metadata."
            if adaptive_status == "covered"
            else "The repo has feedback, iteration, telemetry, and review artifacts, but no adapt-scan/adapt-propose/adapt-apply approval loop and no user-memory policy."
        )
    )
    adaptive_next_action = (
        "Add adapt-apply only after approval ledger, allowlisted targets, dry-run diffs, regression reports, and rollback artifacts are designed."
        if adaptive_status == "partial"
        else "Start with policy and read-only scan tests; do not read shell history or private logs unless the user provides an explicit source path."
    )
    extension_tracks.append(
        build_extension_track(
            key="adaptive-self-iteration",
            label="Adaptive Self-Iteration",
            status=adaptive_status,
            objective="Local-first preference memory, repeated-signal extraction, adaptation proposals, approval, patch application, regression evidence, and rollback.",
            current=adaptive_current,
            target="Proposal-only adaptation with explicit input source, redaction, allowlisted write targets, approval ledger, regression report, and rollback plan.",
            artifact_paths=[
                *adaptive_foundation_paths,
                *adaptive_apply_paths,
                "reports/user_patterns.json",
                "reports/adaptation_proposals.json",
                "reports/iteration-directions.md",
                "reports/adoption_drift_report.md",
            ],
            next_action=adaptive_next_action,
            skill_dir=skill_dir,
        )
    )
    extension_counts: dict[str, int] = {}
    for item in extension_tracks:
        extension_counts[item["status"]] = extension_counts.get(item["status"], 0) + 1

    items = modules + pr_items
    counts: dict[str, int] = {"pass": 0, "warn": 0, "missing": 0}
    for item in items:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    local_ready = counts.get("missing", 0) == 0 and counts.get("warn", 0) == 0
    public_ready = local_ready and summary_value(world_class_ledger, "ready_to_claim_world_class", False) is True
    decision = "world-class-ready" if public_ready else ("local-blueprint-covered-evidence-pending" if local_ready else "continue-implementation")
    summary = {
        "item_count": len(items),
        "module_count": len(modules),
        "recommended_pr_count": len(pr_items),
        "pass_count": counts.get("pass", 0),
        "warn_count": counts.get("warn", 0),
        "missing_count": counts.get("missing", 0),
        "extension_track_count": len(extension_tracks),
        "extension_partial_count": extension_counts.get("partial", 0),
        "extension_planned_count": extension_counts.get("planned", 0),
        "extension_covered_count": extension_counts.get("covered", 0),
        "adaptive_extension_ready": adaptive_status == "covered",
        "local_blueprint_ready": local_ready,
        "public_world_class_ready": public_ready,
        "world_class_evidence_pending_count": pending_world_class,
        "decision": decision,
    }
    return {
        "schema_version": "1.0",
        "ok": counts.get("missing", 0) == 0,
        "generated_at": generated_at,
        "skill_dir": rel_path(skill_dir, ROOT),
        "summary": summary,
        "status_counts": counts,
        "extension_status_counts": extension_counts,
        "modules": modules,
        "recommended_prs": pr_items,
        "reference_extension_tracks": extension_tracks,
        "next_highest_leverage": [
            "Close the four world-class evidence ledger entries with accepted human or external evidence.",
            "Keep the first-class skill interpretation report and Skill Overview v2 contract synchronized as the report model evolves.",
            "Start adaptive self-iteration as explicit-source, proposal-only, approval-gated work; do not scan private logs by default.",
            "Keep the blueprint coverage report in CI so 2.0 plan drift is visible.",
        ],
        "source_blueprint": {
            "title": "Skill Overview / Skill OS 2.0 upgrade plan",
            "core_module_count": 8,
            "recommended_pr_count": 13,
            "reference_extension_count": len(extension_tracks),
            "reference_extensions": [
                "Skill interpretation report",
                "Adaptive self-iteration with local preference memory and approval gates",
            ],
        },
        "artifacts": {
            "json": "reports/skill_os2_coverage.json",
            "markdown": "reports/skill_os2_coverage.md",
        },
    }


def render_table(items: list[dict[str, Any]]) -> list[str]:
    lines = ["| Item | Status | Current | Command | Test |", "| --- | --- | --- | --- | --- |"]
    for item in items:
        lines.append(
            "| "
            + " | ".join(
                [
                    item["label"].replace("|", "\\|"),
                    f"`{item['status']}`",
                    item["current"].replace("|", "\\|"),
                    f"`{item['command']}`",
                    f"`{item['test']}`",
                ]
            )
            + " |"
        )
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Skill OS 2.0 Blueprint Coverage",
        "",
        f"Generated at: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- decision: `{summary['decision']}`",
        f"- local blueprint ready: `{str(summary['local_blueprint_ready']).lower()}`",
        f"- public world-class ready: `{str(summary['public_world_class_ready']).lower()}`",
        f"- pass: `{summary['pass_count']}` / `{summary['item_count']}`",
        f"- missing: `{summary['missing_count']}`",
        f"- warn: `{summary['warn_count']}`",
        f"- reference extensions: `{summary['extension_track_count']}`",
        f"- extension covered: `{summary['extension_covered_count']}`",
        f"- extension partial: `{summary['extension_partial_count']}`",
        f"- extension planned: `{summary['extension_planned_count']}`",
        f"- adaptive extension ready: `{str(summary['adaptive_extension_ready']).lower()}`",
        f"- world-class evidence pending: `{summary['world_class_evidence_pending_count']}`",
        "",
        "This report maps the Skill OS 2.0 upgrade blueprint to concrete local artifacts, commands, and tests. It does not count pending human review, provider runs, metadata fallbacks, or planned work as public world-class evidence.",
        "",
        "## Core Modules",
        "",
        *render_table(report["modules"]),
        "",
        "## Recommended PR Coverage",
        "",
        *render_table(report["recommended_prs"]),
        "",
        "## Reference Extension Tracks",
        "",
        "| Track | Status | Current | Target | Next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["reference_extension_tracks"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    item["label"].replace("|", "\\|"),
                    f"`{item['status']}`",
                    item["current"].replace("|", "\\|"),
                    item["target"].replace("|", "\\|"),
                    item["next_action"].replace("|", "\\|"),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "These extension tracks come from the user-supplied 2.0 reference plan. They are tracked separately from the formal Skill OS blueprint so the report can distinguish landed local architecture from planned explainer/adaptor evolution.",
            "",
        "## Next Highest-Leverage Moves",
        "",
        ]
    )
    lines.extend(f"- {item}" for item in report["next_highest_leverage"])
    lines.extend(["", "## Evidence Detail", ""])
    for item in report["modules"] + report["recommended_prs"] + report["reference_extension_tracks"]:
        existing = [entry["path"] for entry in item["evidence"] if entry["exists"]]
        missing = [entry["path"] for entry in item["evidence"] if not entry["exists"]]
        lines.append(f"### {item['label']}")
        lines.append("")
        lines.append(f"- objective: {item['objective']}")
        lines.append(f"- status: `{item['status']}`")
        lines.append(f"- existing evidence: {', '.join(f'`{path}`' for path in existing) if existing else '`none`'}")
        if missing:
            lines.append(f"- missing evidence: {', '.join(f'`{path}`' for path in missing)}")
        lines.append(f"- next action: {item['next_action']}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Skill OS 2.0 blueprint coverage evidence.")
    parser.add_argument("skill_dir", nargs="?", default=".")
    parser.add_argument("--output-json", default="reports/skill_os2_coverage.json")
    parser.add_argument("--output-md", default="reports/skill_os2_coverage.md")
    parser.add_argument("--generated-at", default=date.today().isoformat())
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    report = build_coverage(skill_dir, args.generated_at)
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
